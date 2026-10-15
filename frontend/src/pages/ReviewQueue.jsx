import { useCallback, useEffect, useState } from "react";
import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import transactionService from "../services/transactionService";

function ReviewQueue() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [search, setSearch] = useState("");

  const loadQueue = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await transactionService.getPendingReviews();
      setItems(response.items ?? []);
    } catch (requestError) {
      setItems([]);
      setError(
        requestError.response?.data?.detail ||
          "Unable to load transactions awaiting human review."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    async function fetchInitialQueue() {
      setError("");
      try {
        const response = await transactionService.getPendingReviews();
        if (active) setItems(response.items ?? []);
      } catch (requestError) {
        if (active) {
          setItems([]);
          setError(
            requestError.response?.data?.detail ||
              "Unable to load transactions awaiting human review."
          );
        }
      } finally {
        if (active) setLoading(false);
      }
    }
    fetchInitialQueue();
    return () => {
      active = false;
    };
  }, []);

  const decide = async (assessmentId, decision) => {
    setSubmitting(assessmentId);
    setError("");
    setMessage("");
    try {
      await transactionService.submitReviewDecision(assessmentId, decision);
      setMessage(
        `Your ${decision.toLowerCase()} decision was saved and audited.`
      );
      await loadQueue();
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail ||
          "Could not save your review decision."
      );
    } finally {
      setSubmitting("");
    }
  };

  const visibleItems = items.filter((item) => {
    const query = search.trim().toLowerCase();
    return (
      !query ||
      [item.reference, item.merchant, item.transaction_type, item.location]
        .filter(Boolean)
        .some((value) => value.toLowerCase().includes(query))
    );
  });
  const highRiskCount = items.filter(
    (item) => item.risk_level === "HIGH"
  ).length;
  const mediumRiskCount = items.filter(
    (item) => item.risk_level === "MEDIUM"
  ).length;

  return (
    <div className="app-layout">
      <Sidebar />
      <div className="main-area">
        <Navbar />
        <main className="page-content">
          <div className="page-header">
            <div className="review-page-title">
              <h1>Human Review Queue</h1>
              <span>Transactions awaiting your decision</span>
            </div>
            <div className="review-header-actions">
              <span className="review-queue-count">
                {loading ? "Loading..." : `${items.length} open`}
              </span>
              <button
                className="review-refresh-button"
                type="button"
                onClick={loadQueue}
                disabled={loading}
              >
                Refresh
              </button>
            </div>
          </div>

          {error && (
            <div className="dashboard-info review-notice" role="alert">
              {error}
              <button
                className="review-refresh-button"
                type="button"
                onClick={loadQueue}
                disabled={loading}
              >
                Retry
              </button>
            </div>
          )}
          {message && (
            <div className="dashboard-info review-success" role="status">
              {message}
            </div>
          )}

          <section className="review-summary-grid" aria-label="Review summary">
            <div className="review-summary-card">
              <span className="review-summary-label">Open reviews</span>
              <strong>{loading ? "—" : items.length}</strong>
              <span className="review-summary-mark">Total queue</span>
            </div>
            <div className="review-summary-card high">
              <span className="review-summary-label">High risk</span>
              <strong>{loading ? "—" : highRiskCount}</strong>
              <span className="review-summary-mark">Priority</span>
            </div>
            <div className="review-summary-card medium">
              <span className="review-summary-label">Medium risk</span>
              <strong>{loading ? "—" : mediumRiskCount}</strong>
              <span className="review-summary-mark">Needs review</span>
            </div>
          </section>

          <section className="review-search-card">
            <label htmlFor="review-search">Search transactions</label>
            <span>Reference, recipient, type, or location</span>
            <input
              id="review-search"
              className="review-search-input"
              type="search"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search pending reviews"
            />
          </section>

          {loading ? (
            <section className="review-empty-state" role="status">
              <span className="review-loading-mark" aria-hidden="true" />
              <h2>Loading reviews</h2>
              <p>Fetching transactions that need your attention.</p>
            </section>
          ) : visibleItems.length === 0 ? (
            <section className="review-empty-state">
              <span className="review-empty-mark" aria-hidden="true">
                {items.length ? "NO MATCH" : "✓"}
              </span>
              <h2>{items.length ? "No matching reviews" : "Queue is clear"}</h2>
              <p>
                {items.length
                  ? "No pending entries match your search."
                  : "There are no transactions waiting for human review."}
              </p>
            </section>
          ) : (
            <section
              className="review-queue-list"
              aria-label="Pending transactions"
            >
              {visibleItems.map((item) => (
                <article
                  className={`review-transaction-card risk-${String(item.risk_level).toLowerCase()}`}
                  key={item.assessment_id}
                >
                  <div className="review-transaction-heading">
                    <div className="review-amount">
                      <span>Transaction amount</span>
                      <strong>
                        {item.currency}{" "}
                        {Number(item.amount).toLocaleString("en-IN", {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </strong>
                    </div>
                    <span
                      className={`review-risk-badge risk-${String(item.risk_level).toLowerCase()}`}
                    >
                      {item.risk_level} RISK
                    </span>
                  </div>
                  <div className="review-transaction-details">
                    <div>
                      <span>Reference / recipient</span>
                      <strong>
                        {item.reference || item.merchant || "Transaction"}
                      </strong>
                    </div>
                    <div>
                      <span>Type and channel</span>
                      <strong>
                        {[item.transaction_type, item.channel]
                          .filter(Boolean)
                          .join(" · ") || "—"}
                      </strong>
                    </div>
                    {item.location && (
                      <div>
                        <span>Location</span>
                        <strong>{item.location}</strong>
                      </div>
                    )}
                  </div>
                  <div className="review-transaction-footer">
                    <time dateTime={item.created_at}>
                      {new Date(item.created_at).toLocaleString()}
                    </time>
                    <div className="review-decision-actions">
                      <button
                        className="review-decision-button agree"
                        type="button"
                        disabled={Boolean(submitting)}
                        onClick={() => decide(item.assessment_id, "AGREE")}
                      >
                        {submitting === item.assessment_id
                          ? "Saving..."
                          : "Agree with risk"}
                      </button>
                      <button
                        className="review-decision-button disagree"
                        type="button"
                        disabled={Boolean(submitting)}
                        onClick={() => decide(item.assessment_id, "DISAGREE")}
                      >
                        Disagree
                      </button>
                    </div>
                  </div>
                </article>
              ))}
            </section>
          )}
        </main>
      </div>
    </div>
  );
}

export default ReviewQueue;
