// src/pages/ResetSuccessPage.jsx
import { Link } from "react-router-dom";
import "../styles.css";

export default function ResetSuccessPage() {
  return (
    <div className="auth-container verification-page">
      <div className="verification-icon success">✓</div>
      <h2 className="auth-title">Password Reset Complete</h2>
      <p className="verification-message">
        Your password has been successfully reset. You can now log in with your new password.
      </p>
      <Link to="/" className="auth-button">
        Go to Login
      </Link>
    </div>
  );
}
