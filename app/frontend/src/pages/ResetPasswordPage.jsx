// src/pages/ResetPasswordPage.jsx
import { useState, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import authService from "../services/authService";
import PasswordInput from "../components/PasswordInput";
import Button from "../components/Button";
import Alert from "../components/Alert";
import LoadingSpinner from "../components/LoadingSpinner";
import "../styles.css";

export default function ResetPasswordPage() {
  const { uid, token } = useParams();
  const navigate = useNavigate();
  const [validating, setValidating] = useState(true);
  const [valid, setValid] = useState(false);
  const [form, setForm] = useState({
    new_password: "",
    confirm_password: "",
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const validateToken = async () => {
      try {
        await authService.validateResetToken(uid, token);
        setValid(true);
      } catch (err) {
        setValid(false);
      } finally {
        setValidating(false);
      }
    };

    if (uid && token) {
      validateToken();
    } else {
      setValid(false);
      setValidating(false);
    }
  }, [uid, token]);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    if (errors[e.target.name]) {
      setErrors({ ...errors, [e.target.name]: null });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const newErrors = {};

    if (!form.new_password) {
      newErrors.new_password = "Password is required";
    } else if (!/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,}$/.test(form.new_password)) {
      newErrors.new_password = "8+ characters with uppercase, lowercase, and number";
    }

    if (form.new_password !== form.confirm_password) {
      newErrors.confirm_password = "Passwords do not match";
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setLoading(true);
    setErrors({});

    try {
      await authService.confirmPasswordReset(uid, token, form.new_password);
      navigate("/reset-success");
    } catch (err) {
      const resp = err?.response?.data;
      if (resp) {
        setErrors(resp);
      } else {
        setErrors({ general: "Failed to reset password. Please try again." });
      }
    } finally {
      setLoading(false);
    }
  };

  if (validating) {
    return (
      <div className="auth-container verification-page">
        <LoadingSpinner size="large" />
        <p className="verification-message">Validating reset link...</p>
      </div>
    );
  }

  if (!valid) {
    return (
      <div className="auth-container verification-page">
        <div className="verification-icon error">✕</div>
        <h2 className="auth-title">Invalid Link</h2>
        <Alert type="error">
          This password reset link is invalid or has expired.
        </Alert>
        <p className="verification-message">
          Please request a new password reset link.
        </p>
        <Link to="/forgot-password" className="auth-button">
          Request New Link
        </Link>
      </div>
    );
  }

  return (
    <div className="auth-container">
      <h2 className="auth-title">Set New Password</h2>
      <p className="auth-subtitle">
        Enter your new password below.
      </p>

      {errors.general && <Alert type="error">{errors.general}</Alert>}
      {errors.non_field_errors && (
        <Alert type="error">
          {Array.isArray(errors.non_field_errors)
            ? errors.non_field_errors.join(" ")
            : errors.non_field_errors}
        </Alert>
      )}

      <form onSubmit={handleSubmit}>
        <div className="form-field">
          <PasswordInput
            name="new_password"
            placeholder="New Password"
            value={form.new_password}
            onChange={handleChange}
            error={errors.new_password}
            autoComplete="new-password"
          />
          {errors.new_password && <p className="form-error">{errors.new_password}</p>}
        </div>

        <div className="form-field">
          <PasswordInput
            name="confirm_password"
            placeholder="Confirm New Password"
            value={form.confirm_password}
            onChange={handleChange}
            error={errors.confirm_password}
            autoComplete="new-password"
          />
          {errors.confirm_password && <p className="form-error">{errors.confirm_password}</p>}
        </div>

        <Button type="submit" loading={loading}>
          Reset Password
        </Button>
      </form>
    </div>
  );
}
