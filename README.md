# Cost-Sensitive Fraud Detection with Operator Feedback Loop

A machine learning project for credit card fraud detection using cost-sensitive evaluation and an operator feedback loop.

## Run the Application Locally

The repository root is the folder containing `backend`, `frontend`, `ml`,
`requirements.txt`, and `docker-compose.yml`. Run the backend and frontend in
separate PowerShell terminals. You need Python 3.12, Node.js (current LTS),
npm, and access to a PostgreSQL database.

### 1. Install Python dependencies and configure the backend

From the repository root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r backend\requirements.txt
Copy-Item .env.example .env
```

Edit the root `.env` and set at least:

* `DATABASE_URL` to a PostgreSQL database the account can access.
* `JWT_SECRET_KEY` to a private random value; do not commit `.env`.

For automatic review emails, also configure `SMTP_HOST`, `SMTP_PORT`,
`SMTP_USERNAME`, `SMTP_PASSWORD`, and `SMTP_FROM_EMAIL`. With Gmail, use an
App Password and the Gmail SMTP settings described below. Email is sent to
the signed-in user's account email when an assessment is MEDIUM or HIGH.

Apply database migrations from the repository root:

```powershell
.\.venv\Scripts\alembic.exe upgrade head
```

### 2. Start the backend

In the first PowerShell terminal, from the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8001
```

The API is at `http://127.0.0.1:8001`; interactive API documentation is at
`http://127.0.0.1:8001/docs`. Keep this terminal open while using the app.

### 3. Install and start the frontend

In a second PowerShell terminal, from the repository root:

```powershell
Copy-Item frontend\.env.example frontend\.env.local
Set-Location frontend
npm install
npm run dev
```

Open the local URL printed by Vite, normally `http://localhost:5173`. The
frontend example configuration connects to the local backend at
`http://127.0.0.1:8001`. Register an account in the app or sign in with an
existing account.

If you are already in the outer download folder, first `cd` into the inner
project folder that contains `backend` and `frontend`. Run commands from that
repository root unless the step explicitly says to enter `frontend`.



### Main Model

* Model: XGBoost
* Model version: `xgb-cost-v1`
* Dataset: ULB Credit Card Fraud Detection
* Target column: `Class`
* Input features: `Time`, `V1` to `V28`, and `Amount`

The prediction page's ordinary transaction form collects amount and a
human-readable timestamp, but does not submit them as a model prediction:
the trained model requires the original PCA-derived `V1`–`V28` features and
`Time` in elapsed seconds. The current project has no supported transformation
from those ordinary fields to the required model inputs. Internal/testing
scoring remains available through the authenticated `/transactions/predict`
API for actual model-compatible feature values; do not guess PCA values or
substitute zeros. Supporting genuine simple-input ML scoring requires a
verified feature-generation pipeline or retraining and validating a model on
ordinary transaction fields.

The user-facing **Transaction Risk Assessment** uses fixed provisional amount
bands, not the XGBoost model or a calibrated fraud probability. Amounts up to
and including 2,000 are LOW; amounts above 2,000 and below 99,999 are MEDIUM;
amounts of 99,999 and above are HIGH. These same numeric cutoffs apply to every
selected currency, without currency conversion. MEDIUM and HIGH assessments
require an agree/disagree human decision and send an email to the signed-in
account when SMTP is configured. Only HIGH assessments appear in saved risk
alerts. Merchant, transaction type, channel, location, and history do not
change this amount-only risk band. These are requested review-routing
thresholds, not validated fraud-detection thresholds; large legitimate
transactions may be flagged, and small fraudulent ones may not be.

The app saves the entered transaction details under the authenticated account.
Previously saved assessments retain their original result; reassess a
transaction to apply the current `fixed-amount-thresholds-v1` policy.

#### Assess transactions from a CSV or PDF

After signing in, open **Predict Transaction** and use **Assess transactions
from a CSV or PDF**. CSV files need a header row containing a date column
(`Date` or `Transaction Date`) and an amount column (`Amount`, `Debit`,
`Withdrawal`, or `Credit`). Common optional headers include `Currency`,
`Description`, `Merchant`, `Reference`, `Type`, and `Channel`. For example:

```csv
Date,Amount,Currency,Description,Reference
15/10/2026 14:30,2500.00,INR,Cafe,TX-001
```

