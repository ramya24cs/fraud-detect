import { useEffect, useState } from "react";
import transactionService from "../services/transactionService";
import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import TransactionAdviceChatbot from "../components/TransactionAdviceChatbot";

const initialTransaction = () => {
  const now = new Date();
  const localDateTime = new Date(
    now.getTime() - now.getTimezoneOffset() * 60_000
  )
    .toISOString()
    .slice(0, 16);

  return {
    amount: "",
    currency: "INR",
    occurredAt: localDateTime,
    type: "UPI",
    merchant: "",
    channel: "Mobile app",
    reference: "",
    location: "",
    remarks: "",
  };
};

const inputStyle = {
  boxSizing: "border-box",
  width: "100%",
  padding: 11,
  border: "1px solid #cbd5e1",
  borderRadius: 7,
  background: "#ffffff",
};

function riskColor(risk) {
  if (risk === "HIGH") return "#b42318";
  if (risk === "MEDIUM") return "#b54708";
  if (risk === "LOW") return "#067647";
  return "#475467";
}

function PredictTransaction() {
  const [transaction, setTransaction] = useState(initialTransaction);
  const [assessment, setAssessment] = useState(null);
  const [pendingReviews, setPendingReviews] = useState([]);
  const [reviewMessage, setReviewMessage] = useState("");
  const [reviewsError, setReviewsError] = useState("");
  const [reviewSubmitting, setReviewSubmitting] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadPendingReviews = async () => {
    try {
      const response = await transactionService.getPendingReviews();
      setPendingReviews(response.items ?? []);
      setReviewsError("");
    } catch (err) {
      setReviewsError(
        err.response?.data?.detail || "Unable to load pending reviews."
      );
    }
  };

  useEffect(() => {
    let active = true;
    transactionService
      .getPendingReviews()
      .then((result) => {
        if (!active) return;
        setPendingReviews(result.items ?? []);
      })
      .catch((err) => {
        if (!active) return;
        setReviewsError(
          err.response?.data?.detail || "Unable to load pending reviews."
        );
      });

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    const assessmentId = new URLSearchParams(window.location.search).get(
      "review"
    );
    if (!assessmentId) return;

    document
      .getElementById(`assessment-review-${assessmentId}`)
      ?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [pendingReviews]);

  const updateTransaction = (name, value) => {
    setTransaction((current) => ({ ...current, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    setAssessment(null);

    try {
      const result = await transactionService.analyzeTransaction({
        amount: Number(transaction.amount),
        currency: transaction.currency,
        occurred_at: new Date(transaction.occurredAt).toISOString(),
        transaction_type: transaction.type,
        merchant: transaction.merchant || null,
        channel: transaction.channel,
        reference: transaction.reference || null,
        location: transaction.location || null,
        remarks: transaction.remarks || null,
      });
      setAssessment(result);
      await loadPendingReviews();
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(
        typeof detail === "string"
          ? detail
          : detail
            ? JSON.stringify(detail)
            : "Assessment failed. Check that the backend and database are running."
      );
    } finally {
      setLoading(false);
    }
  };

  const submitReviewDecision = async (assessmentId, decision) => {
    setReviewSubmitting(assessmentId);
    setReviewMessage("");
    setReviewsError("");
    try {
      await transactionService.submitReviewDecision(assessmentId, decision);
      setReviewMessage(
        `Your ${decision.toLowerCase()} decision was saved.`
      );
      await loadPendingReviews();
    } catch (err) {
      setReviewsError(
        err.response?.data?.detail ||
          "Unable to save the human review decision."
      );
    } finally {
      setReviewSubmitting("");
    }
  };

  const selectedRiskColor = riskColor(assessment?.risk_level);

  return (
    <div className="app-layout">
      <Sidebar />
      <div className="main-area">
        <Navbar />
        <main className="page-content">
          <div className="page-header">
            <div>
              <h1>Transaction Risk Assessment</h1>
              <p>
                Submit a transaction to view its risk status and any required
                next steps.
              </p>
            </div>
            <span className="data-status">
              {loading
                ? "ANALYZING"
                : assessment
                  ? "ASSESSMENT SAVED"
                  : "READY"}
            </span>
          </div>

          {error && (
            <div className="dashboard-info" role="alert">
              <strong>Assessment error:</strong> {error}
            </div>
          )}

          <section className="dashboard-card">
            <h2>Analyze a transaction</h2>

            <form onSubmit={handleSubmit}>
              <div className="dashboard-grid">
                <label>
                  <span style={{ display: "block", marginBottom: 7 }}>
                    Transaction amount
                  </span>
                  <input
                    type="number"
                    min="0.01"
                    step="0.01"
                    required
                    value={transaction.amount}
                    onChange={(event) =>
                      updateTransaction("amount", event.target.value)
                    }
                    placeholder="e.g. 1250.00"
                    style={inputStyle}
                  />
                </label>
                <label>
                  <span style={{ display: "block", marginBottom: 7 }}>
                    Currency
                  </span>
                  <select
                    value={transaction.currency}
                    onChange={(event) =>
                      updateTransaction("currency", event.target.value)
                    }
                    style={inputStyle}
                  >
                    <option value="INR">INR - Indian Rupee</option>
                    <option value="USD">USD - US Dollar</option>
                    <option value="EUR">EUR - Euro</option>
                    <option value="GBP">GBP - British Pound</option>
                  </select>
                </label>
                <label>
                  <span style={{ display: "block", marginBottom: 7 }}>
                    Transaction date and time
                  </span>
                  <input
                    type="datetime-local"
                    required
                    value={transaction.occurredAt}
                    onChange={(event) =>
                      updateTransaction("occurredAt", event.target.value)
                    }
                    style={inputStyle}
                  />
                </label>
                <label>
                  <span style={{ display: "block", marginBottom: 7 }}>
                    Transaction type
                  </span>
                  <select
                    value={transaction.type}
                    onChange={(event) =>
                      updateTransaction("type", event.target.value)
                    }
                    style={inputStyle}
                  >
                    <option value="UPI">UPI</option>
                    <option value="Card">Card</option>
                    <option value="Bank transfer">Bank transfer</option>
                    <option value="Wallet">Digital wallet</option>
                    <option value="Cash">Cash</option>
                    <option value="Other">Other / Unknown</option>
                  </select>
                </label>
                <label>
                  <span style={{ display: "block", marginBottom: 7 }}>
                    Merchant or recipient
                  </span>
                  <input
                    type="text"
                    maxLength={150}
                    value={transaction.merchant}
                    onChange={(event) =>
                      updateTransaction("merchant", event.target.value)
                    }
                    placeholder="Who received the payment?"
                    style={inputStyle}
                  />
                </label>
                <label>
                  <span style={{ display: "block", marginBottom: 7 }}>
                    Payment channel
                  </span>
                  <select
                    value={transaction.channel}
                    onChange={(event) =>
                      updateTransaction("channel", event.target.value)
                    }
                    style={inputStyle}
                  >
                    <option value="Mobile app">Mobile app</option>
                    <option value="Website">Website</option>
                    <option value="In-store POS">In-store POS</option>
                    <option value="ATM">ATM</option>
                    <option value="Bank branch">Bank branch</option>
                    <option value="Other">Other / Unknown</option>
                  </select>
                </label>
                <label>
                  <span style={{ display: "block", marginBottom: 7 }}>
                    Transaction reference ID (optional)
                  </span>
                  <input
                    type="text"
                    maxLength={100}
                    value={transaction.reference}
                    onChange={(event) =>
                      updateTransaction("reference", event.target.value)
                    }
                    placeholder="Enter a reference if available"
                    style={inputStyle}
                  />
                </label>
                <label>
                  <span style={{ display: "block", marginBottom: 7 }}>
                    Location (optional)
                  </span>
                  <input
                    type="text"
                    maxLength={150}
                    value={transaction.location}
                    onChange={(event) =>
                      updateTransaction("location", event.target.value)
                    }
                    placeholder="City or region"
                    style={inputStyle}
                  />
                </label>
                <label style={{ gridColumn: "1 / -1" }}>
                  <span style={{ display: "block", marginBottom: 7 }}>
                    Description or remarks (optional)
                  </span>
                  <textarea
                    rows={3}
                    maxLength={500}
                    value={transaction.remarks}
                    onChange={(event) =>
                      updateTransaction("remarks", event.target.value)
                    }
                    placeholder="Add context for your own review"
                    style={{ ...inputStyle, font: "inherit", resize: "vertical" }}
                  />
                </label>
              </div>
              <button
                type="submit"
                disabled={loading}
                style={{
                  marginTop: 18,
                  padding: "12px 22px",
                  border: 0,
                  borderRadius: 7,
                  background: loading ? "#94a3b8" : "#175cd3",
                  color: "#ffffff",
                  fontWeight: 600,
                  cursor: loading ? "wait" : "pointer",
                }}
              >
                {loading ? "Analyzing..." : "Analyze transaction"}
              </button>
            </form>
          </section>

          {assessment && (
            <section
              className="dashboard-card"
              aria-live="polite"
              style={{ marginTop: 20 }}
            >
              <div className="page-header">
                <div>
                  <h2>Transaction assessment</h2>
                </div>
                <span
                  style={{
                    color: selectedRiskColor,
                    background: `${selectedRiskColor}18`,
                    padding: "8px 14px",
                    borderRadius: 20,
                    fontWeight: 700,
                  }}
                >
                  {assessment.risk_level.replaceAll("_", " ")}
                </span>
              </div>

              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-card-title">Transaction amount</div>
                  <div className="stat-card-value">
                    {assessment.currency} {Number(assessment.amount).toLocaleString()}
                  </div>
                  <div className="stat-card-subtitle">
                    Submitted transaction
                  </div>
                </div>
                <div className="stat-card">
                  <div className="stat-card-title">Human decision</div>
                  <div className="stat-card-value">
                    {assessment.review_required ? "Required" : "Not required"}
                  </div>
                  <div className="stat-card-subtitle">
                    {assessment.review_required
                      ? assessment.review_notification_status === "SENT"
                        ? "Review email accepted for delivery"
                        : "Please review the transaction below"
                      : "No review needed"}
                  </div>
                </div>
              </div>

              {assessment.review_required && (
                <p role="status">
                  {assessment.review_notification_message ||
                    "A human review is required."}
                </p>
              )}
            </section>
          )}

          <section className="dashboard-card" style={{ marginTop: 20 }}>
            <h2>Human review decisions</h2>
            <p>
              MEDIUM and HIGH transactions await an agree/disagree human
              decision. The decision is saved with an audit record.
            </p>
            {reviewsError && (
              <p role="alert" style={{ color: "#b42318" }}>
                {reviewsError}
              </p>
            )}
            {reviewMessage && <p role="status">{reviewMessage}</p>}
            {pendingReviews.length === 0 ? (
              <p>No assessments are waiting for human review.</p>
            ) : (
              <div style={{ display: "grid", gap: 12 }}>
                {pendingReviews.map((item) => (
                  <article
                    key={item.assessment_id}
                    className="stat-card"
                    id={`assessment-review-${item.assessment_id}`}
                    aria-label={`Pending ${item.risk_level.toLowerCase()} review`}
                  >
                    <strong>
                      {item.risk_level} · {item.currency}{" "}
                      {Number(item.amount).toFixed(2)}
                    </strong>
                    <p>
                      {item.transaction_type} via {item.channel}
                      {item.merchant ? ` · ${item.merchant}` : ""}
                      {item.reference ? ` · ${item.reference}` : ""}
                    </p>
                    <div style={{ display: "flex", gap: 8 }}>
                      <button
                        type="button"
                        disabled={Boolean(reviewSubmitting)}
                        onClick={() =>
                          submitReviewDecision(item.assessment_id, "AGREE")
                        }
                      >
                        {reviewSubmitting === item.assessment_id
                          ? "Saving..."
                          : "Agree with risk"}
                      </button>
                      <button
                        type="button"
                        disabled={Boolean(reviewSubmitting)}
                        onClick={() =>
                          submitReviewDecision(item.assessment_id, "DISAGREE")
                        }
                      >
                        Disagree
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>

          {assessment?.review_required && (
            <section
              className="dashboard-card"
              aria-label="Transaction review email"
              style={{ marginTop: 20 }}
            >
              <h2>Review email</h2>
              <p>
                <strong>Status:</strong>{" "}
                {assessment.review_notification_status === "SENT"
                  ? "Accepted for delivery"
                  : "Not sent"}
              </p>
              <p>
                <strong>To:</strong>{" "}
                {assessment.review_notification_recipient}
              </p>
              {assessment.review_notification_subject && (
                <p>
                  <strong>Subject:</strong>{" "}
                  {assessment.review_notification_subject}
                </p>
              )}
              {assessment.review_notification_content && (
                <pre
                  style={{
                    whiteSpace: "pre-wrap",
                    overflowWrap: "anywhere",
                    font: "inherit",
                    padding: 14,
                    borderRadius: 8,
                    background: "#f8fafc",
                  }}
                >
                  {assessment.review_notification_content}
                </pre>
              )}
            </section>
          )}

          {assessment && (
            <TransactionAdviceChatbot
              key={assessment.assessment_id}
              assessment={assessment}
            />
          )}
        </main>
      </div>
    </div>
  );
}

export default PredictTransaction;
