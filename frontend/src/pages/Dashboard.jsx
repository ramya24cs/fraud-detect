import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import DistributionDonut from "../components/DistributionDonut";
import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import transactionService from "../services/transactionService";

const RISK_COLORS = { LOW: "#16a34a", MEDIUM: "#f59e0b", HIGH: "#dc2626" };

function formatAmount(amount, currency = "INR") {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(Number(amount) || 0);
}

function Dashboard() {
  const navigate = useNavigate();
  const [assessments, setAssessments] = useState([]);
  const [pendingCount, setPendingCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchDashboard = useCallback(
    () =>
      Promise.all([
        transactionService.getAssessments({ limit: 500 }),
        transactionService.getPendingReviews(),
      ]),
    []
  );

  useEffect(() => {
    let active = true;
    fetchDashboard()
      .then(([history, pending]) => {
        if (!active) return;
        setAssessments(history.items ?? []);
        setPendingCount(pending.total ?? pending.items?.length ?? 0);
      })
      .catch((requestError) => {
        if (!active) return;
        setError(
          requestError.response?.data?.detail ||
            "Unable to load account transaction assessments."
        );
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [fetchDashboard]);

  const loadDashboard = async () => {
    setLoading(true);
    setError("");
    try {
      const [history, pending] = await fetchDashboard();
      setAssessments(history.items ?? []);
      setPendingCount(pending.total ?? pending.items?.length ?? 0);
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail ||
          "Unable to load account transaction assessments."
      );
    } finally {
      setLoading(false);
    }
  };

  const riskCounts = useMemo(
    () =>
      ["LOW", "MEDIUM", "HIGH"].map((risk) => ({
        name: risk,
        count: assessments.filter((item) => item.risk_level === risk).length,
      })),
    [assessments]
  );
  const reviewedCount = assessments.filter(
    (item) => item.review_decision
  ).length;
  const recent = assessments.slice(0, 6);
  const statCards = [
    {
      title: "Transactions assessed",
      value: assessments.length,
      tone: "total",
      marker: "TX",
      note: "Saved to your account",
    },
    {
      title: "Low risk",
      value: riskCounts[0].count,
      tone: "low",
      marker: "L",
      note: "Classified as low risk",
    },
    {
      title: "Medium risk",
      value: riskCounts[1].count,
      tone: "medium",
      marker: "M",
      note: "Closer assessment recommended",
    },
    {
      title: "High risk",
      value: riskCounts[2].count,
      tone: "high",
      marker: "H",
      note: "Priority attention",
    },
    {
      title: "Awaiting review",
      value: pendingCount,
      tone: "review",
      marker: "!",
      note: "Open in review queue",
    },
    {
      title: "Human decisions",
      value: reviewedCount,
      tone: "decisions",
      marker: "✓",
      note: "Completed review decisions",
    },
  ];

  return (
    <div className="app-layout">
      <Sidebar />
      <div className="main-area">
        <Navbar />
        <main className="page-content dashboard-page">
          <div className="dashboard-hero">
            <div className="dashboard-hero-copy">
              <span className="dashboard-eyebrow">
                <span className="dashboard-eyebrow-dot" />
                PERSONAL RISK OVERVIEW
              </span>
              <h1>Your transaction dashboard</h1>
              <p>
                Monitor assessed activity, risk distribution and outstanding
                reviews in one place.
              </p>
            </div>
            <div className="dashboard-hero-actions">
              <span className="dashboard-live-label">
                <span />
                ACCOUNT VIEW
              </span>
              <button
                className="dashboard-refresh-button"
                type="button"
                onClick={loadDashboard}
                disabled={loading}
              >
                <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
                  <path
                    d="M16.2 8A6.5 6.5 0 0 0 5 5.4L3.8 7M3.8 7V3.8M3.8 7H7m-3.2 5A6.5 6.5 0 0 0 15 14.6l1.2-1.6m0 0v3.2m0-3.2H13"
                    stroke="currentColor"
                    strokeWidth="1.6"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
                {loading ? "Updating" : "Refresh"}
              </button>
            </div>
          </div>

          {error && (
            <div className="dashboard-info" role="alert">
              {error}
            </div>
          )}

          <section className="stats-grid dashboard-stats">
            {statCards.map((card) => (
              <div
                className={`stat-card dashboard-stat-card tone-${card.tone}`}
                key={card.title}
              >
                <div className="dashboard-stat-topline">
                  <span className="dashboard-stat-marker" aria-hidden="true">
                    {card.marker}
                  </span>
                  <span className="dashboard-stat-title">{card.title}</span>
                </div>
                <div className="dashboard-stat-value">
                  {loading ? "—" : card.value}
                </div>
                <div className="dashboard-stat-note">
                  <span className="dashboard-stat-note-dot" />
                  {card.note}
                </div>
              </div>
            ))}
          </section>

          <section className="dashboard-grid dashboard-overview-grid">
            <div className="dashboard-card dashboard-risk-card">
              <div className="dashboard-card-heading">
                <div>
                  <span className="dashboard-card-kicker">DISTRIBUTION</span>
                  <h2>Risk level overview</h2>
                </div>
                <span className="dashboard-heading-icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24" fill="none">
                    <path
                      d="M4 19V5m0 14h16M8 15l3-4 3 2 5-7"
                      stroke="currentColor"
                      strokeWidth="1.7"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </span>
              </div>
              {assessments.length ? (
                <>
                  <DistributionDonut
                    counts={riskCounts}
                    total={assessments.length}
                    colors={RISK_COLORS}
                    caption="Share of assessed transactions"
                  />
                  <div className="dashboard-risk-scale" aria-hidden="true">
                    {riskCounts.map(({ name, count }) => (
                      <span
                        key={name}
                        className={`risk-scale-${name.toLowerCase()}`}
                        style={{
                          flexGrow: count || 0.015,
                          flexBasis: 0,
                        }}
                      />
                    ))}
                  </div>
                </>
              ) : (
                <div className="dashboard-empty-overview">
                  <span aria-hidden="true">◎</span>
                  <p>
                    {loading
                      ? "Loading your account overview..."
                      : "No transactions have been assessed yet."}
                  </p>
                </div>
              )}
            </div>
            <div className="dashboard-card dashboard-review-card">
              <div className="dashboard-card-heading">
                <div>
                  <span className="dashboard-card-kicker">NEXT ACTION</span>
                  <h2>Open human reviews</h2>
                </div>
                <span className="dashboard-heading-icon review-heading-icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24" fill="none">
                    <path
                      d="M12 8v4m0 4h.01M10.3 3.9 2.9 17a2 2 0 0 0 1.8 3h14.6a2 2 0 0 0 1.8-3l-7.4-13.1a2 2 0 0 0-3.4 0Z"
                      stroke="currentColor"
                      strokeWidth="1.7"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </span>
              </div>
              <p className="dashboard-review-description">
                Transactions waiting for your agree/disagree decision.
              </p>
              <div className="dashboard-review-summary">
                <div
                  className={`dashboard-review-count${pendingCount ? " is-pending" : ""}`}
                  aria-label={`${loading ? "Loading" : pendingCount} open human reviews`}
                >
                  {loading ? "—" : pendingCount}
                </div>
                <span className="dashboard-review-label">
                  {pendingCount === 1
                    ? "review needs attention"
                    : "reviews need attention"}
                </span>
              </div>
              <button
                className="dashboard-review-button"
                type="button"
                onClick={() => navigate("/review-queue")}
              >
                Review transactions <span aria-hidden="true">→</span>
              </button>
            </div>
          </section>

          <section className="dashboard-card dashboard-recent-card">
            <div className="dashboard-recent-heading">
              <div>
                <span className="dashboard-card-kicker">YOUR ACTIVITY</span>
                <h2>Recent assessments</h2>
                <p>Latest transactions saved to your account.</p>
              </div>
              <button
                className="dashboard-assess-button"
                type="button"
                onClick={() => navigate("/predict-transaction")}
              >
                <span aria-hidden="true">＋</span>
                Assess a transaction
              </button>
            </div>
            <div className="transaction-table-container dashboard-table-wrap">
              <table className="transaction-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Reference / Recipient</th>
                    <th>Amount</th>
                    <th>Risk</th>
                    <th>Human review</th>
                  </tr>
                </thead>
                <tbody>
                  {recent.map((item) => (
                    <tr key={item.assessment_id}>
                      <td>{new Date(item.created_at).toLocaleString()}</td>
                      <td className="dashboard-reference">
                        {item.reference || item.merchant || "—"}
                      </td>
                      <td className="dashboard-amount">
                        {formatAmount(item.amount, item.currency)}
                      </td>
                      <td>
                        <span
                          className={`dashboard-risk-badge risk-${item.risk_level.toLowerCase()}`}
                        >
                          <span />
                          {item.risk_level.replaceAll("_", " ")}
                        </span>
                      </td>
                      <td>
                        <span
                          className={`dashboard-review-badge ${
                            item.review_decision
                              ? "is-complete"
                              : item.review_required
                                ? "is-pending"
                                : "is-not-required"
                          }`}
                        >
                          {item.review_decision ||
                            (item.review_required
                              ? "Pending"
                              : "Not required")}
                        </span>
                      </td>
                    </tr>
                  ))}
                  {!loading && recent.length === 0 && (
                    <tr>
                      <td colSpan={5}>No assessments found.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}

export default Dashboard;