CSV dates written with slashes are interpreted as day/month/year. Text-based
PDF statements are also supported when each transaction's date and amount
appear together on a readable text line. Scanned/image PDFs and layouts that
cannot be reliably extracted are not supported. Uploads are limited to 10 MB
and 100 transaction rows. The app previews extracted dates and amounts for
correction before submission; check them carefully, especially PDF rows or
statements that show both transaction amounts and balances. Each submitted
row is saved as a separate amount-based assessment under the signed-in
account. Every MEDIUM/HIGH row remains in the human review queue. Batch email
behavior is based on the highest risk row: a LOW- or MEDIUM-only batch sends
no email, while a batch containing one or more HIGH rows sends one summary
email listing the HIGH rows.

This upload feature does **not** turn ordinary statement fields into the
XGBoost model's required PCA-derived features and does not produce an ML
fraud probability. It applies the same provisional fixed amount thresholds as
the manual assessment form.

#### Supplied synthetic transaction data

The supplied 12,000-row `fraud_transactions_synthetic.csv` can be used to
reproduce an experimental three-tier classifier:

```powershell
.\.venv\Scripts\python.exe -m ml.src.models.train_synthetic_risk_tier --data-path "C:\path\to\fraud_transactions_synthetic.csv"
```

The trainer targets `risk_label` and deliberately excludes `risk_score`,
`is_fraud`, transaction IDs, and reference IDs from the input features. In this
file the labels match `risk_score < 35` (LOW), `35 <= risk_score < 55`
(MEDIUM), and `risk_score >= 55` (HIGH) for all 12,000 rows. The model artifact
is written to `ml/models/risk_tier_synthetic.joblib`; evaluation metrics are
written to `ml/reports/synthetic_risk_tier_metrics.json`.

This dataset has only 181 HIGH labels. On the chronological 2,400-row
development holdout, the experimental model achieved 82.8% accuracy and 0.65
macro-F1, but only 35.7% recall for HIGH (15 of 42 HIGH rows detected). The
result is not accurate enough to replace live assessments or claim reliable
fraud detection; this holdout was consulted during development and is not an
untouched final evaluation. It also uses account-context fields that the
current form/API does not collect. The generated model is therefore not wired
into transaction assessment, dashboard, risk analytics, review queue, or
feedback pages. More representative labeled examples—especially HIGH cases—
and an integration that obtains the model's required account-context features
are needed before a production change.

For review emails, configure `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`,
`SMTP_PASSWORD`, `SMTP_FROM_EMAIL`, and `FRONTEND_BASE_URL` in the private
project-root `.env`. The notification is sent to the email address of the
authenticated account that submitted the transaction. Keep the SMTP password
out of source control and chat; for Gmail use an app password. When a review
is required, the API sends an email link to the authenticated assessment page.
For Gmail, use `SMTP_HOST=smtp.gmail.com`, `SMTP_PORT=587`, and your app
password in `SMTP_PASSWORD`.
The reviewer signs in and chooses **Agree with risk** or **Disagree**; the
choice is saved with an audit record. Operators can decide assessments owned
by their own account; an `ADMIN` reviewer can decide any account's pending
assessment. If SMTP settings are missing or email delivery fails, the
assessment remains saved and the API/UI reports that email was not sent.
Gmail app passwords may be copied with spaces for readability; the application
removes whitespace before attempting Gmail SMTP authentication.

### Recent Application Behavior

* **Model expected cost:** `/transactions/predict` runs the trained model and
  the configured cost-sensitive decision policy using actual `Time`, `Amount`,
  and `V1`–`V28` features. Its expected cost is calculated for that prediction;
  it is not a separately trained model. LOW-risk model predictions report
  `0.00` as requested. The case and transaction list show the cost as a plain
  number, without a currency symbol, because the cost-matrix units are not
  currency.
* **Amount-based assessment:** the ordinary transaction form uses fixed
  amount-based LOW/MEDIUM/HIGH bands for review routing. It does not run the
  XGBoost model and cannot calculate model expected cost from ordinary form
  fields. Do not treat its assessment or a model risk flag as proof of fraud.
* **Next-step guidance:** for an assessment requiring review, the help panel
  recommends contacting the bank using an official number and securing the
  payment method if the transaction is not recognized. For users in India, it
  also points to the 1930 financial cyber-fraud helpline and
  `cybercrime.gov.in`. Users should never share their PIN, password, or
  one-time code.

### Use the Existing PostgreSQL Database and Render API

