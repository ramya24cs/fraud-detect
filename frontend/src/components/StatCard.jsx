function StatCard({ title, value, subtitle }) {
  return (
    <div className="stat-card">
      <div className="stat-card-title">{title}</div>

      <div className="stat-card-value">
        {value}
      </div>

      {subtitle && (
        <div className="stat-card-subtitle">
          {subtitle}
        </div>
      )}
    </div>
  );
}

export default StatCard;