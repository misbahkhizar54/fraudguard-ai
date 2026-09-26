# FraudGuard Flask application

from flask import (
    Flask,
    render_template,
    request,
    session,
    redirect,
    url_for
)

from model_service import (
    model_config,
    fraud_threshold,
    predict_transaction,
    get_expected_features
)
from genai_service import (
    generate_investigation_summary,
    ask_fraud_assistant
)
import pandas as pd
from pathlib import Path
from database import (
    save_case,
    get_all_cases,
    create_chat_session,
    save_chat_message,
    get_chat_sessions,
    get_chat_messages
)


app = Flask(__name__)
app.secret_key = "fraudguard-local-development-key"


@app.route("/")
def home():

    case_records = get_all_cases()

    case_summary = {
        "total": len(case_records),
        "high": 0,
        "medium": 0,
        "low": 0,
        "cleared": 0,
        "verification": 0,
        "escalated": 0
    }

    for case in case_records:

        risk_level = case["risk_level"]
        case_status = case["case_status"]

        if risk_level == "High":
            case_summary["high"] += 1

        elif risk_level == "Medium":
            case_summary["medium"] += 1

        elif risk_level == "Low":
            case_summary["low"] += 1

        if case_status == "Cleared":
            case_summary["cleared"] += 1

        elif case_status == "Verification Required":
            case_summary["verification"] += 1

        elif case_status == "Escalated":
            case_summary["escalated"] += 1

    test_metrics = model_config["test"]

    return render_template(
        "dashboard.html",
        model_name=model_config["model_name"],
        threshold=round(fraud_threshold * 100, 2),
        pr_auc=round(test_metrics["pr_auc"], 4),
        recall=round(test_metrics["recall"] * 100, 2),
        precision=round(test_metrics["precision"] * 100, 2),
        case_summary=case_summary
    )



# Analyze transaction page

@app.route(
    "/analyze",
    methods=["GET", "POST"]
)
def analyze():

    result = None
    selected_risk = "high"
    transaction_preview = None
    actual_label = None
    ai_summary = None
    upload_error = None
    input_source = "demo"

    base_dir = (
        Path(__file__)
        .resolve()
        .parent
        .parent
    )

    demo_path = (
        base_dir
        / "outputs"
        / "demo_transactions.csv"
    )

    demo_df = pd.read_csv(
        demo_path
    )

    if request.method == "POST":

        uploaded_file = request.files.get(
            "transaction_file"
        )

        if (
            uploaded_file
            and uploaded_file.filename
        ):
            input_source = "upload"

        selected_risk = request.form.get(
            "risk_example",
            "high"
        )

        analyst_decision = request.form.get(
            "analyst_decision"
        )
        generate_ai = request.form.get(
            "generate_ai"
        )

        if input_source == "upload":

            if not uploaded_file.filename.lower().endswith(".csv"):
                upload_error = (
                    "Please upload a CSV file."
                )

            else:
                try:
                    uploaded_df = pd.read_csv(
                        uploaded_file
                    )

                    if len(uploaded_df) != 1:
                        upload_error = (
                            "The CSV must contain exactly "
                            "one transaction row."
                        )

                    else:
                        expected_features = (
                            get_expected_features()
                        )

                        missing_features = [
                            feature
                            for feature in expected_features
                            if feature not in uploaded_df.columns
                        ]

                        if missing_features:
                            upload_error = (
                                f"The uploaded CSV is missing "
                                f"{len(missing_features)} required "
                                f"model features."
                            )

                        else:
                            transaction_data = (
                                uploaded_df.iloc[0]
                                .to_dict()
                            )

                            result = predict_transaction(
                                transaction_data
                            )
                            session["current_prediction"] = result

                            actual_label = None

                            transaction_preview = {
                                "position": "Uploaded",
                                "amount": round(
                                    float(
                                        uploaded_df.iloc[0][
                                            "TransactionAmt"
                                        ]
                                    ),
                                    3
                                ),
                                "product": uploaded_df.iloc[0][
                                    "ProductCD"
                                ],
                                "network": uploaded_df.iloc[0][
                                    "card4"
                                ],
                                "card_type": uploaded_df.iloc[0][
                                    "card6"
                                ]
                            }

                except Exception:
                    upload_error = (
                        "The CSV could not be read. "
                        "Please check the file format."
                    )

        else:

            selected_row = demo_df[
                demo_df["DemoRiskLevel"]
                == selected_risk
            ].iloc[0]

            transaction_data = (
                selected_row.to_dict()
            )

            result = predict_transaction(
                transaction_data
            )
            session["current_prediction"] = result

            actual_label = int(
                selected_row["ActualLabel"]
            )

            transaction_preview = {
                "position": int(
                    selected_row["DemoPosition"]
                ),
                "amount": round(
                    float(
                        selected_row["TransactionAmt"]
                    ),
                    3
                ),
                "product": selected_row["ProductCD"],
                "network": selected_row["card4"],
                "card_type": selected_row["card6"]
            }

        if generate_ai and result is not None:

            ai_result = generate_investigation_summary(
                result
            )

            if ai_result["success"]:
                ai_summary = ai_result["summary"]
            else:
                ai_summary = (
                    "AI investigation summary is "
                    "temporarily unavailable."
                )

        if analyst_decision and result is not None:

            status_map = {
                "Clear": "Cleared",
                "Verify": "Verification Required",
                "Escalate": "Escalated"
            }

            case_status = status_map[
                analyst_decision
            ]

            save_case(
                demo_position=transaction_preview["position"],
                transaction_amount=transaction_preview["amount"],
                product_code=transaction_preview["product"],
                card_network=transaction_preview["network"],
                card_type=transaction_preview["card_type"],
                fraud_probability=result["fraud_probability"],
                risk_level=result["risk_level"],
                model_decision=result["decision"],
                analyst_decision=analyst_decision,
                case_status=case_status
            )

    return render_template(
        "analyze.html",
        result=result,
        selected_risk=selected_risk,
        transaction_preview=transaction_preview,
        actual_label=actual_label,
        ai_summary=ai_summary,
        upload_error=upload_error,
        input_source=input_source
    )

