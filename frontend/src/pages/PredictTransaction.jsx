import { useState } from "react";
import transactionService from "../services/transactionService";
import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import TransactionAdviceChatbot from "../components/TransactionAdviceChatbot";
import {
  isTransactionPdf,
  parseTransactionCsv,
  parseTransactionPdf,
} from "../utils/transactionFileImport";

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
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [importRecords, setImportRecords] = useState([]);
  const [importResults, setImportResults] = useState([]);
  const [importBatchSummary, setImportBatchSummary] = useState(null);
  const [importFileName, setImportFileName] = useState("");
  const [importProgress, setImportProgress] = useState("");
  const [importLoading, setImportLoading] = useState(false);
  const [importSubmitting, setImportSubmitting] = useState(false);
  const [importError, setImportError] = useState("");

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

  const handleImportFile = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setImportError("");
    setImportRecords([]);
    setImportResults([]);
    setImportBatchSummary(null);
    setImportFileName(file.name);
    setImportProgress("");
    setImportLoading(true);

    try {
      if (file.size > 10 * 1024 * 1024) {
        throw new Error("Files must be 10 MB or smaller.");
      }

      const records = (await isTransactionPdf(file))
        ? await parseTransactionPdf(file, setImportProgress)
        : parseTransactionCsv(await file.text());

      if (records.length > 100) {
        throw new Error(
          "A file can contain at most 100 transactions per import."
        );
      }

      setImportRecords(records);
    } catch (err) {
      setImportError(err.message || "Could not read this file.");
      setImportFileName("");
    } finally {
      setImportLoading(false);
      setImportProgress("");
    }
  };

  const updateImportedRecord = (id, field, value) => {
    setImportRecords((records) =>
      records.map((record) =>
        record.id === id ? { ...record, [field]: value } : record
      )
    );
  };

  const importedRecordIsValid = (record) =>
    Number.isFinite(Number(record.amount)) &&
    Number(record.amount) > 0 &&
    Boolean(record.occurredAt) &&
    !Number.isNaN(new Date(record.occurredAt).getTime()) &&
    /^[A-Za-z]{3}$/.test(record.currency);

  const submitImportedTransactions = async () => {
    setImportSubmitting(true);
    setImportError("");
    setImportResults([]);
    setImportBatchSummary(null);
    try {
      const result = await transactionService.analyzeTransactionBatch({
        transactions: importRecords.map((record) => ({
          amount: Number(record.amount),
          currency: record.currency.toUpperCase(),
          occurred_at: new Date(record.occurredAt).toISOString(),
          transaction_type: record.type,
          merchant: record.merchant || null,
          channel: record.channel,
          reference: record.reference || null,
          location: record.location || null,
          remarks: record.remarks || null,
        })),
      });
      setImportResults(
        result.assessments.map((assessment, index) => ({
          id: importRecords[index].id,
          sourceRow: importRecords[index].sourceRow,
          amount: assessment.amount,
          currency: assessment.currency,
          riskLevel: assessment.risk_level,
        }))
      );
      setImportBatchSummary(result);
      setImportRecords([]);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setImportError(
        typeof detail === "string"
          ? detail
          : detail
            ? JSON.stringify(detail)
            : err.message || "Unable to assess this transaction batch."
      );
    } finally {
      setImportSubmitting(false);
    }
  };

  const selectedRiskColor = riskColor(assessment?.risk_level);

  return (
    <div className="app-layout">
      <Sidebar />
      <div className="main-area">
        <Navbar />
        <main className="page-content predict-page">
          <div className="page-header predict-page-header">
            <div>
              <span className="predict-page-eyebrow">
                TRANSACTION REVIEW WORKSPACE
              </span>
              <h1>Transaction Risk Assessment</h1>
              <p>
                Review a single transaction or assess a statement file.
              </p>
            </div>
            <span
              className={`data-status ${
                loading || importLoading || importSubmitting
                  ? "is-working"
                  : ""
              }`}
            >
              {loading || importSubmitting
                ? "ANALYZING"
                : importLoading
                  ? "READING FILE"
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

          <section className="dashboard-card predict-upload-card">
            <div className="predict-section-heading">
              <span className="predict-section-icon" aria-hidden="true">
                01
              </span>
              <div>
                <h2>Assess a transaction file</h2>
                <p>
                  Import a bank statement from different providers and assess
                  its transactions.
                </p>
              </div>
            </div>
            <label className="predict-upload-dropzone">
              <span className="predict-upload-symbol" aria-hidden="true">↑</span>
              <span className="predict-upload-title">
                {importLoading
                  ? "Reading your file..."
                  : "Choose a file to upload"}
              </span>
              <span className="predict-upload-hint">
                CSV or PDF, including scanned statements · Maximum 10 MB · Up
                to 100 transactions
              </span>
              <span className="predict-upload-button">Browse files</span>
              <input
                className="predict-file-input"
                type="file"
                accept=".csv,text/csv,.pdf,application/pdf"
                onChange={handleImportFile}
                disabled={loading || importLoading || importSubmitting}
              />
            </label>
            {importFileName && (
              <div className="predict-selected-file">
                <span className="predict-file-mark" aria-hidden="true">
                  FILE
                </span>
                <span className="predict-selected-file-name">
                  {importFileName}
                </span>
                {importRecords.length > 0 && (
                  <span className="predict-file-count">
                    {importRecords.length} rows ready
                  </span>
                )}
              </div>
            )}
            {importLoading && (
              <p className="predict-inline-status" role="status">
                {importProgress || "Extracting transactions from your file..."}
              </p>
            )}
            {importError && (
              <p className="predict-error-message" role="alert">
                {importError}
              </p>
            )}

            {importRecords.length > 0 && (
              <div className="predict-preview">
                <div className="predict-preview-heading">
                  <div>
                    <h3>Review extracted transactions</h3>
                    <p>
                      Check the date, amount and currency before assessment.
                    </p>
                  </div>
                  <span className="predict-row-count">
                    {importRecords.length}{" "}
                    {importRecords.length === 1 ? "transaction" : "transactions"}
                  </span>
                </div>
                <p className="predict-date-hint">
                  Dates without a time use midnight. Slash-separated dates are
                  read as day/month/year.
                </p>
                <div className="table-container predict-preview-table">
                  <table>
                    <thead>
                      <tr>
                        <th>Row</th>
                        <th>Date and time</th>
                        <th>Amount</th>
                        <th>Currency</th>
                        <th>Merchant / description</th>
                        <th>Check</th>
                      </tr>
                    </thead>
                    <tbody>
                      {importRecords.map((record) => {
                        const valid = importedRecordIsValid(record);
                        return (
                          <tr key={record.id}>
                            <td>{record.sourceRow}</td>
                            <td>
                              <input
                                aria-label={`Date for row ${record.sourceRow}`}
                                type="datetime-local"
                                value={record.occurredAt}
                                onChange={(event) =>
                                  updateImportedRecord(
                                    record.id,
                                    "occurredAt",
                                    event.target.value
                                  )
                                }
                                style={inputStyle}
                              />
                            </td>
                            <td>
                              <input
                                aria-label={`Amount for row ${record.sourceRow}`}
                                type="number"
                                min="0.01"
                                step="0.01"
                                value={record.amount}
                                onChange={(event) =>
                                  updateImportedRecord(
                                    record.id,
                                    "amount",
                                    event.target.value
                                  )
                                }
                                style={inputStyle}
                              />
                            </td>
                            <td>
                              <input
                                aria-label={`Currency for row ${record.sourceRow}`}
                                type="text"
                                maxLength={3}
                                value={record.currency}
                                onChange={(event) =>
                                  updateImportedRecord(
                                    record.id,
                                    "currency",
                                    event.target.value
                                  )
                                }
                                style={inputStyle}
                              />
                            </td>
                            <td>
                              <input
                                aria-label={`Description for row ${record.sourceRow}`}
                                type="text"
                                maxLength={150}
                                value={record.merchant}
                                onChange={(event) =>
                                  updateImportedRecord(
                                    record.id,
                                    "merchant",
                                    event.target.value
                                  )
                                }
                                style={inputStyle}
                              />
                              {record.remarks && (
                                <small>{record.remarks}</small>
                              )}
                            </td>
                            <td>
                              <span
                                className={`predict-validation ${
                                  valid ? "is-valid" : "is-invalid"
                                }`}
                              >
                                {valid ? "Ready" : "Needs correction"}
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
                <button
                  className="predict-primary-button"
                  type="button"
                  disabled={
                    loading ||
                    importSubmitting ||
                    importRecords.some(
                      (record) => !importedRecordIsValid(record)
                    )
                  }
                  onClick={submitImportedTransactions}
                >
                  {importSubmitting
                    ? "Assessing transactions..."
                    : `Assess ${importRecords.length} transaction${
                        importRecords.length === 1 ? "" : "s"
                      }`}
                </button>
              </div>
            )}

            {importResults.length > 0 && (
              <div className="predict-batch-results" role="status">
                <div className="predict-results-heading">
                  <div>
                    <span className="predict-results-eyebrow">
                      FILE ASSESSMENT COMPLETE
                    </span>
                    <h3>Results</h3>
                    <p>
                      {importResults.filter((result) => !result.error).length}{" "}
                      of {importResults.length} transactions assessed.
                    </p>
                  </div>
                  {importBatchSummary && (
                    <span
                      className={`predict-risk-pill risk-${importBatchSummary.overall_risk_level.toLowerCase()}`}
                    >
                      Overall {importBatchSummary.overall_risk_level}
                    </span>
                  )}
                </div>
                {importBatchSummary && (
                  <div
                    className={`predict-email-summary ${
                      importBatchSummary.review_notification_status === "SENT"
                        ? "is-sent"
                        : "is-neutral"
                    }`}
                  >
                    <strong>
                      {importBatchSummary.review_notification_status === "SENT"
                        ? "One amount-threshold alert email sent"
                        : importBatchSummary.review_notification_status ===
                            "NOT_REQUIRED"
                          ? "No amounts above 50,000"
                          : `Batch email ${importBatchSummary.review_notification_status.toLowerCase()}`}
                    </strong>
                    {importBatchSummary.review_notification_message && (
                      <span>{importBatchSummary.review_notification_message}</span>
                    )}
                  </div>
                )}
                <ul className="predict-result-list">
                  {importResults.map((result) => (
                    <li className="predict-result-row" key={result.id}>
                      <span className="predict-result-row-number">
                        Row {result.sourceRow}
                      </span>
                      {result.error ? (
                        <span className="predict-error-message">
                          {result.error}
                        </span>
                      ) : (
                        <>
                          <span
                            className={`predict-risk-pill risk-${result.riskLevel.toLowerCase()}`}
                          >
                            {result.riskLevel}
                          </span>
                          <span className="predict-result-amount">
                            {result.currency}{" "}
                            {Number(result.amount).toLocaleString()}
                          </span>
                        </>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </section>

          <section className="dashboard-card predict-manual-card">
            <div className="predict-section-heading">
              <span className="predict-section-icon" aria-hidden="true">
                02
              </span>
              <div>
                <h2>Assess one transaction</h2>
                <p>Enter the transaction details below for an individual assessment.</p>
              </div>
            </div>

            <form className="predict-manual-form" onSubmit={handleSubmit}>
              <div className="dashboard-grid predict-form-grid">
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
                className="predict-primary-button"
                type="submit"
                disabled={loading || importLoading || importSubmitting}
              >
                {loading ? "Analyzing..." : "Analyze transaction"}
              </button>
            </form>
          </section>

          {assessment && (
            <section
              className="dashboard-card predict-single-result"
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
                  <div className="stat-card-title">Human review</div>
                  <div className="stat-card-value">
                    {assessment.review_required ? "Required" : "Not required"}
                  </div>
                </div>
              </div>
            </section>
          )}

          {assessment?.review_required && (
            <section
              className="dashboard-card"
              aria-label="Transaction email notification"
              style={{ marginTop: 20 }}
            >
              <h2>Email notification</h2>
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
