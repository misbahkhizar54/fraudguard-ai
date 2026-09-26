# FraudGuard AI

## AI-Powered Fraud Detection & Investigation Assistant

FraudGuard AI is a human-in-the-loop fraud detection web application developed as part of the AI Engineering Batch 06 Capstone Project.

The system combines machine learning, explainable AI, and Generative AI to help fraud analysts evaluate potentially fraudulent e-commerce transactions.

### Core Workflow

Transaction Input → XGBoost Fraud Detection → Risk Score → SHAP Explanation → AI Investigation Support → Human Analyst Decision

The application allows analysts to:

- Analyze prepared demo transactions.
- Upload a model-ready transaction CSV.
- Generate fraud-risk probabilities using XGBoost.
- Classify transactions into Low, Medium, or High Risk.
- View SHAP-based explanations of model influence.
- Generate AI investigation summaries using a local Qwen model.
- Ask contextual follow-up questions about the current transaction.
- Record human analyst decisions as Clear, Verify, or Escalate.
- Review investigation history and dashboard statistics.

> FraudGuard AI is a decision-support prototype. A high fraud-risk score does not prove that a transaction is fraudulent. Final case decisions remain with the human analyst.

## Dataset

FraudGuard AI uses the **IEEE-CIS Fraud Detection** dataset from the Kaggle IEEE-CIS Fraud Detection competition.

### Dataset Files Used

- `train_transaction.csv`
- `train_identity.csv`

The two datasets are joined using `TransactionID`.

### Dataset Summary

- Labelled transactions: 590,540
- Original transaction features: 394 columns
- Fraudulent transactions: 20,663 (3.50%)
- Legitimate transactions: 569,877 (96.50%)
- Identity records: 144,233
- Transactions with identity information: approximately 24.42%
- Target variable: `isFraud`

The dataset is highly imbalanced, so model evaluation focuses on precision, recall, F1-score, PR-AUC, ROC-AUC, and confusion matrices rather than accuracy alone.

### Dataset Source and License

Dataset source: **Kaggle - IEEE-CIS Fraud Detection Competition**

The dataset is provided under the competition's rules and terms of use. The raw IEEE-CIS dataset is **not included in this repository**. Users should obtain the dataset directly from Kaggle and comply with the applicable competition rules.

Place the downloaded files inside:

`data/train_transaction.csv`

`data/train_identity.csv`

## Project Structure

```text
FraudGuard AI/
│
├── app/
│   ├── app.py
│   ├── model_service.py
│   ├── database.py
│   ├── genai_service.py
│   │
│   ├── static/
│   │   └── css/
│   │       └── style.css
│   │
│   └── templates/
│       ├── base.html
│       ├── dashboard.html
│       ├── analyze.html
│       ├── cases.html
│       └── assistant.html
│
├── data/
│   ├── train_transaction.csv
│   ├── train_identity.csv
│   └── fraudguard.db
│
├── models/
│   ├── fraudguard_xgboost_pipeline.joblib
│   └── fraudguard_model_config.json
│
├── notebooks/
│   └── 01_eda.ipynb
│
├── outputs/
│   ├── demo_transactions.csv
│   └── test_transaction_111.csv
│
├── test_genai.py
└── README.md
```

## Machine Learning Model

FraudGuard AI treats fraud detection as an imbalanced binary classification problem.

Two main machine-learning approaches were evaluated:

1. **Logistic Regression** — baseline model
2. **XGBoost** — final tree-based model

A chronological **70/15/15 train-validation-test split** was used:

- Training: 413,378 transactions
- Validation: 88,581 transactions
- Test: 88,581 transactions

This prevents future transactions from being used to train a model that is evaluated on earlier transactions.

### Logistic Regression Baseline

The Logistic Regression baseline achieved:

| Metric    | Validation Result |
| --------- | ----------------: |
| ROC-AUC   |            0.8394 |
| PR-AUC    |            0.3709 |
| Precision |            0.4781 |
| Recall    |            0.3304 |
| F1-score  |            0.3907 |

### Final XGBoost Model

After comparing multiple XGBoost configurations, **XGBoost Model 2A** was selected as the final model.

The fraud-alert threshold was selected using the validation set and then locked before final test evaluation.

**Final threshold: 0.7271 (72.71%)**

### Validation Performance

