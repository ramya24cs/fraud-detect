function DecisionBadge({ decision }) {
  const normalizedDecision = decision?.toUpperCase();

  return (
    <span
      className={`decision-badge decision-${normalizedDecision?.toLowerCase()}`}
    >
      {normalizedDecision || "UNKNOWN"}
    </span>
  );
}

export default DecisionBadge;