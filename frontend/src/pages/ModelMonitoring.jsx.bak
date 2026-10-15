
import { useEffect, useState } from "react";
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

const MODEL_VERSION = "xgb-cost-v1";

const TEST_RESULTS = {
  model: "XGBoost",
  dataset: "ULB Credit Card Fraud Detection",
  split: "test",
  threshold: 0.5,
  precision: 0.8125,
  recall: 0.75,
  f1: 0.78,
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

const COST_SCENARIOS = [
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
  if (value === undefined || value === null || value === "") {
    return "—";
  }

  return Number(value).toLocaleString("en-IN");
}

function formatDecimal(value, digits = 4) {
  return Number(value).toFixed(digits);
}

function formatPercent(value) {
  return `${(Number(value) * 100).toFixed(2)}%`;
}

function getModelObject(response) {
  const data = response?.data;

  if (Array.isArray(data)) {
    return data[0] ?? {};
  }

  return data?.item ?? data?.model ?? data?.data ?? data ?? {};
}

function getModelList(response) {
  const data = response?.data;

  if (Array.isArray(data)) {
    return data;
  }

  const items =
    data?.items ??
    data?.models ??
    data?.results ??
    data?.data;

  return Array.isArray(items) ? items : [];
}

function ModelMonitoring() {
  const [model, setModel] = useState(null);
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentError, setCurrentError] = useState("");
  const [historyError, setHistoryError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadModels() {
      setLoading(true);
      setCurrentError("");
      setHistoryError("");

      const [currentResult, historyResult] =
        await Promise.allSettled([
          api.get("/models/current"),
          api.get("/models"),
        ]);

      if (!active) return;

      if (currentResult.status === "fulfilled") {
        const current = getModelObject(currentResult.value);

        setModel(
          Object.keys(current).length > 0 ? current : null
        );
      } else {
        setModel(null);

        const error = currentResult.reason;

        setCurrentError(
          error?.response?.data?.detail ??
            error?.message ??
            "Unable to load the current model."
        );
      }

      if (historyResult.status === "fulfilled") {
        setModels(getModelList(historyResult.value));
      } else {
        setModels([]);

        const error = historyResult.reason;

        setHistoryError(
          error?.response?.status === 403
            ? "Your account does not have permission to view model history. Ask your backend teammate to check the endpoint permissions."
            : error?.response?.data?.detail ??
                error?.message ??
                "Unable to load model history."
        );
      }

      setLoading(false);
    }

    loadModels();

    return () => {
      active = false;
    };
  }, []);

  const version =
    model?.version ??
    model?.model_version ??
    MODEL_VERSION;

  const artifactPath =
    model?.artifact_path ??
    "ml/models/xgboost_baseline.joblib";

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
      : model?.status ??
        model?.deployment_status ??
        "Not reported";

  const algorithm =
    model?.algorithm ??
    model?.model_type ??
    model?.model_name ??
    "XGBoost";

  const confusionMatrix = [
    {
      name: "Actual legitimate",
      correct: TEST_RESULTS.tn,
      incorrect: TEST_RESULTS.fp,
    },
    {
      name: "Actual fraud",
      correct: TEST_RESULTS.tp,
      incorrect: TEST_RESULTS.fn,
    },
  ];

  return (
    <div className="app-layout">
      <Sidebar />

      <div className="main-area">
        <Navbar />

        <main className="page-content">
          <div className="page-header">
            <div>
              <h1>Model Monitoring</h1>
              <p>
                Monitor the registered model, saved test
                performance, and cost-sensitive policy
                evaluation results.
              </p>
            </div>

            <span className="data-status">
              SAVED EVALUATION RESULTS
            </span>
          </div>

          {currentError && (
            <div className="dashboard-info" role="alert">
              <p>
                Could not load registered model information:{" "}
                {String(currentError)}
              </p>
            </div>
          )}

          <section className="stats-grid">
            <StatCard
              title="Model Version"
              value={MODEL_VERSION}
              subtitle="Version recorded in model metadata"
            />

            <StatCard
              title="Algorithm"
              value="XGBoost"
              subtitle="Trained model artifact"
            />

            <StatCard
              title="Precision"
              value={formatPercent(TEST_RESULTS.precision)}
              subtitle="Saved test result"
            />

            <StatCard
              title="Recall"
              value={formatPercent(TEST_RESULTS.recall)}
              subtitle="Saved test result"
            />

            <StatCard
              title="F1 Score"
              value={formatDecimal(TEST_RESULTS.f1, 2)}
              subtitle="Saved test result"
            />

            <StatCard
              title="ROC-AUC"
              value={formatDecimal(TEST_RESULTS.roc_auc)}
              subtitle="Saved test result"
            />

            <StatCard
              title="PR-AUC"
              value={formatDecimal(TEST_RESULTS.pr_auc)}
              subtitle="Saved test result"
            />

            <StatCard
              title="Test Expected Cost"
              value={formatNumber(TEST_RESULTS.expected_cost)}
              subtitle="Reported by final_test_results.csv"
            />
          </section>

          <section className="dashboard-card">
            <h2>Model Information</h2>

            <p>
              The following information identifies the model
              configured in this project. Registration status
              and training timestamp are shown only when
              supplied by the backend.
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
                <strong>Local artifact:</strong>{" "}
                ml/models/xgboost_baseline.joblib
              </p>

              <p>
                <strong>Preprocessor:</strong>{" "}
                ml/models/preprocessor.joblib
              </p>

              <p>
                <strong>Dataset:</strong>{" "}
                {TEST_RESULTS.dataset}
              </p>

              <p>
                <strong>Evaluation split:</strong>{" "}
                {TEST_RESULTS.split}
              </p>

              <p>
                <strong>Evaluation threshold:</strong>{" "}
                {TEST_RESULTS.threshold}
              </p>

              <p>
                <strong>Registered model status:</strong>{" "}
                {activeStatus}
              </p>

              <p>
                <strong>Training date:</strong>{" "}
                {formatDate(trainedAt)}
              </p>
            </div>
          </section>

          <section className="dashboard-card">
            <h2>Test Confusion Matrix</h2>

            <p>
              Actual test-set counts from
              ml/reports/final_test_results.csv.
            </p>

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
                    <td>{formatNumber(TEST_RESULTS.tn)} true negatives</td>
                    <td>{formatNumber(TEST_RESULTS.fp)} false positives</td>
                  </tr>

                  <tr>
                    <td>Fraud</td>
                    <td>{formatNumber(TEST_RESULTS.tp)} true positives</td>
                    <td>{formatNumber(TEST_RESULTS.fn)} false negatives</td>
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

            <p>
              These are offline test-set results at threshold
              0.5. They are not counts of live transactions.
            </p>
          </section>

          <section className="dashboard-card">
            <h2>Cost-Sensitive Policy Comparison</h2>

            <p>
              Compare the saved expected costs under the
              three scenarios in
              ml/reports/cost_sensitivity_results.csv.
            </p>

            <div style={{ width: "100%", height: 320 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={COST_SCENARIOS}>
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
                  {COST_SCENARIOS.map((scenario) => (
                    <tr key={scenario.scenario}>
                      <td>{scenario.scenario}</td>
                      <td>{formatNumber(scenario.expectedCost)}</td>
                      <td>{formatNumber(scenario.approve)}</td>
                      <td>{formatNumber(scenario.review)}</td>
                      <td>{formatNumber(scenario.block)}</td>
                      <td>
                        {`${(
                          scenario.reviewRate * 100
                        ).toFixed(4)}%`}
                      </td>
                      <td>{scenario.approveThreshold}</td>
                      <td>{scenario.blockThreshold}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <p>
              The baseline reference has the lowest reported
              expected cost among these three scenarios.
              These saved results do not by themselves prove
              that it is optimal for every deployment.
            </p>
          </section>

          <section className="dashboard-card">
            <h2>Decision Distribution by Scenario</h2>

            <p>
              Saved approve, review, and block counts for
              each cost-sensitive policy scenario.
            </p>

            <div style={{ width: "100%", height: 320 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={COST_SCENARIOS}>
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
                    dataKey="approve"
                    name="Approve"
                    fill="#16a34a"
                  />
                  <Bar
                    dataKey="review"
                    name="Review"
                    fill="#d97706"
                  />
                  <Bar
                    dataKey="block"
                    name="Block"
                    fill="#dc2626"
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </section>

          <section className="dashboard-card">
            <h2>Model Monitoring and Version History</h2>

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
                              {item.version ??
                                item.model_version ??
                                "—"}
                            </td>

                            <td>
                              {item.id ??
                                item.model_id ??
                                "—"}
                            </td>

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
                    <p>
                      No model history records were returned
                      by the backend.
                    </p>
                  )
                )}
              </>
            )}

            <p>
              The page reads registered model information
              from the backend. The test metrics and policy
              comparisons above are saved evaluation results.
              This page does not train, retrain, or activate
              models.
            </p>
          </section>
        </main>
      </div>
    </div>
  );
}

export default ModelMonitoring;
