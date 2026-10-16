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
import transactionService from "../services/transactionService";

const COLORS = { LOW: "#16a34a", MEDIUM: "#f59e0b", HIGH: "#dc2626" };

function RiskAnalytics() {
  const [assessments, setAssessments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    transactionService
      .getAssessments({ limit: 500 })
      .then((response) => {
        if (active) setAssessments(response.items ?? []);
      })
      .catch((requestError) => {
        if (active) {
          setError(
            requestError.response?.data?.detail ||
              "Unable to load transaction risk assessments."
          );
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const riskData = useMemo(
    () =>
      ["LOW", "MEDIUM", "HIGH"].map((risk) => ({
        name: risk,
        count: assessments.filter((item) => item.risk_level === risk).length,
      })),
    [assessments]
  );
  const decisionData = useMemo(
    () => [
      {
        name: "Pending",
        count: assessments.filter(
          (item) => item.review_required && !item.review_decision
        ).length,
      },
      {
        name: "Agree",
        count: assessments.filter((item) => item.review_decision === "AGREE")
          .length,
      },
      {
        name: "Disagree",
        count: assessments.filter(
          (item) => item.review_decision === "DISAGREE"
        ).length,
      },
    ],
    [assessments]
  );

  return (
    <div className="app-layout">
      <Sidebar />
      <div className="main-area">
        <Navbar />
        <main className="page-content risk-analytics-page">
          <div className="dashboard-hero analytics-hero">
            <div className="dashboard-hero-copy">
              <span className="dashboard-eyebrow">
                <span className="dashboard-eyebrow-dot" />
                ACCOUNT RISK INTELLIGENCE
              </span>
              <h1>Risk analytics</h1>
              <p>
                Explore risk patterns and review outcomes across your saved
                assessments.
              </p>
            </div>
            <span className="analytics-hero-badge">RISK PROFILE</span>
          </div>

          {error && (
            <div className="dashboard-info" role="alert">
              {error}
            </div>
          )}

          <section className="stats-grid insight-stat-grid">
            {riskData.map((item) => (
              <div className={`stat-card insight-stat-card tone-${item.name.toLowerCase()}`} key={item.name}>
                <div className="stat-card-title">{item.name} risk</div>
                <div className="stat-card-value">
                  {loading ? "—" : item.count}
                </div>
                <div className="stat-card-subtitle">Saved assessments</div>
              </div>
            ))}
            <div className="stat-card insight-stat-card tone-decisions">
              <div className="stat-card-title">Reviewed by a human</div>
              <div className="stat-card-value">
                {loading
                  ? "—"
                  : assessments.filter((item) => item.review_decision).length}
              </div>
              <div className="stat-card-subtitle">Agree or disagree recorded</div>
            </div>
          </section>

          <section className="dashboard-grid insight-chart-grid">
            <div className="dashboard-card insight-chart-card">
              <div className="analytics-card-heading">
                <div>
                  <span className="dashboard-card-kicker">RISK MIX</span>
                  <h2>Assessment risk levels</h2>
                </div>
                <span className="dashboard-heading-icon" aria-hidden="true">◒</span>
              </div>
              {assessments.length ? (
                <DistributionDonut
                  counts={riskData}
                  total={assessments.length}
                  colors={COLORS}
                  caption="Share of saved assessments"
                />
              ) : (
                <p>
                  {loading ? "Loading..." : "No assessments available yet."}
                </p>
              )}
            </div>
            <div className="dashboard-card insight-chart-card">
              <div className="analytics-card-heading">
                <div>
                  <span className="dashboard-card-kicker">REVIEW OUTCOMES</span>
                  <h2>Human review status</h2>
                </div>
                <span className="dashboard-heading-icon" aria-hidden="true">↗</span>
              </div>
              <div className="risk-review-chart">
                <div className="risk-review-summary" aria-label="Review totals">
                  {decisionData.map(({ name, count }) => (
                    <div className="risk-review-stat" key={name}>
                      <span>{name}</span>
                      <strong>{count}</strong>
                    </div>
                  ))}
                </div>
                <div style={{ width: "100%", height: 240 }}>
                  <ResponsiveContainer>
                    <BarChart data={decisionData}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="name" tickLine={false} axisLine={false} />
                      <YAxis allowDecimals={false} />
                      <Tooltip />
                      <Bar
                        dataKey="count"
                        fill="#2563eb"
                        radius={[7, 7, 0, 0]}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </section>

          <section className="dashboard-card analytics-table-card">
            <div className="analytics-card-heading">
              <div>
                <span className="dashboard-card-kicker">TRANSACTION HISTORY</span>
                <h2>Assessment detail</h2>
              </div>
              <span className="analytics-hero-badge">{assessments.length} RECORDS</span>
            </div>
            <div className="transaction-table-container">
              <table className="transaction-table">
                <thead>
                  <tr>
                    <th>Created</th>
                    <th>Reference / Recipient</th>
                    <th>Amount</th>
                    <th>Risk</th>
                    <th>Human decision</th>
                  </tr>
                </thead>
                <tbody>
                  {assessments.map((item) => (
                    <tr key={item.assessment_id}>
                      <td>{new Date(item.created_at).toLocaleString()}</td>
                      <td>{item.reference || item.merchant || "—"}</td>
                      <td>
                        {item.currency} {Number(item.amount).toFixed(2)}
                      </td>
                      <td>
                        <span
                          className={`dashboard-risk-badge risk-${String(item.risk_level).toLowerCase()}`}
                        >
                          <span />
                          {String(item.risk_level).replaceAll("_", " ")}
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
                  {!loading && assessments.length === 0 && (
                    <tr>
                      <td colSpan={5}>No transaction assessments yet.</td>
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

export default RiskAnalytics;
