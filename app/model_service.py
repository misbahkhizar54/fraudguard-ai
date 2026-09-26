# FraudGuard model service
# Load the trained XGBoost pipeline and model configuration

from pathlib import Path
import json
import joblib
import pandas as pd
import shap


BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "models"

MODEL_PATH = MODEL_DIR / "fraudguard_xgboost_pipeline.joblib"
CONFIG_PATH = MODEL_DIR / "fraudguard_model_config.json"


def load_fraudguard_model():
    model = joblib.load(MODEL_PATH)

    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        config = json.load(file)

    threshold = float(config["threshold"])

    return model, config, threshold


model, model_config, fraud_threshold = load_fraudguard_model()

# Prepare SHAP explainer

preprocessor = model.named_steps["preprocessor"]
classifier = model.named_steps["classifier"]

shap_feature_names = (
    preprocessor.get_feature_names_out()
)

shap_explainer = shap.TreeExplainer(
    classifier
)


# Get the exact input features expected by the trained pipeline


def get_expected_features():
    return list(
        preprocessor.feature_names_in_
    )

# Predict fraud risk and explain one transaction

def predict_transaction(transaction_data, top_n=5):

    expected_features = list(
        preprocessor.feature_names_in_
    )

    transaction_df = pd.DataFrame(
        [transaction_data]
    )

    transaction_df = transaction_df.reindex(
        columns=expected_features
    )

    fraud_probability = float(
        model.predict_proba(transaction_df)[0, 1]
    )

    if fraud_probability >= fraud_threshold:
        risk_level = "High"
        decision = "Fraud Alert"

    elif fraud_probability >= 0.30:
        risk_level = "Medium"
        decision = "Review Recommended"

    else:
        risk_level = "Low"
        decision = "Low Risk"

    transformed_row = preprocessor.transform(
        transaction_df
    )

    shap_result = shap_explainer(
        transformed_row
    )

    contributions = pd.DataFrame({
        "feature": shap_feature_names,
        "value": shap_result.data[0],
        "shap_value": shap_result.values[0]
    })

    contributions["feature"] = (
        contributions["feature"]
        .str.replace(
            "numeric__",
            "",
            regex=False
        )
        .str.replace(
            "categorical__",
            "",
            regex=False
        )
    )

    increasing = (
        contributions[
            contributions["shap_value"] > 0
        ]
        .sort_values(
            "shap_value",
            ascending=False
        )
        .head(top_n)
        .reset_index(drop=True)
    )

    reducing = (
        contributions[
            contributions["shap_value"] < 0
        ]
        .sort_values(
            "shap_value",
            ascending=True
        )
        .head(top_n)
        .reset_index(drop=True)
    )

    return {
        "fraud_probability": fraud_probability,
        "fraud_percentage": round(
            fraud_probability * 100,
            2
        ),
        "threshold": fraud_threshold,
        "threshold_percentage": round(
            fraud_threshold * 100,
            2
        ),
        "risk_level": risk_level,
        "decision": decision,
        "risk_increasing_factors": (
            increasing.to_dict(
                orient="records"
            )
        ),
        "risk_reducing_factors": (
            reducing.to_dict(
                orient="records"
            )
        )
    }



# Test FraudGuard prediction using a real processed transaction

if __name__ == "__main__":
    import pandas as pd

    print("FraudGuard model loaded successfully.")
    print("Model:", model_config["model_name"])
    print(f"Fraud threshold: {fraud_threshold:.4f}")

    test_path = (
        BASE_DIR
        / "outputs"
        / "test_transaction_111.csv"
    )

    test_df = pd.read_csv(test_path)

    print("\nTest transaction loaded.")
    print("Shape:", test_df.shape)

    transaction_data = (
        test_df.iloc[0].to_dict()
    )

    result = predict_transaction(
        transaction_data
    )

    print("\nPrediction Result")

    print(
        "Fraud probability:",
        f'{result["fraud_probability"]:.2%}'
    )

    print(
        "Threshold:",
        f'{result["threshold"]:.2%}'
    )
    print(
        "Risk level:",
        result["risk_level"]
    )

    print(
        "Decision:",
        result["decision"]
    )

    print(
        "Fraud percentage:",
        result["fraud_percentage"]
    )

    print(
        "Threshold percentage:",
        result["threshold_percentage"]
    )

    print("\nTop factors increasing risk:")

    for factor in result["risk_increasing_factors"]:
        print(
            factor["feature"],
            "| value:",
            factor["value"],
            "| SHAP:",
            round(
                factor["shap_value"],
                4
            )
        )

    print("\nTop factors reducing risk:")

    for factor in result["risk_reducing_factors"]:
        print(
            factor["feature"],
            "| value:",
            factor["value"],
            "| SHAP:",
            round(
                factor["shap_value"],
                4
            )
        )