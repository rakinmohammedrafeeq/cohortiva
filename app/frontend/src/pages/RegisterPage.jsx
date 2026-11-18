// src/pages/RegisterPage.jsx
import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import authService from "../services/authService";
import PasswordInput from "../components/PasswordInput";
import Button from "../components/Button";
import Alert from "../components/Alert";
import ProgressIndicator from "../components/ProgressIndicator";
import "../styles.css";

export default function RegisterPage() {
  const navigate = useNavigate();
  const MAX_LEN = 75;
  const [step, setStep] = useState(1);
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    confirm_password: "",
    first_name: "",
    last_name: "",
    student_id: "",
    faculty: "",
    major: "",
  });
  const [faculties, setFaculties] = useState([]);
  const [majors, setMajors] = useState([]);
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState("");

  const handleChange = (e) => {
    const value = e.target.value.slice(0, MAX_LEN);
    setForm({ ...form, [e.target.name]: value });
    
    // Clear field-specific error when user starts typing
    if (errors[e.target.name]) {
      setErrors({ ...errors, [e.target.name]: null });
    }

    // Password strength indicator
    if (e.target.name === "password") {
      const pwd = value;
      if (pwd.length === 0) {
        setPasswordStrength("");
      } else if (pwd.length < 8) {
        setPasswordStrength("weak");
      } else if (/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,}$/.test(pwd)) {
        setPasswordStrength("strong");
      } else {
        setPasswordStrength("medium");
      }
    }
  };

  const validateStep1 = () => {
    const newErrors = {};

    if (!form.username.trim()) {
      newErrors.username = "Username is required";
    } else if (!/^[a-zA-Z][a-zA-Z0-9_]{2,20}$/.test(form.username)) {
      newErrors.username = "Username must be 3-21 characters, start with a letter";
    }

    if (!form.email.trim()) {
      newErrors.email = "Email is required";
    } else if (!/^[^\s@]+@hcmut\.edu\.vn$/.test(form.email)) {
      newErrors.email = "Must be a valid @hcmut.edu.vn email";
    }

    if (!form.password) {
      newErrors.password = "Password is required";
    } else if (!/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,}$/.test(form.password)) {
      newErrors.password = "8+ characters with uppercase, lowercase, and number";
    }

    if (form.password !== form.confirm_password) {
      newErrors.confirm_password = "Passwords do not match";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const validateStep2 = () => {
    const newErrors = {};

    if (!form.first_name.trim()) {
      newErrors.first_name = "First name is required";
    } else if (!/^[A-Za-zÀ-ỹ\s]+$/.test(form.first_name)) {
      newErrors.first_name = "Letters and spaces only";
    }

    if (!form.last_name.trim()) {
      newErrors.last_name = "Last name is required";
    } else if (!/^[A-Za-zÀ-ỹ\s]+$/.test(form.last_name)) {
      newErrors.last_name = "Letters and spaces only";
    }

    if (!form.student_id.trim()) {
      newErrors.student_id = "Student ID is required";
    } else if (!/^\d{7}$/.test(form.student_id)) {
      newErrors.student_id = "Must be exactly 7 digits";
    }

    if (!form.faculty) {
      newErrors.faculty = "Please select a faculty";
    }

    if (!form.major) {
      newErrors.major = "Please select a major";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateStep1()) {
      setStep(2);
    }
  };

  const handleBack = () => {
    setStep(1);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateStep2()) return;

    setLoading(true);
    setErrors({});

    try {
      const payload = { ...form };
      payload.faculty = Number(payload.faculty);
      payload.major = Number(payload.major);
      
      await authService.registerStudent(payload);
      navigate("/verification-sent");
    } catch (err) {
      const resp = err?.response?.data;
      if (resp) {
        setErrors(resp);
        // If username/email error, go back to step 1
        if (resp.username || resp.email) {
          setStep(1);
        }
      } else {
        setErrors({ general: "Registration failed. Please try again." });
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let mounted = true;
    authService
      .getFaculties()
      .then((data) => {
        if (mounted) setFaculties(data || []);
      })
      .catch(() => setFaculties([]));
    return () => (mounted = false);
  }, []);

  useEffect(() => {
    if (!form.faculty) {
      setMajors([]);
      setForm((s) => ({ ...s, major: "" }));
      return;
    }
    let mounted = true;
    authService
      .getMajors(form.faculty)
      .then((data) => {
        if (mounted) setMajors(data || []);
      })
      .catch(() => setMajors([]));
    return () => (mounted = false);
  }, [form.faculty]);

  return (
    <div className="auth-container">
      <h2 className="auth-title">Create Account</h2>
      
      <ProgressIndicator currentStep={step} totalSteps={2} />

      {errors.general && <Alert type="error">{errors.general}</Alert>}
      {errors.non_field_errors && (
        <Alert type="error">
          {Array.isArray(errors.non_field_errors) 
            ? errors.non_field_errors.join(" ") 
            : errors.non_field_errors}
        </Alert>
      )}

      {step === 1 && (
        <div className="registration-step">
          <div className="form-field">
            <input
              type="text"
              name="username"
              placeholder="Username"
              value={form.username}
              onChange={handleChange}
              className={`auth-input ${errors.username ? 'input-error' : ''}`}
              autoComplete="off"
            />
            {errors.username && <p className="form-error">{errors.username}</p>}
          </div>

          <div className="form-field">
            <input
              type="email"
              name="email"
              placeholder="Email (@hcmut.edu.vn)"
              value={form.email}
              onChange={handleChange}
              className={`auth-input ${errors.email ? 'input-error' : ''}`}
              autoComplete="off"
            />
            {errors.email && <p className="form-error">{errors.email}</p>}
          </div>

          <div className="form-field">
            <PasswordInput
              name="password"
              placeholder="Password"
              value={form.password}
              onChange={handleChange}
              error={errors.password}
              autoComplete="new-password"
            />
            {passwordStrength && (
              <div className={`password-strength strength-${passwordStrength}`}>
                {passwordStrength === "weak" && "Weak"}
                {passwordStrength === "medium" && "Medium"}
                {passwordStrength === "strong" && "Strong ✓"}
              </div>
            )}
            {errors.password && <p className="form-error">{errors.password}</p>}
          </div>

          <div className="form-field">
            <PasswordInput
              name="confirm_password"
              placeholder="Confirm Password"
              value={form.confirm_password}
              onChange={handleChange}
              error={errors.confirm_password}
              autoComplete="new-password"
            />
            {errors.confirm_password && <p className="form-error">{errors.confirm_password}</p>}
          </div>

          <Button type="button" onClick={handleNext}>
            Next
          </Button>
        </div>
      )}

      {step === 2 && (
        <form onSubmit={handleSubmit} className="registration-step">
          <div className="form-field">
            <input
              type="text"
              name="first_name"
              placeholder="First Name"
              value={form.first_name}
              onChange={handleChange}
              className={`auth-input ${errors.first_name ? 'input-error' : ''}`}
              autoComplete="given-name"
            />
            {errors.first_name && <p className="form-error">{errors.first_name}</p>}
          </div>

          <div className="form-field">
            <input
              type="text"
              name="last_name"
              placeholder="Last Name"
              value={form.last_name}
              onChange={handleChange}
              className={`auth-input ${errors.last_name ? 'input-error' : ''}`}
              autoComplete="family-name"
            />
            {errors.last_name && <p className="form-error">{errors.last_name}</p>}
          </div>

          <div className="form-field">
            <input
              type="text"
              name="student_id"
              placeholder="Student ID (7 digits)"
              value={form.student_id}
              onChange={handleChange}
              className={`auth-input ${errors.student_id ? 'input-error' : ''}`}
              autoComplete="off"
            />
            {errors.student_id && <p className="form-error">{errors.student_id}</p>}
          </div>

          <div className="form-field">
            <select
              name="faculty"
              value={form.faculty}
              onChange={handleChange}
              className={`auth-select ${errors.faculty ? 'input-error' : ''}`}
            >
              <option value="">Select Faculty</option>
              {faculties.map((f) => (
                <option key={f.id} value={f.id}>
                  {f.name}
                </option>
              ))}
            </select>
            {errors.faculty && <p className="form-error">{errors.faculty}</p>}
          </div>

          <div className="form-field">
            <select
              name="major"
              value={form.major}
              onChange={handleChange}
              className={`auth-select ${errors.major ? 'input-error' : ''}`}
              disabled={!form.faculty}
            >
              <option value="">
                {!form.faculty ? "Select faculty first" : majors.length ? "Select Major" : "No majors available"}
              </option>
              {majors.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name}
                </option>
              ))}
            </select>
            {errors.major && <p className="form-error">{errors.major}</p>}
          </div>

          <div className="button-group">
            <Button type="button" variant="secondary" onClick={handleBack}>
              Back
            </Button>
            <Button type="submit" loading={loading}>
              Register
            </Button>
          </div>
        </form>
      )}

      <p className="auth-link">
        Already have an account? <Link to="/">Login</Link>
      </p>
    </div>
  );
}
