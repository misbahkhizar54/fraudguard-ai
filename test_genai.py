
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent



from app.model_service import predict_transaction
from app.genai_service import generate_investigation_summary


demo_path = PROJECT_ROOT / "outputs" / "demo_transactions.csv"

demo_df = pd.read_csv(demo_path)

high_risk_row = demo_df[
    demo_df["DemoRiskLevel"].str.lower() == "high"
].iloc[0]

transaction_data = high_risk_row.to_dict()

prediction = predict_transaction(
    transaction_data,
    top_n=5
)

print("\nML RESULT")
print("Probability:", prediction["fraud_percentage"])
print("Threshold:", prediction["threshold_percentage"])
print("Risk level:", prediction["risk_level"])
print("Decision:", prediction["decision"])

print("\nGenerating AI investigation summary...")

ai_result = generate_investigation_summary(prediction)

print("\nAI RESULT")
print("Success:", ai_result["success"])
print("\nSummary:")
print(ai_result["summary"])