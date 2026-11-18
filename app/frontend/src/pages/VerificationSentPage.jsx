// src/pages/VerificationSentPage.jsx
import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import authService from "../services/authService";
import Button from "../components/Button";
import Alert from "../components/Alert";
import "../styles.css";

// Resend status codes from the backend
const STATUS_IDLE = "idle";
const STATUS_SENDING = "sending";
const STATUS_SENT = "sent";
const STATUS_COOLDOWN = "cooldown";
const STATUS_DELIVERY_FAILED = "delivery_failed";
const STATUS_ERROR = "error";

export default function VerificationSentPage() {
  const location = useLocation();

  // Email passed via navigate state from RegisterPage; falls back to empty
  // so the user can enter it manually if the page is refreshed.
  const [email, setEmail] = useState(() => location.state?.email || "");
  const [emailInput, setEmailInput] = useState("");
  const [showEmailInput, setShowEmailInput] = useState(!location.state?.email);

  const [resendStatus, setResendStatus] = useState(STATUS_IDLE);
  const [message, setMessage] = useState("");
  const [cooldown, setCooldown] = useState(0);
  const [loading, setLoading] = useState(false);

  const startCooldown = (seconds) => {
    setCooldown(seconds);
    const interval = setInterval(() => {
      setCooldown((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  const handleResend = async (e) => {
    e?.preventDefault();

    const resolvedEmail = email || emailInput.trim();
    if (!resolvedEmail) {
      setResendStatus(STATUS_ERROR);
      setMessage("Please enter your email address to resend the verification link.");
      return;
    }

    setLoading(true);
    setResendStatus(STATUS_SENDING);
    setMessage("");

    try {
      const data = await authService.resendVerification(resolvedEmail);

      // Track the email used so subsequent resends don't need re-entry
      if (!email) setEmail(resolvedEmail);
      setShowEmailInput(false);

      setResendStatus(STATUS_SENT);
      setMessage(data?.detail || "Verification email sent! Check your inbox.");
      startCooldown(60);
    } catch (err) {
      const status = err?.response?.status;
      const detail = err?.response?.data?.detail || "";
      const retryAfter = err?.response?.data?.retry_after;

      if (status === 429) {
        // Per-account cooldown reported by backend
        const secs = retryAfter || 60;
        setResendStatus(STATUS_COOLDOWN);
        setMessage(detail || `Please wait ${secs} seconds before requesting another email.`);
        startCooldown(secs);
      } else if (status === 503) {
        // Email delivery failed on the server
        setResendStatus(STATUS_DELIVERY_FAILED);
        setMessage("We could not deliver the email right now. Please try again in a moment.");
      } else if (!err?.response) {
        // Network / CORS / timeout
        setResendStatus(STATUS_ERROR);
        setMessage("Network error — check your internet connection and try again.");
      } else {
        setResendStatus(STATUS_ERROR);
        setMessage(detail || "Something went wrong. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  const alertType = () => {
    if (resendStatus === STATUS_SENT) return "success";
    if (resendStatus === STATUS_COOLDOWN) return "warning";
    return "error";
  };

  return (
    <div className="auth-container verification-page">
      <div className="verification-icon">✉️</div>
      <h2 className="auth-title">Check Your Email</h2>

      {email ? (
        <p className="verification-message">
          We sent a verification link to <strong>{email}</strong>.{" "}
          Click the link in the email to activate your account.
        </p>
      ) : (
        <p className="verification-message">
          A verification link has been sent to your registered email address.
          Click the link to activate your account.
        </p>
      )}

      {/* Email input — shown on page refresh (state lost) or when email is unknown */}
      {showEmailInput && (
        <form onSubmit={handleResend} style={{ marginBottom: "1rem" }}>
          <label className="form-label" htmlFor="resend-email">
            Your registered email address
          </label>
          <input
            id="resend-email"
            type="email"
            className="form-input"
            placeholder="you@example.com"
            value={emailInput}
            onChange={(e) => setEmailInput(e.target.value)}
            autoComplete="email"
            required
          />
          <Button
            type="submit"
            loading={loading}
            disabled={cooldown > 0}
            style={{ marginTop: "0.75rem", width: "100%" }}
          >
            {cooldown > 0 ? `Resend in ${cooldown}s` : "Send Verification Email"}
          </Button>
        </form>
      )}

      {/* Status feedback */}
      {message && (
        <Alert type={alertType()}>
          {message}
        </Alert>
      )}

      {/* Resend button — shown when email is known */}
      {!showEmailInput && (
        <div className="verification-actions">
          <Button
            onClick={handleResend}
            disabled={cooldown > 0}
            loading={loading}
          >
            {cooldown > 0 ? `Resend in ${cooldown}s` : "Resend Email"}
          </Button>

          {email && (
            <button
              type="button"
              className="auth-link-btn"
              onClick={() => {
                setShowEmailInput(true);
                setEmail("");
                setEmailInput("");
                setResendStatus(STATUS_IDLE);
                setMessage("");
              }}
              style={{ marginTop: "0.5rem", display: "block", fontSize: "0.82rem", color: "#64748B" }}
            >
              Wrong email address? Click to change it.
            </button>
          )}
        </div>
      )}

      <p className="auth-link" style={{ marginTop: "1.25rem" }}>
        <Link to="/">Back to Login</Link>
      </p>
    </div>
  );
}
