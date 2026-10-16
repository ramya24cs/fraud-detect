import { useEffect, useMemo, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import StatCard from "../components/StatCard";
import api from "../services/api";

const MODEL_VERSION_FALLBACK = "xgb-cost-v1";

const SAVED_TEST_RESULTS = {
  model: "XGBoost",
  dataset: "ULB Credit Card Fraud Detection",
  split: "test",
  threshold: 0.5,
  precision: 0.8125,
  recall: 0.75,
  f1_score: 0.78,
  roc_auc: 0.9782647102832718,
  pr_auc: 0.7689240183986886,
  tn: 42660,
  fp: 9,
  fn: 13,
  tp: 39,
  fp_cost: 5,
  fn_cost: 100,
  expected_cost: 1345,
};

const SAVED_COST_SCENARIOS = [
  {
    scenario: "Baseline reference",
    reviewCost: 2,
    missedFraudCost: 100,
    approveThreshold: 0.02,
    blockThreshold: 0.98,
    expectedCost: 1728,
    approve: 42601,
    review: 79,
    block: 38,
    reviewRate: 0.18493375158013016,
  },
  {
    scenario: "Higher fraud loss",
    reviewCost: 2,
    missedFraudCost: 200,
    approveThreshold: 0.02,
    blockThreshold: 0.98,
    expectedCost: 2428,
    approve: 42601,
    review: 79,
    block: 38,
    reviewRate: 0.18493375158013016,
  },
  {
    scenario: "High review cost",
    reviewCost: 10,
    missedFraudCost: 100,
    approveThreshold: 0.07,
    blockThreshold: 0.08,
    expectedCost: 1960,
    approve: 42651,
    review: 5,
    block: 62,
    reviewRate: 0.011704667821527225,
  },
];

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? String(value)
    : date.toLocaleString("en-IN");
}

function formatNumber(value) {
  if (value === undefined || value === null || value === "") return "—";
  const number = Number(value);
  return Number.isFinite(number) ? number.toLocaleString("en-IN") : "—";
}

function formatDecimal(value, digits = 4) {
  if (value === undefined || value === null || value === "") return "—";
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(digits) : "—";
}

function formatPercent(value) {
  if (value === undefined || value === null || value === "") return "—";
  const number = Number(value);
  return Number.isFinite(number) ? `${(number * 100).toFixed(2)}%` : "—";
}

function getModelObject(response) {
  const data = response?.data;
  if (Array.isArray(data)) return data[0] ?? {};
  return data?.item ?? data?.model ?? data?.data ?? data ?? {};
}

function getModelList(response) {
  const data = response?.data;
  if (Array.isArray(data)) return data;

  const items = data?.items ?? data?.models ?? data?.results ?? data?.data;
  return Array.isArray(items) ? items : [];
}

