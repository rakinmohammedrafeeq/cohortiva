// src/pages/ResetSentPage.jsx
import { Link } from "react-router-dom";
import "../styles.css";

export default function ResetSentPage() {
  return (
    <div className="auth-container verification-page">
      <div className="verification-icon">✉️</div>
      <h2 className="auth-title">Check Your Email</h2>
      <p className="verification-message">
        If an account exists with that email, you'll receive password reset 
        instructions shortly.
      </p>
      <p className="verification-note">
        Please check your spam folder if you don't see the email within a few minutes.
      </p>
      <Link to="/" className="auth-button">
        Back to Login
      </Link>
    </div>
  );
}
