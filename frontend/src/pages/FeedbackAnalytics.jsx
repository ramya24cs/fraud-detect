import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import DistributionDonut from "../components/DistributionDonut";
import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import api from "../services/api";
import transactionService from "../services/transactionService";

const COLORS = { AGREE: "#16a34a", DISAGREE: "#dc2626", PENDING: "#f59e0b" };

function FeedbackAnalytics() {
  const [assessments, setAssessments] = useState([]);
  const [legacyFeedback, setLegacyFeedback] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    Promise.allSettled([
      transactionService.getAssessments({ limit: 500 }),
      fetchFeedback(),
    ]).then(([assessmentResult, feedbackResult]) => {
      if (!active) return;
      if (assessmentResult.status === "fulfilled") {
        setAssessments(assessmentResult.value.items ?? []);
      } else {
        setError(
          assessmentResult.reason.response?.data?.detail ||
            "Unable to load human review decisions."
        );
      }
      if (feedbackResult.status === "fulfilled") {
        setLegacyFeedback(feedbackResult.value);
      }
      setLoading(false);
    });
    return () => {
      active = false;
    };
  }, []);

  const decisionData = useMemo(
    () =>
      ["AGREE", "DISAGREE", "PENDING"].map((decision) => ({
        name: decision,
        count:
          decision === "PENDING"
            ? assessments.filter(
                (item) => item.review_required && !item.review_decision
              ).length
            : assessments.filter(
                (item) => item.review_decision === decision
              ).length,
      })),
    [assessments]
  );
  const reviewed = assessments.filter((item) => item.review_decision);
  const disagreementRate = reviewed.length
    ? Math.round(
        (reviewed.filter((item) => item.review_decision === "DISAGREE")
          .length /
          reviewed.length) *
          100
      )
    : 0;

  return (
    <div className="app-layout">
      <Sidebar />
      <div className="main-area">
        <Navbar />
        <main className="page-content feedback-page">
          <div className="dashboard-hero analytics-hero">
            <div className="dashboard-hero-copy">
              <span className="dashboard-eyebrow">
                <span className="dashboard-eyebrow-dot" />
                HUMAN-IN-THE-LOOP SIGNALS
              </span>
              <h1>Feedback analysis</h1>
              <p>
                See how human decisions add context to risk assessments and
                shape review quality.
              </p>
            </div>
            <span className="analytics-hero-badge">DECISION INSIGHTS</span>
          </div>

          {error && (
            <div className="dashboard-info" role="alert">
              {error}
            </div>
          )}

          <section className="stats-grid insight-stat-grid feedback-stat-grid">
            {[
              ["Assessments reviewed", reviewed.length],
              ["Agreed with risk", decisionData[0].count],
              ["Disagreed", decisionData[1].count],
              ["Awaiting decision", decisionData[2].count],
              ["Disagreement rate", `${disagreementRate}%`],
              ["Legacy ML feedback", legacyFeedback.length],
            ].map(([title, value]) => (
              <div className="stat-card insight-stat-card" key={title}>
                <div className="stat-card-title">{title}</div>
                <div className="stat-card-value">
                  {loading ? "—" : value}
                </div>
                <div className="stat-card-subtitle">Saved backend records</div>
              </div>
            ))}
          </section>

          <section className="dashboard-grid insight-chart-grid">
            <div className="dashboard-card insight-chart-card">
              <div className="analytics-card-heading">
                <div>
                  <span className="dashboard-card-kicker">DECISION MIX</span>
                  <h2>Human decision distribution</h2>
                </div>
                <span className="dashboard-heading-icon" aria-hidden="true">◒</span>
              </div>
              {decisionData.some((item) => item.count > 0) ? (
                <DistributionDonut
                  counts={decisionData}
                  total={decisionData.reduce(
                    (sum, item) => sum + item.count,
                    0
                  )}
                  colors={COLORS}
                  centerLabel="reviews"
                  caption="Pending and completed reviews"
                />
              ) : (
                <p>
                  {loading
                    ? "Loading decisions..."
                    : "No human decisions have been recorded."}
                </p>
              )}
            </div>
            <div className="dashboard-card insight-chart-card">
              <div className="analytics-card-heading">
                <div>
                  <span className="dashboard-card-kicker">DECISION VOLUME</span>
                  <h2>Review outcomes</h2>
                </div>
                <span className="dashboard-heading-icon" aria-hidden="true">↗</span>
              </div>
              <div style={{ width: "100%", height: 300 }}>
                <ResponsiveContainer>
                  <BarChart data={decisionData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#2563eb" radius={[5, 5, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </section>

          <section className="dashboard-card analytics-table-card">
            <div className="analytics-card-heading">
              <div>
                <span className="dashboard-card-kicker">AUDIT TRAIL</span>
                <h2>Recent human decisions</h2>
              </div>
              <span className="analytics-hero-badge">{reviewed.length} DECISIONS</span>
            </div>
            <div className="transaction-table-container">
              <table className="transaction-table">
                <thead>
                  <tr>
                    <th>Reviewed</th>
                    <th>Reference / Recipient</th>
                    <th>Risk at assessment</th>
                    <th>Human decision</th>
                    <th>Comment</th>
                  </tr>
                </thead>
                <tbody>
                  {reviewed.slice(0, 100).map((item) => (
                    <tr key={item.assessment_id}>
                      <td>
                        {item.reviewed_at
                          ? new Date(item.reviewed_at).toLocaleString()
                          : "—"}
                      </td>
                      <td>{item.reference || item.merchant || "—"}</td>
                      <td>
                        {item.risk_level}
                      </td>
                      <td>
                        <span
                          className={`dashboard-review-badge ${
                            item.review_decision === "APPROVED"
                              ? "is-complete"
                              : "is-pending"
                          }`}
                        >
                          {item.review_decision}
                        </span>
                      </td>
                      <td>{item.review_comment || "—"}</td>
                    </tr>
                  ))}
                  {!loading && reviewed.length === 0 && (
                    <tr>
                      <td colSpan={5}>No completed human reviews yet.</td>
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

async function fetchFeedback() {
  const response = await api.get("/feedback");
  const data = response.data;
  return Array.isArray(data) ? data : data.items ?? [];
}

export default FeedbackAnalytics;