| Metric    | Result |
| --------- | -----: |
| ROC-AUC   | 0.9155 |
| PR-AUC    | 0.5433 |
| Precision | 0.5883 |
| Recall    | 0.4579 |
| F1-score  | 0.5150 |

### Untouched Test Performance

| Metric    | Result |
| --------- | -----: |
| Accuracy  | 0.9655 |
| ROC-AUC   | 0.8993 |
| PR-AUC    | 0.5028 |
| Precision | 0.5056 |
| Recall    | 0.4535 |
| F1-score  | 0.4781 |

### Test Confusion Matrix

|                   | Predicted Legitimate | Predicted Fraud Alert |
| ----------------- | -------------------: | --------------------: |
| Actual Legitimate |               84,131 |                 1,367 |
| Actual Fraud      |                1,685 |                 1,398 |

Because only approximately 3.5% of the transactions are fraudulent, **accuracy is not treated as the primary performance measure**. PR-AUC, precision, recall, F1-score, ROC-AUC, and the confusion matrix provide a more informative assessment of fraud-detection performance.

## Risk Levels

FraudGuard AI uses the following application-level risk bands:

- **High Risk:** probability >= 72.71%
- **Medium Risk:** probability >= 30% and < 72.71%
- **Low Risk:** probability < 30%

The **72.71% threshold** is the model's selected fraud-alert threshold. The **30% Medium Risk boundary** is an application-level review band used to surface uncertain transactions for human review; it is not a separately trained model threshold.

## Explainable AI with SHAP

FraudGuard AI uses **SHAP (SHapley Additive exPlanations)** to explain individual XGBoost predictions.

For each analyzed transaction, the application displays:

- Features that increase the model score.
- Features that reduce the model score.
- The SHAP value associated with each displayed feature.

Positive SHAP values indicate features pushing the model score upward, while negative SHAP values indicate features pushing the model score downward.

Because many IEEE-CIS variables are anonymized, FraudGuard AI does not invent real-world meanings for features such as `V258`, `C1`, or `C13`. SHAP values are presented as model influence rather than proof that a feature caused fraud.

## Generative AI Integration

FraudGuard AI integrates **Qwen3 1.7B** locally through **Ollama**.

Generative AI is connected directly to the machine-learning output rather than being used as a standalone generic chatbot.

The GenAI component can receive:

- Fraud probability
- Fraud-alert threshold
- Risk level
- Model decision
- SHAP-based increasing factors
- SHAP-based reducing factors

### AI Investigation Summary

After a transaction has been analyzed, the analyst can generate an AI investigation summary based on the actual XGBoost prediction and SHAP explanation.

AI generation is performed on demand so that normal transaction prediction does not have to wait for local LLM inference.

### Contextual AI Assistant

The AI Assistant receives the latest analyzed transaction as context. This allows the analyst to ask follow-up questions about the result currently being reviewed.

For example:

**Analyst:**

> Why is this transaction high risk?

For a test transaction with a **99.44% fraud-risk probability**, the assistant correctly identified that the score exceeded the **72.71% fraud-alert threshold** and referred to the actual model features influencing that prediction.

### GenAI Safety and Grounding

The Qwen prompt instructs the assistant to:

- Use the actual model result provided by FraudGuard AI.
- Avoid inventing transaction facts or evidence.
- Avoid inventing meanings for anonymized IEEE-CIS features.
- Treat SHAP as model influence rather than real-world causation.
- Avoid claiming that the model proves or confirms fraud.
- Leave the final Clear, Verify, or Escalate decision to the human analyst.

This creates a **human-in-the-loop** workflow in which machine learning and Generative AI support investigation without replacing the analyst's final judgment.

## Installation and Setup

### Requirements

- Python 3.13
- Conda
- Ollama
- Git
- A local copy of the IEEE-CIS Fraud Detection dataset

The project was developed and tested using Python 3.13.11.

### 1. Clone the Repository

```bash
git clone <YOUR-GITHUB-REPOSITORY-URL>
cd "FraudGuard AI"
```

Replace `<YOUR-GITHUB-REPOSITORY-URL>` with the actual repository URL after the project is uploaded to GitHub.

### 2. Create the Conda Environment

```bash
conda create -n fraudguard python=3.13
conda activate fraudguard
```

### 3. Install Python Dependencies

Install the required libraries:

