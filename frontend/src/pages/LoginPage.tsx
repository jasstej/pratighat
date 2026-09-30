import { useState, FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../utils/api";

export default function LoginPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (isLogin) {
        const data = await api.login(email, password) as any;
        localStorage.setItem("pratighat_token", data.access_token);
        localStorage.setItem("pratighat_refresh", data.refresh_token);
        navigate("/");
        window.location.reload();
      } else {
        const username = email.split('@')[0].replace(/[^a-zA-Z0-9_-]/g, '_').toLowerCase();
        await api.register({ username, email, full_name: name, password });
        setIsLogin(true);
        setError("Account created. Please log in.");
      }
    } catch (err: any) {
      setError(err.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-card">
      <div className="login-header">
        <h2>{isLogin ? "Welcome back" : "Create account"}</h2>
        <p className="login-desc">
          {isLogin
            ? "Sign in to access your security dashboard"
            : "Register a new account to get started"}
        </p>
      </div>

      {error && (
        <div className="login-error">
          <span>⚠</span>
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="login-form">
        {!isLogin && (
          <div className="form-group">
            <label htmlFor="name">Full name</label>
            <input
              id="name"
              type="text"
              placeholder="Jane Assessment"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>
        )}

        <div className="form-group">
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            placeholder="admin@pratighat.ai"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={6}
          />
        </div>

        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? (
            <>
              <span className="loading-spinner" style={{ width: "16px", height: "16px", borderWidth: "2px" }} />
              {isLogin ? "Signing in..." : "Creating account..."}
            </>
          ) : (
            isLogin ? "Sign in" : "Create account"
          )}
        </button>
      </form>

      <div className="toggle-row" style={{ textAlign: "center", marginTop: "12px" }}>
        <button
          className="btn-ghost-sm"
          onClick={() => {
            setIsLogin(!isLogin);
            setError("");
          }}
        >
          {isLogin ? "Need an account? Register" : "Have an account? Sign in"}
        </button>
      </div>

      <div className="login-demo">
        <div className="demo-label">Demo credentials</div>
        <div className="demo-creds">
          Email: <code>admin@pratighat.ai</code>
          <br />
          Password: <code>admin123</code>
        </div>
      </div>
    </div>
  );
}
