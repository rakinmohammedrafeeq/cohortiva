// src/pages/VerifyEmailPage.jsx
import { useState, useEffect } from "react";
import { Link, useParams } from "react-router-dom";
import authService from "../services/authService";
import LoadingSpinner from "../components/LoadingSpinner";
import Alert from "../components/Alert";
import "../styles.css";

export default function VerifyEmailPage() {
  const { token } = useParams();
  const [status, setStatus] = useState("loading"); // loading, success, error
  const [message, setMessage] = useState("");

  useEffect(() => {
    const verify = async () => {
      try {
        await authService.verifyEmail(token);
        setStatus("success");
        setMessage("Your email has been verified successfully!");
      } catch (err) {
        setStatus("error");
        const errorMsg = err?.response?.data?.error || "Invalid or expired verification link.";
        setMessage(errorMsg);
      }
    };

    if (token) {
      verify();
    } else {
      setStatus("error");
      setMessage("No verification token provided.");
    }
  }, [token]);

  return (
    <div className="auth-container verification-page">
      {status === "loading" && (
        <>
          <LoadingSpinner size="large" />
          <p className="verification-message">Verifying your email...</p>
        </>
      )}

      {status === "success" && (
        <>
          <div className="verification-icon success">✓</div>
          <h2 className="auth-title">Email Verified!</h2>
          <Alert type="success">{message}</Alert>
          <p className="verification-message">
            Your account is now active. You can log in to access your dashboard.
          </p>
          <Link to="/" className="auth-button">
            Go to Login
          </Link>
        </>
      )}

      {status === "error" && (
        <>
          <div className="verification-icon error">✕</div>
          <h2 className="auth-title">Verification Failed</h2>
          <Alert type="error">{message}</Alert>
          <p className="verification-message">
            The verification link may be invalid or expired.
          </p>
          <div className="verification-actions">
            <Link to="/verification-sent" className="auth-link">
              Request New Link
            </Link>
            <span className="link-separator">|</span>
            <Link to="/" className="auth-link">
              Back to Login
            </Link>
          </div>
        </>
      )}
    </div>
  );
}