```bash
pip install pandas numpy scikit-learn xgboost shap flask requests joblib
```

### 4. Download the Dataset

Download the IEEE-CIS Fraud Detection dataset from the Kaggle competition page.

Place the required files in:

```text
data/train_transaction.csv
data/train_identity.csv
```

The raw dataset is not distributed with this repository.

### 5. Install Ollama

Install Ollama and make sure the Ollama service is running.

Pull the local Qwen model:

```bash
ollama pull qwen3:1.7b
```

Start Ollama if it is not already running:

```bash
ollama serve
```

FraudGuard AI expects the Ollama API at:

```text
http://127.0.0.1:11434
```

### 6. Run FraudGuard AI

From the project root directory, activate the environment:

```bash
conda activate fraudguard
```

Start the Flask application:

```bash
python app/app.py
```

Open the local address displayed by Flask in your web browser.

## Using the Application

1. Open **Analyze Transaction**.
2. Select a prepared demo transaction or upload one model-ready transaction CSV.
3. Run the XGBoost analysis.
4. Review the fraud probability, risk level, threshold, and SHAP explanation.
5. Optionally generate an AI investigation summary.
6. Use **AI Assistant** to ask follow-up questions about the latest analyzed transaction.
7. Record the analyst decision as **Clear**, **Verify**, or **Escalate**.
8. Review saved investigations from the **Cases** page.
9. Use the **Dashboard** to view model information and investigation statistics.

### CSV Upload Note

The current prototype expects a **model-ready CSV containing exactly one transaction row and the features required by the saved preprocessing/model pipeline**.

The upload feature is intended to demonstrate transaction ingestion in the capstone prototype. It is not a production-ready parser for arbitrary banking or payment-provider transaction formats.

## Technology Stack

### Machine Learning and Data

- Python
- pandas
- NumPy
- scikit-learn
- XGBoost
- SHAP
- joblib

### Generative AI

- Ollama
- Qwen3 1.7B
- Local LLM inference

### Web Application

- Flask
- HTML
- CSS
- JavaScript
- Chart.js

### Data Storage

- SQLite

### Development Tools

- Visual Studio Code
- Jupyter Notebook
- Conda
- Git
- GitHub

## Limitations

FraudGuard AI is an educational capstone prototype and has several limitations:

- The model was trained and evaluated on the IEEE-CIS dataset and has not been validated on live financial institution data.
- The dataset contains many anonymized features, limiting their real-world interpretation.
- Fraud is highly imbalanced, and the final model does not detect every fraudulent transaction.
- The Medium Risk boundary is an application-level review rule rather than a separately optimized classification threshold.
- CSV uploads must already contain the model-ready feature schema expected by the saved pipeline.
- Local Qwen inference can be slower on CPU-only systems.
- AI-generated explanations are investigation support and may require analyst verification.
- The application does not connect to a live payment processor or banking system.
- Analyst case history is stored locally using SQLite.
- The system is a decision-support prototype and should not be used as an autonomous fraud decision system.

## Future Improvements

Possible future improvements include:

- Build a production-style preprocessing layer for raw transaction inputs.
- Support batch transaction uploads.
- Add stronger data validation and schema checking.
- Evaluate additional imbalance-handling and threshold-selection strategies.
- Improve probability calibration and model monitoring.
- Add temporal drift monitoring and scheduled model retraining.
- Add authentication and role-based access for analysts.
- Use a production database instead of local SQLite.
- Add secure integration with transaction and case-management systems.
- Improve the contextual AI assistant with controlled case-history retrieval.
- Add automated testing for model, API, database, and GenAI components.
- Deploy the application using a production-ready web server and infrastructure.

## Human-in-the-Loop Design

FraudGuard AI does not automatically determine whether a customer committed fraud.

The system provides:

**Transaction → ML Risk Assessment → SHAP Explanation → GenAI Investigation Support → Human Analyst Decision**

The human analyst remains responsible for the final case disposition.

## Project Status

**Capstone Project 1 — Completed Prototype**

Core functionality includes:

- XGBoost fraud detection
- Chronological model evaluation
- Optimized fraud-alert threshold
- SHAP explainability
- CSV transaction upload
- Local Qwen GenAI integration
- AI investigation summaries
- Context-aware AI Assistant
- Human analyst case decisions
- SQLite case history
- Investigation dashboard