function ModelMonitoring() {
  const [model, setModel] = useState(null);
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [currentError, setCurrentError] = useState("");
  const [historyError, setHistoryError] = useState("");
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    let active = true;
    let hasLoadedOnce = false;
    let requestInProgress = false;

    async function loadModels() {
      if (requestInProgress) return;
      requestInProgress = true;

      if (active) {
        if (!hasLoadedOnce) setLoading(true);
        else setRefreshing(true);
        setCurrentError("");
        setHistoryError("");
      }

      const [currentResult, historyResult] = await Promise.allSettled([
        api.get("/models/current"),
        api.get("/models"),
      ]);

      if (!active) {
        requestInProgress = false;
        return;
      }

      if (currentResult.status === "fulfilled") {
        const current = getModelObject(currentResult.value);
        setModel(Object.keys(current).length > 0 ? current : null);
      } else {
        // Keep the last successful model data visible if a refresh fails.
        setCurrentError(
          currentResult.reason?.response?.data?.detail ??
            currentResult.reason?.message ??
            "Unable to load the current model."
        );
      }

      if (historyResult.status === "fulfilled") {
        setModels(getModelList(historyResult.value));
      } else {
        setHistoryError(
          historyResult.reason?.response?.status === 403
            ? "Your account does not have permission to view model history."
            : historyResult.reason?.response?.data?.detail ??
                historyResult.reason?.message ??
                "Unable to load model history."
        );
      }

      if (
        currentResult.status === "fulfilled" ||
        historyResult.status === "fulfilled"
      ) {
        setLastUpdated(new Date());
      }

      setLoading(false);
      setRefreshing(false);
      hasLoadedOnce = true;
      requestInProgress = false;
    }

    loadModels();
    const intervalId = setInterval(loadModels, 30000);

    return () => {
      active = false;
      clearInterval(intervalId);
    };
  }, []);

  const version = model?.version ?? model?.model_version ?? MODEL_VERSION_FALLBACK;
  const artifactPath =
    model?.artifact_path ?? "ml/models/xgboost_baseline.joblib";
  const trainedAt =
    model?.trained_at ??
    model?.updated_at ??
    model?.created_at ??
    model?.registered_at;

  const activeStatus =
    typeof model?.active === "boolean"
      ? model.active
        ? "Active"
        : "Inactive"
      : model?.status ?? model?.deployment_status ?? "Not reported";

  const algorithm =
    model?.algorithm ?? model?.model_type ?? model?.model_name ?? "XGBoost";

  // Metrics are sourced from the active model registry API.
  // Do not substitute saved test metrics when API values are missing.
  const metrics = model?.metrics_json ?? {};

  const precision = metrics.precision;
  const recall = metrics.recall;
  const f1Score = metrics.f1_score ?? metrics.f1;
  const rocAuc = metrics.roc_auc ?? metrics.roc_auc_score;
  const prAuc = metrics.pr_auc ?? metrics.average_precision;
  const apiExpectedCost = metrics.expected_cost ?? metrics.test_expected_cost;
  const hasApiExpectedCost = apiExpectedCost !== undefined && apiExpectedCost !== null;
  const expectedCost =
    apiExpectedCost ??
    (version === MODEL_VERSION_FALLBACK
      ? SAVED_TEST_RESULTS.expected_cost
      : undefined);

  const confusionMatrix = useMemo(
    () => [
      {
        name: "Actual legitimate",
        correct: SAVED_TEST_RESULTS.tn,
        incorrect: SAVED_TEST_RESULTS.fp,
      },
      {
        name: "Actual fraud",
        correct: SAVED_TEST_RESULTS.tp,
        incorrect: SAVED_TEST_RESULTS.fn,
      },
    ],
    []
  );

  return (
    <div className="app-layout">
      <Sidebar />

      <div className="main-area">
        <Navbar />

        <main className="page-content model-monitoring-page">
          <div className="dashboard-hero analytics-hero model-monitoring-hero">
            <div className="dashboard-hero-copy">
              <span className="dashboard-eyebrow">
                <span className="dashboard-eyebrow-dot" />
                MODEL OPERATIONS
              </span>
              <h1>Model monitoring</h1>
              <p className="monitoring-last-updated">
                {lastUpdated
                  ? `Last API update: ${formatDate(lastUpdated)}`
                  : "Waiting for the first API response..."}
                {refreshing ? " · Refreshing..." : ""}
              </p>
            </div>
            <span className="model-status-pill">
              <span />
              {String(activeStatus).toUpperCase()}
            </span>
          </div>

          {currentError && (
            <div className="dashboard-info" role="alert">
              <p>
                Could not refresh registered model information:{" "}
                {String(currentError)}
              </p>
            </div>
          )}

          {loading && !model && (
            <div className="dashboard-info" role="status">
              <p>Loading model information from the backend API...</p>
            </div>
          )}

          <section className="stats-grid model-monitoring-stats">
            <StatCard
              title="Model Version"
              value={version}
              subtitle={model ? "From registered model API" : "No API model loaded"}
            />

            <StatCard
              title="Algorithm"
              value={algorithm}
              subtitle={model ? "Registered model metadata" : "No API model loaded"}
            />

            <StatCard
              title="Precision"
              value={formatPercent(precision)}
              subtitle="From registered model API"
            />

            <StatCard
              title="Recall"
              value={formatPercent(recall)}
              subtitle="From registered model API"
            />

            <StatCard
              title="F1 Score"
              value={formatDecimal(f1Score, 2)}
              subtitle="From registered model API"
            />

            <StatCard
              title="ROC-AUC"
              value={formatDecimal(rocAuc)}
              subtitle="From registered model API"
            />

            <StatCard
              title="PR-AUC"
              value={formatDecimal(prAuc)}
              subtitle="From registered model API"
            />

            <StatCard
              title="Expected Cost"
              value={formatNumber(expectedCost)}
              subtitle={
                hasApiExpectedCost
                  ? "From registered model API"
                  : version === MODEL_VERSION_FALLBACK
                    ? "Saved test result (9 false positives × 5 + 13 false negatives × 100)"
                    : "Not supplied by the API"
              }
            />
          </section>

          <section className="dashboard-card model-info-card">
            <div className="analytics-card-heading">
              <div>
                <span className="dashboard-card-kicker">ACTIVE REGISTRATION</span>
                <h2>Model information</h2>
              </div>
              <span className="dashboard-heading-icon" aria-hidden="true">◈</span>
            </div>
            <p>
              This section displays the active model information returned by
              the backend. Registration status and training timestamp appear
              only when supplied by the API.
            </p>

            <div className="model-info-list">
              <p>
                <strong>Model version:</strong> {version}
              </p>
              <p>
                <strong>Algorithm:</strong> {algorithm}
              </p>
              <p>
                <strong>Artifact path:</strong> {artifactPath}
              </p>
              <p>
                <strong>Local artifact reference:</strong>{" "}
                ml/models/xgboost_baseline.joblib
              </p>
              <p>
                <strong>Preprocessor reference:</strong>{" "}
                ml/models/preprocessor.joblib
              </p>
              <p>
                <strong>Registered model status:</strong> {activeStatus}
              </p>
              <p>
                <strong>Training date:</strong> {formatDate(trainedAt)}
              </p>
              <p>
                <strong>Last successful API update:</strong>{" "}
                {formatDate(lastUpdated)}
              </p>
            </div>
          </section>

          <section className="dashboard-card model-chart-card">
            <div className="analytics-card-heading">
              <div>
                <span className="dashboard-card-kicker">OFFLINE EVALUATION</span>
                <h2>Saved test confusion matrix</h2>
              </div>
              <span className="analytics-hero-badge">REFERENCE METRICS</span>
            </div>

            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Actual class</th>
                    <th>Correct prediction</th>
                    <th>Incorrect prediction</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Legitimate</td>
                    <td>{formatNumber(SAVED_TEST_RESULTS.tn)} true negatives</td>
                    <td>{formatNumber(SAVED_TEST_RESULTS.fp)} false positives</td>
                  </tr>
                  <tr>
                    <td>Fraud</td>
                    <td>{formatNumber(SAVED_TEST_RESULTS.tp)} true positives</td>
                    <td>{formatNumber(SAVED_TEST_RESULTS.fn)} false negatives</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div style={{ width: "100%", height: 300, marginTop: 24 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={confusionMatrix}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar
                    dataKey="correct"
                    name="Correct predictions"
                    fill="#16a34a"
                  />
                  <Bar
                    dataKey="incorrect"
                    name="Incorrect predictions"
                    fill="#dc2626"
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>

          </section>

          <section className="dashboard-card model-chart-card">
            <div className="analytics-card-heading">
              <div>
                <span className="dashboard-card-kicker">DECISION ECONOMICS</span>
                <h2>Cost-sensitive policy scenarios</h2>
              </div>
              <span className="dashboard-heading-icon" aria-hidden="true">↗</span>
            </div>

            <div style={{ width: "100%", height: 320 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={SAVED_COST_SCENARIOS}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="scenario"
                    interval={0}
                    tick={{ fontSize: 12 }}
                  />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar
                    dataKey="expectedCost"
                    name="Expected cost"
                    fill="#2563eb"
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Scenario</th>
                    <th>Expected cost</th>
                    <th>Approve</th>
                    <th>Review</th>
                    <th>Block</th>
                    <th>Review rate</th>
                    <th>Approve threshold</th>
                    <th>Block threshold</th>
                  </tr>
                </thead>
                <tbody>
                  {SAVED_COST_SCENARIOS.map((scenario) => (
                    <tr key={scenario.scenario}>
                      <td>{scenario.scenario}</td>
                      <td>{formatNumber(scenario.expectedCost)}</td>
                      <td>{formatNumber(scenario.approve)}</td>
                      <td>{formatNumber(scenario.review)}</td>
                      <td>{formatNumber(scenario.block)}</td>
                      <td>{`${(scenario.reviewRate * 100).toFixed(4)}%`}</td>
                      <td>{scenario.approveThreshold}</td>
                      <td>{scenario.blockThreshold}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

          </section>

          <section className="dashboard-card model-chart-card">
            <div className="analytics-card-heading">
              <div>
                <span className="dashboard-card-kicker">POLICY COMPARISON</span>
                <h2>Decision distribution by scenario</h2>
              </div>
              <span className="dashboard-heading-icon" aria-hidden="true">▥</span>
            </div>

            <div style={{ width: "100%", height: 320 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={SAVED_COST_SCENARIOS}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="scenario"
                    interval={0}
                    tick={{ fontSize: 12 }}
                  />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="approve" name="Approve" fill="#16a34a" />
                  <Bar dataKey="review" name="Review" fill="#d97706" />
                  <Bar dataKey="block" name="Block" fill="#dc2626" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </section>

          <section className="dashboard-card model-history-card">
            <div className="analytics-card-heading">
              <div>
                <span className="dashboard-card-kicker">REGISTRY</span>
                <h2>Model version history</h2>
              </div>
              <span className="dashboard-heading-icon" aria-hidden="true">↻</span>
            </div>

            {loading ? (
              <p>Loading registered model information...</p>
            ) : (
              <>
                {historyError && (
                  <div className="dashboard-info" role="status">
                    <p>{historyError}</p>
                  </div>
                )}

                {models.length > 0 ? (
                  <div className="table-container">
                    <table>
                      <thead>
                        <tr>
                          <th>Version</th>
                          <th>Model ID</th>
                          <th>Status</th>
                          <th>Artifact Path</th>
                          <th>Trained At</th>
                        </tr>
                      </thead>
                      <tbody>
                        {models.map((item, index) => (
                          <tr
                            key={
                              item.id ??
                              item.model_id ??
                              item.version ??
                              index
                            }
                          >
                            <td>
                              {item.version ?? item.model_version ?? "—"}
                            </td>
                            <td>{item.id ?? item.model_id ?? "—"}</td>
                            <td>
                              {typeof item.active === "boolean"
                                ? item.active
                                  ? "Active"
                                  : "Inactive"
                                : item.status ?? "—"}
                            </td>
                            <td>{item.artifact_path ?? "—"}</td>
                            <td>
                              {formatDate(
                                item.trained_at ??
                                  item.updated_at ??
                                  item.created_at
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  !historyError && (
                    <p>No model history records were returned by the backend.</p>
                  )
                )}
              </>
            )}

          </section>
        </main>
      </div>
    </div>
  );
}

export default ModelMonitoring;
