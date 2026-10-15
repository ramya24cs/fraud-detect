import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

import { formatCurrency } from "../utils/formatters";

function CostChart({ data = [] }) {
  if (!data || data.length === 0) {
    return (
      <div className="chart-empty">
        <p>No cost data available.</p>
      </div>
    );
  }

  return (
    <div className="chart-container">
      <h3>Cost Analysis</h3>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />

          <XAxis
            dataKey="label"
            tick={{ fontSize: 12 }}
          />

          <YAxis
            tickFormatter={(value) =>
              formatCurrency(value)
            }
          />

          <Tooltip
            formatter={(value) =>
              formatCurrency(value)
            }
          />

          <Bar
            dataKey="cost"
            name="Expected Cost"
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export default CostChart;