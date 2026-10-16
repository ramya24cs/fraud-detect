
import { useState } from "react";
import {
  Link,
  useLocation,
  useNavigate,
} from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();

  const [formData, setFormData] = useState({
    email: location.state?.email || "",
    password: "",
  });

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const registered = location.state?.registered === true;
  const sessionExpired = location.state?.sessionExpired === true;

  const handleChange = (event) => {
    setFormData({
      ...formData,
      [event.target.name]: event.target.value,
    });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      await login(formData);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Login failed. Check your email and password."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page auth-page">
      <div className="auth-layout">
        <section className="auth-visual" aria-label="Fraud monitoring overview">
          <div className="auth-brand">
            <span className="auth-brand-mark" aria-hidden="true">
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
            <span>Sentinel<span className="auth-brand-light">Risk</span></span>
          </div>

          <div className="auth-hero-copy">
            <span className="auth-overline">
              <span className="auth-live-dot" />
              INTELLIGENCE · PROTECTION · TRUST
            </span>
            <h1>
              See risk
              <br />
              <span>before it strikes.</span>
            </h1>
            <p>
              A clearer view of every transaction. Spot unusual activity,
              understand risk, and act with confidence.
            </p>
          </div>

          <div className="auth-visualization" aria-hidden="true">
            <div className="auth-grid-glow" />
            <div className="auth-orbit auth-orbit-outer" />
            <div className="auth-orbit auth-orbit-inner" />
            <svg className="auth-signal-chart" viewBox="0 0 620 250" fill="none">
              <defs>
                <linearGradient id="signal-stroke" x1="35" y1="120" x2="590" y2="120">
                  <stop stopColor="#38BDF8" stopOpacity=".12" />
                  <stop offset=".52" stopColor="#38BDF8" />
                  <stop offset="1" stopColor="#A78BFA" stopOpacity=".65" />
                </linearGradient>
                <linearGradient id="signal-fill" x1="310" y1="45" x2="310" y2="240">
                  <stop stopColor="#38BDF8" stopOpacity=".2" />
                  <stop offset="1" stopColor="#38BDF8" stopOpacity="0" />
                </linearGradient>
              </defs>
              <path
                d="M20 191h580M20 140h580M20 89h580M20 38h580"
                stroke="white"
                strokeOpacity=".08"
                strokeDasharray="4 8"
              />
              <path
                d="M20 182 92 176l35 8 41-25 35 8 42-63 37 50 38-98 34 72 40-20 36 39 42-24 37 8 51-53 43 11 37-22"
                stroke="url(#signal-stroke)"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M20 182 92 176l35 8 41-25 35 8 42-63 37 50 38-98 34 72 40-20 36 39 42-24 37 8 51-53 43 11 37-22v202H20V182Z"
                fill="url(#signal-fill)"
              />
              <circle cx="355" cy="138" r="5" fill="#38BDF8" />
              <circle cx="355" cy="138" r="12" stroke="#38BDF8" strokeOpacity=".35" />
            </svg>
            <div className="auth-scan-card">
              <span className="auth-scan-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none">
                  <path d="m3 12 5-5 4 4 8-8M15 3h5v5" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
                  <path d="M4 17h4m3-3h4m3-4h3" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
                </svg>
              </span>
              <span>
                <strong>Transaction signals</strong>
                <small>Patterns brought into focus</small>
              </span>
              <span className="auth-scan-pulse" />
            </div>
            <div className="auth-visual-caption">
              <span>RISK SIGNAL</span>
              <span>LIVE MONITORING</span>
            </div>
          </div>

          <div className="auth-trust-row">
            <span><span className="auth-check">✓</span> Account-level visibility</span>
            <span><span className="auth-check">✓</span> Risk-aware decisions</span>
          </div>
        </section>

        <section className="auth-form-panel">
          <div className="auth-form-topline">
            <span className="auth-mobile-brand">Sentinel<span>Risk</span></span>
            <span className="auth-secure-label">
              <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
                <rect x="4.5" y="8.5" width="11" height="8" rx="2" stroke="currentColor" strokeWidth="1.5" />
                <path d="M7 8V6a3 3 0 0 1 6 0v2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
              SECURE SIGN IN
            </span>
          </div>

          <div className="auth-form-content">
            <span className="auth-form-eyebrow">OPERATOR PORTAL</span>
            <h2>Welcome back</h2>
            <p className="auth-form-intro">Sign in to continue to your risk dashboard.</p>

            {registered && (
              <p className="auth-success" role="status">
                Your account is ready. Sign in to get started.
              </p>
            )}
            {sessionExpired && (
              <p className="login-error" role="status">
                Your session expired. Please sign in again to continue.
              </p>
            )}

            <form onSubmit={handleSubmit}>
              <div>
                <label htmlFor="email">Email address</label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="you@company.com"
                  autoComplete="email"
                  required
                />
              </div>

              <div>
                <label htmlFor="password">Password</label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="Enter your password"
                  autoComplete="current-password"
                  required
                />
              </div>

              {error && (
                <p className="login-error" role="alert">
                  {error}
                </p>
              )}

              <button type="submit" disabled={loading}>
                <span>{loading ? "Signing in..." : "Sign in to dashboard"}</span>
                {!loading && <span aria-hidden="true">→</span>}
              </button>
            </form>

            <p className="auth-register-prompt">
              New to SentinelRisk? <Link to="/register">Create an account</Link>
            </p>
          </div>

          <div className="auth-form-footer">
            <span>Protected access for your account</span>
            <span>© Fraud Detection System</span>
          </div>
        </section>
      </div>
    </div>
  );
}

export default Login;
