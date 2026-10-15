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

  return (
    <div className="app-layout">
      <Sidebar />
      <div className="main-area">
        <Navbar />
        <main className="page-content">
          <div className="page-header">
            <div>
              <h1>Fraud Detection Dashboard</h1>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <button
                type="button"
                onClick={loadDashboard}
                disabled={loading}
              >
                Refresh
              </button>
            </div>
          </div>

          {error && (
            <div className="dashboard-info" role="alert">
              {error}
            </div>
          )}

          <section className="stats-grid">
            {[
              ["Transactions assessed", assessments.length],
              ["Low risk", riskCounts[0].count],
              ["Medium risk", riskCounts[1].count],
              ["High risk", riskCounts[2].count],
              ["Awaiting review", pendingCount],
              ["Human decisions", reviewedCount],
            ].map(([title, value]) => (
              <div className="stat-card" key={title}>
                <div className="stat-card-title">{title}</div>
                <div className="stat-card-value">
                  {loading ? "—" : value}
                </div>
                <div className="stat-card-subtitle">Current account</div>
              </div>
            ))}
          </section>

          <section className="dashboard-grid">
            <div className="dashboard-card">
              <h2>Risk level overview</h2>
              {assessments.length ? (
                <DistributionDonut
                  counts={riskCounts}
                  total={assessments.length}
                  colors={RISK_COLORS}
                  caption="Share of assessed transactions"
                />
              ) : (
                <p>
                  {loading
                    ? "Loading assessments..."
                    : "No transactions have been assessed yet."}
                </p>
              )}
            </div>
            <div className="dashboard-card">
              <h2>Open human reviews</h2>
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
                  {pendingCount === 1 ? "review needs attention" : "reviews need attention"}
                </span>
              </div>
              <button
                className="dashboard-review-button"
                type="button"
                onClick={() => navigate("/review-queue")}
              >
                Open review queue <span aria-hidden="true">→</span>
              </button>
            </div>
          </section>

          <section className="dashboard-card">
            <div className="page-header">
              <div>
                <h2>Recent assessments</h2>
                <p>Latest transaction entries saved for your account.</p>
              </div>
              <button
                type="button"
                onClick={() => navigate("/predict-transaction")}
              >
                Assess transaction
              </button>
            </div>
            <div className="transaction-table-container">
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
                      <td>{item.reference || item.merchant || "—"}</td>
                      <td>{formatAmount(item.amount, item.currency)}</td>
                      <td>{item.risk_level}</td>
                      <td>
                        {item.review_decision ||
                          (item.review_required ? "Pending" : "Not required")}
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
