
import { NavLink } from "react-router-dom";

function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-title">
        Fraud Detection
      </div>

      <nav className="sidebar-nav">
        <NavLink
          to="/dashboard"
          className={({ isActive }) => isActive ? "active" : ""}
        >
          Dashboard
        </NavLink>

        <NavLink
          to="/predict-transaction"
          className={({ isActive }) => isActive ? "active" : ""}
        >
          Predict Transaction
        </NavLink>

        <NavLink
          to="/risk-analytics"
          className={({ isActive }) => isActive ? "active" : ""}
        >
          Risk Analytics
        </NavLink>

        <NavLink
          to="/review-queue"
          className={({ isActive }) => isActive ? "active" : ""}
        >
          Review Queue
        </NavLink>

        <NavLink
          to="/feedback-analytics"
          className={({ isActive }) => isActive ? "active" : ""}
        >
          Feedback Analytics
        </NavLink>

        <NavLink
          to="/model-monitoring"
          className={({ isActive }) => isActive ? "active" : ""}
        >
          Model Monitoring
        </NavLink>
      </nav>
    </aside>
  );
}

export default Sidebar;