@app.route("/cases")
def cases():

    case_records = get_all_cases()

    total_cases = len(case_records)

    escalated_cases = sum(
        1
        for case in case_records
        if case["case_status"] == "Escalated"
    )

    verification_cases = sum(
        1
        for case in case_records
        if case["case_status"] == "Verification Required"
    )

    cleared_cases = sum(
        1
        for case in case_records
        if case["case_status"] == "Cleared"
    )

    return render_template(
        "cases.html",
        cases=case_records,
        total_cases=total_cases,
        escalated_cases=escalated_cases,
        verification_cases=verification_cases,
        cleared_cases=cleared_cases
    )


@app.route(
    "/assistant",
    methods=["GET", "POST"]
)
def ai_assistant():

    current_prediction = session.get(
        "current_prediction"
    )

    chat_session_id = session.get(
        "chat_session_id"
    )

    # Create a new chat session when needed
    if chat_session_id is None:

        transaction_id = None
        risk_level = None
        fraud_score = None

        if current_prediction:

            transaction_id = current_prediction.get(
                "demo_position"
            )

            risk_level = current_prediction.get(
                "risk_level"
            )

            fraud_score = current_prediction.get(
                "fraud_percentage"
            )

        chat_session_id = create_chat_session(
            transaction_id=transaction_id,
            risk_level=risk_level,
            fraud_score=fraud_score
        )

        session["chat_session_id"] = (
            chat_session_id
        )

    if request.method == "POST":

        question = request.form.get(
            "question",
            ""
        ).strip()

        if question:

            save_chat_message(
                chat_session_id,
                "user",
                question
            )

            ai_result = ask_fraud_assistant(
                question,
                current_prediction
            )

            answer = ai_result["answer"]

            save_chat_message(
                chat_session_id,
                "assistant",
                answer
            )

    history = get_chat_messages(
        chat_session_id
    )

    return render_template(
        "assistant.html",
        history=history
    )


@app.route("/assistant/new")
def new_chat():

    session.pop(
        "chat_session_id",
        None
    )

    return redirect(
        url_for("ai_assistant")
    )


@app.route("/assistant/history")
def chat_history():

    chats = get_chat_sessions()

    return render_template(
        "chat_history.html",
        chats=chats
    )


@app.route("/assistant/chat/<int:chat_id>")
def open_chat(chat_id):

    messages = get_chat_messages(
        chat_id
    )

    if not messages:
        return redirect(
            url_for("chat_history")
        )

    session["chat_session_id"] = chat_id

    return redirect(
        url_for("ai_assistant")
    )


if __name__ == "__main__":
    app.run(
        debug=True
    )