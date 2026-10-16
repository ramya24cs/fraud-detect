import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { getCurrentAccount } from "../services/authService";

function Navbar() {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const [accountEmail, setAccountEmail] = useState("Loading account...");

  useEffect(() => {
    let active = true;

    getCurrentAccount()
      .then((account) => {
        if (active) setAccountEmail(account.email);
      })
      .catch(() => {
        if (active) setAccountEmail("Account unavailable");
      });

    return () => {
      active = false;
    };
  }, []);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <header className="navbar">
      <div className="navbar-brand">
        <h2>Fraud Detection System</h2>
      </div>

      <div className="navbar-actions">
        <span className="operator-label">
          {accountEmail}
        </span>

        <button
          type="button"
          onClick={handleLogout}
        >
          Logout
        </button>
      </div>
    </header>
  );
}

export default Navbar;