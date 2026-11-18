// src/pages/ForgotPassword.jsx
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import authService from "../services/authService";
import Button from "../components/Button";
import Alert from "../components/Alert";
import "../styles.css";

export default function ForgotPassword() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!email.trim()) {
      setError("Please enter your email address");
      return;
    }

    if (!/^[^\s@]+@hcmut\.edu\.vn$/.test(email)) {
      setError("Please enter a valid @hcmut.edu.vn email");
      return;
    }

    setLoading(true);
    try {
      await authService.requestPasswordReset(email);
      navigate("/reset-sent");
    } catch (err) {
      // Always show success to prevent email enumeration
      navigate("/reset-sent");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <h2 className="auth-title">Reset Password</h2>
      <p className="auth-subtitle">
        Enter your email address and we'll send you a link to reset your password.
      </p>

      {error && <Alert type="error">{error}</Alert>}

      <form onSubmit={handleSubmit}>
        <div className="form-field">
          <input
            type="email"
            placeholder="Email (@hcmut.edu.vn)"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={`auth-input ${error ? 'input-error' : ''}`}
            autoComplete="email"
          />
        </div>

        <Button type="submit" loading={loading}>
          Send Reset Link
        </Button>
      </form>

      <p className="auth-link">
        <Link to="/">Back to Login</Link>
      </p>
    </div>
  );
}
