import { getRiskBadgePresentation } from "../utils/riskBadgePresentation";

function RiskBadge({ level }) {
  const presentation = getRiskBadgePresentation(level);

  return (
    <span
      className={presentation.className}
      aria-label={presentation.ariaLabel}
    >
      {presentation.label}
    </span>
  );
}

export default RiskBadge;