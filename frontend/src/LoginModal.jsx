import { useState } from "react";
import { Shield, Lock, User, KeyRound, AlertCircle, ArrowRight, CheckCircle2 } from "lucide-react";
import { useAuth } from "./AuthContext";

export const LoginModal = () => {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError("Please fill in both username and password.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await login(username, password);
    } catch (err) {
      setError(err.message || "Failed to authenticate. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  const handleFillDemo = () => {
    setUsername("admin");
    setPassword("admin123");
    setError("");
  };

  return (
    <div className="login-overlay">
      <div className="login-card">
        <div className="login-header">
          <div className="security-shield-icon">
            <Shield size={36} />
          </div>
          <h2>Private Search Portal</h2>
          <div className="security-badge">
            <Lock size={12} style={{ marginRight: "4px" }} />
            Encrypted TLS / Tailscale Overlay
          </div>
          <p className="login-subtitle">
            This metasearch infrastructure is private and accessible only to authorized network members.
          </p>
        </div>

        {error && (
          <div className="auth-error-banner">
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="login-form">
          <div className="input-group">
            <label>
              <User size={14} style={{ marginRight: "6px" }} />
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. admin"
              autoFocus
              required
            />
          </div>

          <div className="input-group">
            <label>
              <KeyRound size={14} style={{ marginRight: "6px" }} />
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              required
            />
          </div>

          <button type="submit" className="login-button" disabled={loading}>
            {loading ? "Authenticating..." : "Unlock Private Search"}
            <ArrowRight size={16} style={{ marginLeft: "6px" }} />
          </button>
        </form>

        <div className="demo-credentials-box">
          <div className="demo-info-row">
            <span>Default Admin Demo:</span>
            <code>admin</code> / <code>admin123</code>
          </div>
          <button type="button" onClick={handleFillDemo} className="fill-demo-btn">
            <CheckCircle2 size={13} style={{ marginRight: "4px" }} />
            Fill Demo Credentials
          </button>
        </div>
      </div>
    </div>
  );
};
