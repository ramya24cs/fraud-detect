
import { NavLink } from "react-router-dom";

function Sidebar() {
  const pages = [
    ["01", "/dashboard", "Dashboard"],
    ["02", "/predict-transaction", "Predict Transaction"],
    ["03", "/risk-analytics", "Risk Analytics"],
    ["04", "/review-queue", "Review Queue"],
    ["05", "/feedback-analytics", "Feedback Analytics"],
    ["06", "/model-monitoring", "Model Monitoring"],
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <span className="sidebar-brand-mark" aria-hidden="true">
          <svg viewBox="0 0 32 32" fill="none">
            <path
              d="M16 3.5 27 8v7.7c0 6.2-4.4 10.7-11 13.3C9.4 26.4 5 21.9 5 15.7V8l11-4.5Z"
              stroke="currentColor"
              strokeWidth="1.8"
            />
            <path
              d="m10.7 16.1 3.4 3.4 7.4-7.5"
              stroke="currentColor"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
            />
          </svg>
        </span>
        <span className="sidebar-title">
          Fraud<span>Detection</span>
        </span>
      </div>

      <nav className="sidebar-nav">
        <span className="sidebar-section-label">WORKSPACE</span>
        {pages.map(([number, path, title]) => (
          <NavLink
            key={path}
            to={path}
            className={({ isActive }) =>
              `sidebar-link${isActive ? " active" : ""}`
            }
          >
            <span className="sidebar-link-number" aria-hidden="true">
              {number}
            </span>
            <span>{title}</span>
            <span className="sidebar-link-arrow" aria-hidden="true">›</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <span className="sidebar-footer-indicator" />
        Risk intelligence workspace
      </div>
    </aside>
  );
}

export default Sidebar;
