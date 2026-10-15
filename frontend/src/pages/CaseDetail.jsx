
import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";

import api from "../services/api";
import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import RiskBadge from "../components/RiskBadge";
import DecisionBadge from "../components/DecisionBadge";
import FeedbackForm from "../components/FeedbackForm";
import ShapExplanation from "../components/ShapExplanation";
import { formatCost } from "../utils/formatters";

function formatCurrency(value) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  const number = Number(value);

  if (!Number.isFinite(number)) {
    return "—";
  }

  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(number);
}

function formatProbability(value) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  let number = Number(value);

  if (!Number.isFinite(number)) {
    return "—";
  }

  if (number > 1 && number <= 100) {
    number /= 100;
  }

  if (number < 0 || number > 1) {
    return "—";
  }

  return `${(number * 100).toFixed(2)}%`;
}

function getDecision(value) {
  const decision = String(value ?? "").trim().toUpperCase();

  if (["APPROVE", "APPROVED"].includes(decision)) {
    return "APPROVE";
  }

  if (["REVIEW", "REVIEW_REQUIRED"].includes(decision)) {
    return "REVIEW";
  }

  if (["BLOCK", "BLOCKED"].includes(decision)) {
    return "BLOCK";
  }

  return value ?? "—";
}

function getErrorMessage(err) {
  const detail = err?.response?.data?.detail;

  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) =>
        typeof item === "string"
          ? item
          : item?.msg ?? JSON.stringify(item)
      )
      .join(", ");
  }

  if (detail && typeof detail === "object") {
    return JSON.stringify(detail);
  }

  return err?.message ?? "An unexpected error occurred.";
}

function CaseDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [transaction, setTransaction] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [feedbackMessage, setFeedbackMessage] = useState("");
  const [feedbackError, setFeedbackError] = useState("");
  const [submittingFeedback, setSubmittingFeedback] = useState(false);

  useEffect(() => {
    let active = true;

    async function loadCase() {
      setLoading(true);
      setError("");
      setTransaction(null);

      try {
        const response = await api.get(
          `/transactions/${encodeURIComponent(id)}`
        );

        if (!active) {
          return;
        }

        const data =
          response.data?.item ??
          response.data?.data ??
          response.data;

        setTransaction(data);
      } catch (err) {
        if (!active) {
          return;
        }

        setError(
          err.response?.status === 404
            ? "Transaction not found."
            : getErrorMessage(err)
        );
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    if (id) {
      loadCase();
    } else {
      setError("Transaction ID is missing.");
      setLoading(false);
    }

    return () => {
      active = false;
    };
  }, [id]);

  async function handleFeedback({
    transactionId,
    feedback,
    operatorDecision,
    reasonCode,
    comment,
  }) {
    setSubmittingFeedback(true);
    setFeedbackMessage("");
    setFeedbackError("");

    try {
      const payload = {
        transaction_id:
          transactionId ?? transaction?.transaction_id ?? id,
        operator_decision: String(operatorDecision ?? "")
          .trim()
          .toUpperCase(),
        reason_code: String(reasonCode ?? "")
          .trim()
          .toUpperCase(),
        feedback: String(feedback ?? "")
          .trim()
          .toUpperCase(),
        comment: String(comment ?? "").trim(),
      };

      if (
        !payload.transaction_id ||
        !payload.operator_decision ||
        !payload.reason_code ||
        !payload.feedback
      ) {
        throw new Error("Please complete all required feedback fields.");
      }

      const response = await api.post("/feedback", payload);

      setFeedbackMessage(
        response.data?.message ??
          "Feedback submitted successfully."
      );

      return response.data;
    } catch (err) {
      setFeedbackError(getErrorMessage(err));
      throw err;
    } finally {
      setSubmittingFeedback(false);
    }
  }

  const prediction = transaction?.prediction ?? {};

  const rawExplanation =
    prediction.shap_explanation ??
    prediction.explanation ??
    prediction.feature_importance;

  const explanation = Array.isArray(rawExplanation)
    ? rawExplanation
    : [];
  const riskAlertStatus = prediction.risk_alert_status;

  return (
    <div className="app-layout">
      <Sidebar />

      <div className="main-area">
        <Navbar />

        <main className="page-content">
          <div className="page-header">
            <div>
              <h1>Case Details</h1>
              <p>
                Transaction ID: <strong>{id || "—"}</strong>
              </p>
            </div>

            <span className="data-status">
              {loading
                ? "LOADING DATA"
                : transaction
                  ? "LIVE API DATA"
                  : "UNAVAILABLE"}
            </span>
          </div>

          {loading && (
            <div className="dashboard-card">
              <p>Loading transaction details...</p>
            </div>
          )}

          {!loading && error && (
            <div className="dashboard-info" role="alert">
              <p>{error}</p>

              <button
                type="button"
                onClick={() => navigate("/review-queue")}
              >
                Back to Review Queue
              </button>
            </div>
          )}

          {!loading && transaction && (
            <>
              <section className="stats-grid">
                <div className="dashboard-card">
                  <h3>Transaction Amount</h3>
                  <h2>{formatCurrency(transaction.amount)}</h2>
                </div>

                <div className="dashboard-card">
                  <h3>Fraud Probability</h3>
                  <h2>
                    {formatProbability(prediction.fraud_probability)}
                  </h2>
                </div>

                <div className="dashboard-card">
                  <h3>Risk Level</h3>
                  <RiskBadge level={prediction.risk_level} />
                </div>

                <div className="dashboard-card">
                  <h3>System Decision</h3>
                  <DecisionBadge
                    decision={getDecision(prediction.decision)}
                  />
                </div>
              </section>

              <section className="dashboard-card" aria-live="polite">
                <h2>Model risk assessment</h2>
                <p>
                  <RiskBadge level={prediction.risk_level} />{" "}
                  <strong>
                    {formatProbability(prediction.fraud_probability)} estimated
                    fraud probability
                  </strong>
                </p>
                <p>
                  Risk describes the model estimate. The separate recommended
                  action is selected by the configured expected-cost matrix.
                </p>
                {prediction.explanation_summary && (
                  <p>{prediction.explanation_summary}</p>
                )}
                <p>
                  {prediction.review_required
                    ? "Operator review is required."
                    : "Operator review is not required by the selected action."}
                </p>
                {prediction.risk_alert_triggered && (
                  <p role="status">
                    High-risk alert:{" "}
                    {riskAlertStatus === "SENT"
                      ? "email sent."
                      : riskAlertStatus === "NOT_CONFIGURED"
                        ? "SMTP is not configured; email was not sent."
                        : riskAlertStatus === "FAILED"
                          ? "email delivery failed."
                          : riskAlertStatus === "STATUS_NOT_SAVED"
                            ? "delivery was attempted, but its status could not be saved."
                            : riskAlertStatus === "PENDING"
                              ? "email status is pending or could not be recorded."
                              : "triggered; notification status is unavailable."}
                  </p>
                )}
                <p>
                  The existing XGBoost model returns raw, uncalibrated
                  probabilities. Its required inputs are Time, Amount, and
                  PCA-derived V1–V28; ordinary merchant, location, or device
                  details are not transformed into those model features.
                </p>
              </section>

              <section className="dashboard-grid">
                <div className="dashboard-card">
                  <h2>Decision Information</h2>

                  <p>
                    <strong>External ID:</strong>{" "}
                    {transaction.external_id ?? "—"}
                  </p>

                  <p>{formatCost(prediction.expected_cost)}</p>

                  <p>
                    <strong>Model Version:</strong>{" "}
                    {prediction.model_version ?? "—"}
                  </p>

                  <p>
                    <strong>Prediction Created At:</strong>{" "}
                    {prediction.prediction_timestamp ??
                    prediction.created_at
                      ? new Date(
                          prediction.prediction_timestamp ??
                            prediction.created_at
                        ).toLocaleString("en-IN")
                      : "—"}
                  </p>

                  <p>
                    <strong>Transaction Created At:</strong>{" "}
                    {transaction.created_at
                      ? new Date(
                          transaction.created_at
                        ).toLocaleString("en-IN")
                      : "—"}
                  </p>
                </div>

                <div className="dashboard-card">
                  <h2>Feature Explanation</h2>
                  <p>
                    Feature contributions describe this model output; they do
                    not independently prove fraud.
                  </p>

                  {explanation.length > 0 ? (
                    <ShapExplanation
                      explanation={explanation}
                    />
                  ) : (
                    <p>
                      SHAP explanation data is not available in the
                      transaction response. Transaction input
                      features are not SHAP contributions.
                    </p>
                  )}

                  <details>
                    <summary>View transaction features</summary>

                    <ul>
                      {Object.entries(
                        transaction.features ?? {}
                      ).map(([name, value]) => (
                        <li key={name}>
                          <strong>{name}:</strong>{" "}
                          {String(value)}
                        </li>
                      ))}
                    </ul>
                  </details>
                </div>
              </section>

              <section className="dashboard-card">
                <h2>Operator Feedback</h2>

                <p>
                  Submit your decision and observations for this
                  transaction.
                </p>

                <FeedbackForm
                  transactionId={transaction.transaction_id ?? id}
                  onSubmit={handleFeedback}
                />

                {submittingFeedback && (
                  <p>Submitting feedback...</p>
                )}

                {feedbackMessage && (
                  <div className="dashboard-info" role="status">
                    <p>{feedbackMessage}</p>
                  </div>
                )}

                {feedbackError && (
                  <div className="dashboard-info" role="alert">
                    <p>{feedbackError}</p>
                  </div>
                )}
              </section>
            </>
          )}

          <button
            type="button"
            onClick={() => navigate("/review-queue")}
          >
            Back to Review Queue
          </button>
        </main>
      </div>
    </div>
  );
}

export default CaseDetail;
