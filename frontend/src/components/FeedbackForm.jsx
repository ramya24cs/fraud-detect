
import { useState } from "react";

const demoMode = import.meta.env.VITE_DEMO_MODE === "true";

const feedbackOptions = [
  { value: "CONFIRMED_FRAUD", label: "Confirmed Fraud" },
  { value: "CONFIRMED_GENUINE", label: "Confirmed Genuine" },
  { value: "DISPUTED", label: "Disputed" },
  { value: "INCONCLUSIVE", label: "Inconclusive" },
];


const decisionOptions = [
  { value: "CONFIRMED_FRAUD", label: "Confirmed Fraud" },
  { value: "CONFIRMED_GENUINE", label: "Confirmed Genuine" },
  { value: "DISPUTED", label: "Disputed" },
  { value: "INCONCLUSIVE", label: "Inconclusive" },
];


const reasonOptions = [
  { value: "OPERATOR_REVIEW", label: "Operator Review" },
  { value: "SUSPECTED_FRAUD", label: "Suspected Fraud" },
  { value: "VERIFIED_GENUINE", label: "Verified Genuine" },
  {
    value: "INSUFFICIENT_INFORMATION",
    label: "Insufficient Information",
  },
];

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

  return err?.message ?? "Unable to submit feedback. Please try again.";
}

function FeedbackForm({ transactionId, onSubmitted, onSubmit }) {
  const [feedback, setFeedback] = useState("");
  const [operatorDecision, setOperatorDecision] = useState("INCONCLUSIVE");
  const [reasonCode, setReasonCode] = useState("OPERATOR_REVIEW");
  const [comment, setComment] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  function clearMessages() {
    setMessage("");
    setError("");
  }

  async function handleSubmit(event) {
    event.preventDefault();
    clearMessages();

    if (!transactionId) {
      setError("Transaction ID is missing.");
      return;
    }

    if (!feedback || !operatorDecision || !reasonCode) {
      setError("Please complete all required fields.");
      return;
    }

    if (demoMode) {
      setMessage(
        "Demo mode is enabled. Feedback has not been saved to the backend."
      );
      return;
    }

    if (typeof onSubmit !== "function") {
      setError("Feedback submission handler is not configured.");
      return;
    }

    setLoading(true);

    try {
      const payload = {
        transactionId,
        feedback: String(feedback).trim().toUpperCase(),
        operatorDecision: String(operatorDecision).trim().toUpperCase(),
        reasonCode: String(reasonCode).trim().toUpperCase(),
        comment: comment.trim(),
      };

      await onSubmit(payload);

      setMessage("Feedback submitted successfully.");
      setFeedback("");
      setComment("");

      if (typeof onSubmitted === "function") {
        await onSubmitted();
      }
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="feedback-form">
      <h3>Operator Feedback</h3>

      <p>
        Submit your assessment and observations for this transaction.
      </p>

      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="feedback">Feedback Label</label>

          <select
            id="feedback"
            name="feedback"
            value={feedback}
            onChange={(event) => {
              setFeedback(event.target.value);
              clearMessages();
            }}
            required
            disabled={loading}
          >
            <option value="">Select feedback</option>

            {feedbackOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="operatorDecision">
            Operator Decision
          </label>

          <select
            id="operatorDecision"
            name="operator_decision"
            value={operatorDecision}
            onChange={(event) => {
              setOperatorDecision(event.target.value);
              clearMessages();
            }}
            required
            disabled={loading}
          >
            {decisionOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="reasonCode">Reason Code</label>

          <select
            id="reasonCode"
            name="reason_code"
            value={reasonCode}
            onChange={(event) => {
              setReasonCode(event.target.value);
              clearMessages();
            }}
            required
            disabled={loading}
          >
            {reasonOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="comment">Operator Comment</label>

          <textarea
            id="comment"
            name="comment"
            value={comment}
            onChange={(event) => {
              setComment(event.target.value);
              clearMessages();
            }}
            placeholder="Enter your observations..."
            rows={4}
            disabled={loading}
          />
        </div>

        {error && (
          <p className="feedback-error" role="alert">
            {error}
          </p>
        )}

        {message && (
          <p className="feedback-success" role="status">
            {message}
          </p>
        )}

        <button type="submit" disabled={loading}>
          {loading ? "Submitting..." : "Submit Feedback"}
        </button>
      </form>
    </div>
  );
}

export default FeedbackForm;
