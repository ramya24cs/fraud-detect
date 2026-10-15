import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

function ProbabilityChart({ data = [] }) {
  if (!data || data.length === 0) {
    return (
      <div className="chart-empty">
        <p>No probability data available.</p>
      </div>
    );
  }

  return (
    <div className="chart-container">
      <h3>Fraud Probability Distribution</h3>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />

          <XAxis
            dataKey="label"
            tick={{ fontSize: 12 }}
          />

          <YAxis
            domain={[0, 1]}
            tickFormatter={(value) =>
              `${(value * 100).toFixed(0)}%`
            }
          />

          <Tooltip
            formatter={(value) =>
              `${(Number(value) * 100).toFixed(2)}%`
            }
          />

          <Bar
            dataKey="probability"
            name="Fraud Probability"
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export default ProbabilityChart;