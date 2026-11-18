// src/pages/LoginPage.jsx
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import authService from "../services/authService";
import PasswordInput from "../components/PasswordInput";
import Button from "../components/Button";
import Alert from "../components/Alert";
import "../styles.css";

export default function LoginPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [emailVerified, setEmailVerified] = useState(true);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    if (error) setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!form.username.trim() || !form.password) {
      setError("Please enter both username and password");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await authService.login(form.username, form.password);
      
      // Check email_verified status
      if (response.email_verified === false) {
        setEmailVerified(false);
      }
      
      // Proceed to dashboard
      setTimeout(() => {
        window.location.href = "/dashboard";
      }, emailVerified ? 0 : 1500);
    } catch (err) {
      setError("Invalid username or password");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container fade-in">
      <h2 className="auth-title">Welcome Back</h2>
      <p className="auth-subtitle">Sign in to continue your learning journey</p>

      {!emailVerified && (
        <Alert type="warning">
          Your email is not verified. Please check your inbox and verify your email.
        </Alert>
      )}

      {error && <Alert type="error">{error}</Alert>}

      <form onSubmit={handleSubmit}>
        <div className="form-field">
          <input
            type="text"
            name="username"
            placeholder="Username"
            value={form.username}
            onChange={handleChange}
            className="auth-input"
            autoComplete="username"
          />
        </div>

        <div className="form-field">
          <PasswordInput
            name="password"
            placeholder="Password"
            value={form.password}
            onChange={handleChange}
            autoComplete="current-password"
          />
        </div>

        <div className="auth-extra">
          <Link to="/forgot-password">Forgot Password?</Link>
        </div>

        <Button type="submit" loading={loading}>
          Login
        </Button>
      </form>

      <p className="auth-link">
        Don't have an account? <Link to="/register">Create a learner account</Link> or <Link to="/apply-coach">Apply as a coach</Link>
      </p>
      
      <p className="auth-link" style={{ marginTop: "0.75rem" }}>
        <Link to="/">← Back to Home</Link>
      </p>
    </div>
  );
}
