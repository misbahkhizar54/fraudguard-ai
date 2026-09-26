import requests


OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "qwen3:1.7b"


def format_factors(factors):
    if not factors:
        return "None provided"

    formatted = []

    for factor in factors:
        feature = factor.get("feature", "Unknown")
        value = factor.get("value", "N/A")
        shap_value = factor.get("shap_value", "N/A")

        formatted.append(
            f"- {feature} = {value} (SHAP influence: {shap_value})"
        )

    return "\n".join(formatted)


def generate_investigation_summary(prediction_result):
    probability = prediction_result["fraud_percentage"]
    threshold = prediction_result["threshold_percentage"]
    risk_level = prediction_result["risk_level"]
    model_decision = prediction_result["decision"]

    increasing_factors = format_factors(
        prediction_result["risk_increasing_factors"]
    )

    reducing_factors = format_factors(
        prediction_result["risk_reducing_factors"]
    )

    prompt = f"""
You are FraudGuard AI, an assistant supporting a human fraud analyst.

Write a concise professional investigation summary based ONLY on the
machine-learning evidence below.

MODEL RESULT
Fraud probability: {probability:.2f}%
Fraud alert threshold: {threshold:.2f}%
Risk level: {risk_level}
Model decision: {model_decision}

FACTORS INCREASING THE MODEL SCORE
{increasing_factors}

FACTORS REDUCING THE MODEL SCORE
{reducing_factors}

STRICT RULES:
1. State whether the fraud probability is above or below the threshold.
2. Do not say that fraud is confirmed.
3. Do not invent meanings for anonymous IEEE-CIS features.
4. Do not claim that a SHAP factor proves fraudulent behaviour.
5. Treat SHAP values only as model influence.
6. Do not invent transaction facts that are not provided.
7. State that the final disposition belongs to the human analyst.
8. Use one short paragraph.
9. Maximum 120 words.
10. Do not include headings, bullet points, recommendations, marketing text,
    greetings, or information outside the supplied evidence.

Return only the investigation summary.
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2
                }
            },
            timeout=120
        )

        response.raise_for_status()

        data = response.json()
        summary = data.get("response", "").strip()

        return {
            "success": True,
            "summary": summary
        }

    except requests.RequestException as error:
        return {
            "success": False,
            "summary": (
                "AI investigation summary is temporarily unavailable."
            ),
            "error": str(error)
        }

def ask_fraud_assistant(
    question,
    prediction_result=None
):

    if prediction_result:

        probability = prediction_result.get(
            "fraud_percentage"
        )

        threshold = prediction_result.get(
            "threshold_percentage"
        )

        risk_level = prediction_result.get(
            "risk_level"
        )

        model_decision = prediction_result.get(
            "decision"
        )

        increasing_factors = format_factors(
            prediction_result.get(
                "risk_increasing_factors",
                []
            )
        )

        reducing_factors = format_factors(
            prediction_result.get(
                "risk_reducing_factors",
                []
            )
        )

        transaction_context = f"""
CURRENT TRANSACTION RESULT:
Fraud probability: {probability}%
Fraud alert threshold: {threshold}%
Risk level: {risk_level}
Model decision: {model_decision}

Factors increasing the model score:
{increasing_factors}

Factors reducing the model score:
{reducing_factors}
"""

    else:

        transaction_context = """
CURRENT TRANSACTION RESULT:
No transaction has been analyzed in the current session.
"""

    system_context = """
You are FraudGuard AI, an AI assistant supporting human fraud analysts.

PROJECT FACTS:
- FraudGuard uses an XGBoost fraud-detection model.
- The official fraud-alert threshold is 72.71%.
- High Risk: fraud probability >= 72.71%.
- Medium Risk: fraud probability >= 30% and < 72.71%.
- Low Risk: fraud probability < 30%.
- SHAP is used to explain model influence.
- Positive SHAP values increase the model score.
- Negative SHAP values reduce the model score.
- The final case decision belongs to the human analyst.

STRICT RULES:
1. Answer only the question that was asked.
2. Keep the answer concise, normally 2 to 5 sentences.
3. Never say that the model proves or confirms fraud.
4. Use terms such as "fraud risk", "fraud alert",
   "model score", or "potential fraud".
5. Never invent transaction facts or evidence.
6. Never invent meanings for anonymized IEEE-CIS features.
7. Do not give hypothetical feature examples unless the
   question explicitly asks for examples.
8. If discussing SHAP, describe it only as influence on
   the model score.
9. Do not make the final Clear, Verify, or Escalate
   decision for the analyst.
10. Do not use Markdown.
11. Do not use headings, bullet points, asterisks,
    HTML tags, or special formatting.
12. Return plain text only.
13. If the analyst asks about one concept, answer only that concept.
14. Do not introduce SHAP, other model features, or investigation topics
unless they are directly relevant to the question.
15. When explaining SHAP, say that positive SHAP values increase
    the model score and negative SHAP values reduce the model score.
    Do not describe SHAP values as changing the real-world likelihood
    of fraud.

16. Do not mention SHAP unless the analyst specifically asks about
    SHAP, feature influence, or model explanation.
17. Never describe the fraud probability as the real-world likelihood
    that fraud occurred. Describe it as the model-estimated fraud risk
    or model fraud-risk score.
18. Only discuss SHAP values or feature contributions when the analyst
    specifically asks why the model produced the result, which features
    influenced it, or asks about SHAP/explainability.
"""

    prompt = f"""
   
{system_context}

{transaction_context}

ANALYST QUESTION:
{question}

Provide a direct plain-text answer:
"""
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1
                }
            },
            timeout=120
        )
        response.raise_for_status()

        data = response.json()

        answer = data.get("response", "").strip()

        answer = " ".join(
            answer.split()
        )

        return {
            "success": True,
            "answer": answer
        }
    except requests.RequestException as error:
        return {
            "success": False,
            "answer": (
                "FraudGuard AI is temporarily unavailable."
            ),
            "error": str(error)
        }