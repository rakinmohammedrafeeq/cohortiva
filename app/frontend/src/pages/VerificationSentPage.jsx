// src/pages/VerificationSentPage.jsx
import { useState } from "react";
import { Link } from "react-router-dom";
import authService from "../services/authService";
import Button from "../components/Button";
import Alert from "../components/Alert";
import "../styles.css";

export default function VerificationSentPage() {
  const [cooldown, setCooldown] = useState(0);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const handleResend = async () => {
    setLoading(true);
    setMessage("");
    try {
      await authService.resendVerification();
      setMessage("Verification email sent! Check your inbox.");
      setCooldown(60);
      const interval = setInterval(() => {
        setCooldown((prev) => {
          if (prev <= 1) {
            clearInterval(interval);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } catch (err) {
      setMessage(err?.response?.data?.error || "Failed to resend email. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container verification-page">
      <div className="verification-icon">✉️</div>
      <h2 className="auth-title">Check Your Email</h2>
      <p className="verification-message">
        We've sent a verification link to your email address. 
        Click the link to verify your account.
      </p>

      {message && (
        <Alert type={message.includes("sent") ? "success" : "error"}>
          {message}
        </Alert>
      )}

      <div className="verification-actions">
        <Button 
          onClick={handleResend} 
          disabled={cooldown > 0}
          loading={loading}
        >
          {cooldown > 0 ? `Resend in ${cooldown}s` : "Resend Email"}
        </Button>
      </div>

      <p className="auth-link">
        <Link to="/">Back to Login</Link>
      </p>
    </div>
  );
}
