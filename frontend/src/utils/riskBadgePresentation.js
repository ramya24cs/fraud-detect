const RISK_LEVELS = new Set(["LOW", "MEDIUM", "HIGH"]);

export function getRiskBadgePresentation(level) {
  const normalizedLevel = String(level ?? "").trim().toUpperCase();
  const riskLevel = RISK_LEVELS.has(normalizedLevel)
    ? normalizedLevel
    : "UNKNOWN";

  return {
    label: riskLevel,
    className: `risk-badge risk-${riskLevel.toLowerCase()}`,
    ariaLabel: `${riskLevel} risk`,
  };
}