The backend reads `DATABASE_URL` from the project-root `.env`. Do not start or
create a local PostgreSQL container when you intend to use the existing
database. For local development, start the API on port 8001 to avoid clashes
with older API or Docker processes using port 8000:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8001
```

`docker-compose.yml` passes the same configured `DATABASE_URL` and optional
SMTP reviewer settings through to the API container.
After pulling code changes, apply additive schema migrations with:

```powershell
.\.venv\Scripts\alembic.exe upgrade head
```

This applies the prediction-alert-status migration (`7f15a3c92b44`) as well
as any earlier unapplied revisions. It is required before the updated backend
can persist/read high-risk email delivery status.

For local frontend development, copy `frontend/.env.example` to
`frontend/.env.local`; the default points to the local FastAPI process, which
uses the existing root `.env` database URL at `http://127.0.0.1:8001` (use
`127.0.0.1` rather than `localhost` so requests reach the same local backend).
To use the deployed Render API,
set `VITE_API_BASE_URL` to its API base URL and restart Vite.

The currently deployed Render OpenAPI document has `/transactions/predict`
but does not yet expose `/transactions/analyze` or `/transactions/risk-alerts`.
Deploy the updated backend and apply the additive assessment migration to the
existing PostgreSQL database before configuring the frontend to use the new
assessment endpoints on Render. Do not point this version of the UI at Render
for assessment until those routes are present. The deployed `/health` endpoint
reported the database connected when checked on 2026-10-14.

### Important Files

* `ml/src/models/inference.py` - fraud probability prediction interface
* `ml/models/model_metadata.json` - model configuration and metadata
* `ml/reports/member1_handoff.md` - integration handoff instructions
* `ml/reports/member1_ml_report.md` - Member 1 ML report
* `ml/reports/model_selection_decision.md` - model selection rationale
* `ml/reports/final_test_results.csv` - final test metrics

### Python Environment

Use Python 3.12 and create a virtual environment:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Dataset and Model Artifacts

The original dataset, processed CSV files, and trained `.joblib` model artifacts are excluded from Git by `.gitignore`. They must be obtained through the team's agreed file-sharing method or regenerated using the documented ML pipeline before running inference.

Do not commit the original dataset, virtual environment, or large generated files without team agreement.

### Risk Classification Defaults

The application uses three risk bands based on fraud probability:

* LOW: probability < `RISK_LOW_THRESHOLD`
* MEDIUM: `RISK_LOW_THRESHOLD` <= probability < `RISK_HIGH_THRESHOLD`
* HIGH: probability >= `RISK_HIGH_THRESHOLD`

Initial defaults are `RISK_LOW_THRESHOLD=0.30` and
`RISK_HIGH_THRESHOLD=0.70`, with exact boundaries:

* `0.00 <= p < 0.30`: LOW
* `0.30 <= p < 0.70`: MEDIUM
* `0.70 <= p <= 1.00`: HIGH

These are engineering defaults, not proven optimal thresholds. They are
configurable in `.env` and must be evaluated against validation data, fraud
prevalence, false-positive and missed-fraud costs, and operational review
capacity. The current XGBoost inference returns its raw, uncalibrated
probability: the isotonic calibration experiment did not improve validation
Brier score, and its calibration subset was small. Risk tier is computed
independently of the action.

The prediction engine selects APPROVE, REVIEW, or BLOCK by minimizing expected
cost under the configured cost matrix. With the currently approved costs
(`review=2`, `residual-risk=10`, `block-friction=5`, `block=20`), BLOCK is
never cheaper than REVIEW for any probability from 0 to 1. Therefore live
predictions will not return BLOCK until the project owner revises and validates
the cost assumptions. This is separate from risk classification; a HIGH tier
does not by itself imply BLOCK.

An assessment from the ordinary transaction-entry page remains a separate
history-based heuristic. The existing trained XGBoost model requires `Time`,
`Amount`, and PCA-derived `V1`–`V28`; ordinary merchant/location details cannot
generate those values. The API rejects missing model features rather than
inventing zeros. The model prediction API therefore must receive the actual
model-compatible features from a trusted upstream source.

### Final XGBoost Test Results

* Precision: 0.8125
* Recall: 0.7500
* F1-score: 0.7800
* ROC-AUC: 0.978265
* PR-AUC: 0.768924
* False positives: 9
* False negatives: 13

These results were obtained at a 0.50 classification threshold on the held-out test set. Final business decision thresholds and the operator feedback policy are handled by the relevant project components.


