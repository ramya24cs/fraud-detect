function DistributionDonut({
  counts,
  total,
  colors,
  centerLabel = "assessed",
  caption = "Share of all assessments",
}) {
  const shares = counts.map((item) =>
    total ? (item.count / total) * 100 : 0
  );
  const segments = counts
    .map(({ name }, index) => {
      const start = shares
        .slice(0, index)
        .reduce((sum, share) => sum + share, 0);
      return `${colors[name]} ${start}% ${start + shares[index]}%`;
    })
    .join(", ");

  return (
    <div className="risk-overview">
      <div
        className="risk-donut-chart"
        style={{ background: `conic-gradient(${segments})` }}
        role="img"
        aria-label={counts
          .map(({ name, count }) => `${name}: ${count}`)
          .join(", ")}
      >
        <div className="risk-donut-center">
          <strong>{total}</strong>
          <span>{centerLabel}</span>
        </div>
      </div>
      <div className="risk-overview-legend">
        {counts.map(({ name, count }, index) => (
          <div className="risk-legend-row" key={name}>
            <span
              className="risk-legend-swatch"
              style={{ backgroundColor: colors[name] }}
            />
            <span className="risk-legend-name">{name}</span>
            <strong>{count}</strong>
            <span className="risk-legend-percent">
              {total ? `${Math.round(shares[index])}%` : "0%"}
            </span>
          </div>
        ))}
        <p className="risk-legend-caption">{caption}</p>
      </div>
    </div>
  );
}

export default DistributionDonut;
