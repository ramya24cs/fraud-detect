import RiskBadge from "./RiskBadge";
import DecisionBadge from "./DecisionBadge";
import {
  formatCost,
  formatCurrency,
  formatPercentage,
} from "../utils/formatters";

function TransactionTable({ transactions = [], onSelect }) {
  if (transactions.length === 0) {
    return (
      <div className="transaction-table-empty">
        <p>No transactions available.</p>
      </div>
    );
  }

  return (
    <div className="transaction-table-container">
      <table className="transaction-table">
        <thead>
          <tr>
            <th>Transaction ID</th>
            <th>Amount</th>
            <th>Fraud Probability</th>
            <th>Risk Level</th>
            <th>Decision</th>
            <th>Expected Cost</th>
            <th>Action</th>
          </tr>
        </thead>

        <tbody>
          {transactions.map((transaction) => (
            <tr key={transaction.id}>
              <td>{transaction.id}</td>

              <td>
                {formatCurrency(transaction.amount)}
              </td>

              <td>
                {formatPercentage(transaction.fraud_probability)}
              </td>

              <td>
                <RiskBadge level={transaction.risk_level} />
              </td>

              <td>
                <DecisionBadge decision={transaction.decision} />
              </td>

              <td>
                {formatCost(transaction.expected_cost)}
              </td>

              <td>
                <button
                  type="button"
                  onClick={() => onSelect?.(transaction)}
                >
                  View
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default TransactionTable;