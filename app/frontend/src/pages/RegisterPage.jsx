// src/pages/RegisterPage.jsx
import { useState, useEffect } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import authService from "../services/authService";
import PasswordInput from "../components/PasswordInput";
import Button from "../components/Button";
import Alert from "../components/Alert";
import ProgressIndicator from "../components/ProgressIndicator";
import "../styles.css";

export default function RegisterPage({ initialRole }) {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const queryType = searchParams.get("type");

  // Account mode: "learner" or "coach"
  const [accountType, setAccountType] = useState(() => {
    if (initialRole === "coach" || queryType === "coach") return "coach";
    return "learner";
  });

  const MAX_LEN = 100;
  const [step, setStep] = useState(1);

  // Learner form state
  const [learnerForm, setLearnerForm] = useState({
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

  // Coach form state
  const [coachForm, setCoachForm] = useState({
    username: "",
    email: "",
    password: "",
    confirm_password: "",
    first_name: "",
    last_name: "",
    expertise: "",
    experience: "",
    qualifications: "",
    bio: "",
  });

  // Academic catalogue states
  const [faculties, setFaculties] = useState([]);
  const [facultiesLoading, setFacultiesLoading] = useState(false);
  const [facultiesError, setFacultiesError] = useState(null);

  const [majors, setMajors] = useState([]);
  const [majorsLoading, setMajorsLoading] = useState(false);
  const [majorsError, setMajorsError] = useState(null);

  // Common UI states
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState("");
  const [coachSubmitted, setCoachSubmitted] = useState(false);

  // Calculate password strength
  const calculateStrength = (pwd) => {
    if (!pwd || pwd.length === 0) return "";
    let strength = 0;
    if (pwd.length >= 8) strength++;
    if (pwd.length >= 12) strength++;
    if (/[a-z]/.test(pwd) && /[A-Z]/.test(pwd)) strength++;
    if (/\d/.test(pwd)) strength++;
    if (/[^a-zA-Z0-9]/.test(pwd)) strength++;

    if (strength <= 2) return "weak";
    if (strength <= 3) return "medium";
    return "strong";
  };

  const handleLearnerChange = (e) => {
    const value = e.target.value.slice(0, MAX_LEN);
    setLearnerForm((prev) => ({ ...prev, [e.target.name]: value }));

    if (errors[e.target.name]) {
      setErrors((prev) => ({ ...prev, [e.target.name]: null }));
    }

    if (e.target.name === "password") {
      setPasswordStrength(calculateStrength(value));
    }
  };

  const handleCoachChange = (e) => {
    const max = e.target.tagName === "TEXTAREA" ? 1000 : MAX_LEN;
    const value = e.target.value.slice(0, max);
    setCoachForm((prev) => ({ ...prev, [e.target.name]: value }));

    if (errors[e.target.name]) {
      setErrors((prev) => ({ ...prev, [e.target.name]: null }));
    }

    if (e.target.name === "password") {
      setPasswordStrength(calculateStrength(value));
    }
  };

  // Fetch faculties on mount
  useEffect(() => {
    let mounted = true;
    setFacultiesLoading(true);
    setFacultiesError(null);

    authService
      .getFaculties()
      .then((data) => {
        if (mounted) {
          setFaculties(Array.isArray(data) ? data : []);
          setFacultiesLoading(false);
        }
      })
      .catch((err) => {
        if (mounted) {
          console.error("Failed to load faculties:", err);
          setFaculties([]);
          setFacultiesError("Unable to load academic faculties from server.");
          setFacultiesLoading(false);
        }
      });

    return () => {
      mounted = false;
    };
  }, []);

  // Fetch majors when selected faculty changes
  useEffect(() => {
    if (!learnerForm.faculty) {
      setMajors([]);
      setMajorsError(null);
      setLearnerForm((prev) => ({ ...prev, major: "" }));
      return;
    }

    let mounted = true;
    setMajorsLoading(true);
    setMajorsError(null);

    authService
      .getMajors(learnerForm.faculty)
      .then((data) => {
        if (mounted) {
          setMajors(Array.isArray(data) ? data : []);
          setMajorsLoading(false);
        }
      })
      .catch((err) => {
        if (mounted) {
          console.error("Failed to load majors:", err);
          setMajors([]);
          setMajorsError("Unable to load majors for selected faculty.");
          setMajorsLoading(false);
        }
      });

    return () => {
      mounted = false;
    };
  }, [learnerForm.faculty]);

  // Validation helpers
  const validateAccountCredentials = (username, email, password, confirm_password) => {
    const newErrors = {};

    if (!username.trim()) {
      newErrors.username = "Username is required";
    } else if (!/^[a-zA-Z][a-zA-Z0-9_]{2,29}$/.test(username.trim())) {
      newErrors.username = "Username must be 3-30 characters, start with a letter, and contain only letters, numbers, or underscores";
    }

    if (!email.trim()) {
      newErrors.email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      newErrors.email = "Must be a valid email address";
    }

    if (!password) {
      newErrors.password = "Password is required";
    } else if (password.length < 8) {
      newErrors.password = "Password must be at least 8 characters";
    } else if (/^\d+$/.test(password)) {
      newErrors.password = "Password cannot be entirely numeric";
    } else if (username && password.toLowerCase().includes(username.toLowerCase())) {
      newErrors.password = "Password is too similar to your username";
    } else if (email && password.toLowerCase().includes(email.split("@")[0].toLowerCase())) {
      newErrors.password = "Password is too similar to your email";
    }

    if (password !== confirm_password) {
      newErrors.confirm_password = "Passwords do not match";
    }

    return newErrors;
  };

  const validateLearnerStep1 = () => {
    const newErrors = validateAccountCredentials(
      learnerForm.username,
      learnerForm.email,
      learnerForm.password,
      learnerForm.confirm_password
    );
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const validateLearnerStep2 = () => {
    const newErrors = {};

    if (!learnerForm.first_name.trim()) {
      newErrors.first_name = "First name is required";
    } else if (!/^[A-Za-zÀ-ỹ\s'-]+$/.test(learnerForm.first_name.trim())) {
      newErrors.first_name = "Letters and spaces only";
    }

    if (!learnerForm.last_name.trim()) {
      newErrors.last_name = "Last name is required";
    } else if (!/^[A-Za-zÀ-ỹ\s'-]+$/.test(learnerForm.last_name.trim())) {
      newErrors.last_name = "Letters and spaces only";
    }

    // Student ID is optional; if provided, validate reasonable alphanumeric format
    const trimmedSid = learnerForm.student_id ? learnerForm.student_id.trim() : "";
    if (trimmedSid) {
      if (!/^[a-zA-Z0-9\-_]{3,30}$/.test(trimmedSid)) {
        newErrors.student_id = "Student ID must be between 3 and 30 characters and contain only letters, numbers, hyphens, or underscores.";
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const validateCoachForm = () => {
    const newErrors = validateAccountCredentials(
      coachForm.username,
      coachForm.email,
      coachForm.password,
      coachForm.confirm_password
    );

    if (!coachForm.first_name.trim()) {
      newErrors.first_name = "First name is required";
    }
    if (!coachForm.last_name.trim()) {
      newErrors.last_name = "Last name is required";
    }
    if (!coachForm.expertise.trim()) {
      newErrors.expertise = "Areas of expertise are required";
    }
    if (!coachForm.experience.trim()) {
      newErrors.experience = "Relevant experience is required";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Learner submit
  const handleLearnerSubmit = async (e) => {
    e.preventDefault();
    if (!validateLearnerStep2()) return;

    setLoading(true);
    setErrors({});

    try {
      const trimmedSid = learnerForm.student_id ? learnerForm.student_id.trim() : "";
      const payload = {
        username: learnerForm.username.trim(),
        email: learnerForm.email.trim(),
        password: learnerForm.password,
        first_name: learnerForm.first_name.trim(),
        last_name: learnerForm.last_name.trim(),
        student_id: trimmedSid ? trimmedSid.toUpperCase() : null,
        faculty: learnerForm.faculty ? Number(learnerForm.faculty) : null,
        major: learnerForm.major ? Number(learnerForm.major) : null,
      };

      await authService.registerStudent(payload);
      navigate("/verification-sent");
    } catch (err) {
      const resp = err?.response?.data;
      if (resp && typeof resp === "object") {
        setErrors(resp);
        // If step 1 field failed on backend, navigate back to step 1
        if (resp.username || resp.email || resp.password) {
          setStep(1);
        }
      } else {
        setErrors({ general: "Registration failed. Please check your network connection and try again." });
      }
    } finally {
      setLoading(false);
    }
  };

  // Coach application submit
  const handleCoachSubmit = async (e) => {
    e.preventDefault();
    if (!validateCoachForm()) return;

    setLoading(true);
    setErrors({});

    try {
      const payload = {
        username: coachForm.username.trim(),
        email: coachForm.email.trim(),
        password: coachForm.password,
        first_name: coachForm.first_name.trim(),
        last_name: coachForm.last_name.trim(),
        expertise: coachForm.expertise.trim(),
        experience: coachForm.experience.trim(),
        qualifications: coachForm.qualifications.trim(),
        bio: coachForm.bio.trim(),
      };

      await authService.applyCoach(payload);
      setCoachSubmitted(true);
    } catch (err) {
      const resp = err?.response?.data;
      if (resp && typeof resp === "object") {
        setErrors(resp);
      } else {
        setErrors({ general: "Application submission failed. Please check your network connection and try again." });
      }
    } finally {
      setLoading(false);
    }
  };

  const switchAccountType = (type) => {
    setAccountType(type);
    setStep(1);
    setErrors({});
    setPasswordStrength("");
  };

  return (
    <div className="auth-container" style={{ maxWidth: accountType === "coach" ? "580px" : "480px" }}>
      {/* Account Type Selector */}
      <div className="account-type-selector" role="tablist" aria-label="Account Type Selection">
        <button
          type="button"
          role="tab"
          aria-selected={accountType === "learner"}
          className={`account-type-btn ${accountType === "learner" ? "active" : ""}`}
          onClick={() => switchAccountType("learner")}
        >
          Learner Registration
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={accountType === "coach"}
          className={`account-type-btn ${accountType === "coach" ? "active" : ""}`}
          onClick={() => switchAccountType("coach")}
        >
          Apply as a Coach
        </button>
      </div>

      {/* Global Alerts */}
      {errors.general && <Alert type="error">{errors.general}</Alert>}
      {errors.non_field_errors && (
        <Alert type="error">
          {Array.isArray(errors.non_field_errors)
            ? errors.non_field_errors.join(" ")
            : errors.non_field_errors}
        </Alert>
      )}

      {/* COACH APPLICATION SUCCESS VIEW */}
      {accountType === "coach" && coachSubmitted ? (
        <div className="registration-step" style={{ textAlign: "center", padding: "1.5rem 0" }}>
          <h2 className="auth-title" style={{ color: "var(--success-green, #16A34A)" }}>
            Application Submitted
          </h2>
          <Alert type="info">
            Your coach application has been submitted and is currently pending administrator review.
            Please check your email inbox to verify your email address. You will receive active coach privileges
            once an administrator approves your application.
          </Alert>
          <div style={{ marginTop: "2rem" }}>
            <Button type="button" onClick={() => navigate("/")}>
              Return to Login
            </Button>
          </div>
        </div>
      ) : accountType === "coach" ? (
        /* COACH APPLICATION FORM */
        <div>
          <h2 className="auth-title">Apply as a Coach</h2>
          <p className="auth-subtitle" style={{ fontSize: "0.88rem", color: "#64748B", marginBottom: "1.2rem" }}>
            Share your expertise on Cohortiva. All coach applications are reviewed and approved by administrators.
          </p>

          <Alert type="warning">
            <strong>Approval Required:</strong> Coach accounts do not receive active privileges automatically. An administrator will review your application before coach features are unlocked.
          </Alert>

          <form onSubmit={handleCoachSubmit} className="registration-step">
            <h3 style={{ fontSize: "1rem", margin: "1rem 0 0.5rem", color: "#1E293B" }}>Account Credentials</h3>

            <div className="form-field">
              <input
                type="text"
                name="username"
                placeholder="Username *"
                value={coachForm.username}
                onChange={handleCoachChange}
                className={`auth-input ${errors.username ? "input-error" : ""}`}
                autoComplete="username"
              />
              {errors.username && <p className="form-error">{errors.username}</p>}
            </div>

            <div className="form-field">
              <input
                type="email"
                name="email"
                placeholder="Email Address *"
                value={coachForm.email}
                onChange={handleCoachChange}
                className={`auth-input ${errors.email ? "input-error" : ""}`}
                autoComplete="email"
              />
              {errors.email && <p className="form-error">{errors.email}</p>}
            </div>

            <div className="form-field">
              <PasswordInput
                name="password"
                placeholder="Password *"
                value={coachForm.password}
                onChange={handleCoachChange}
                error={errors.password}
                autoComplete="new-password"
              />
              <p className="form-hint">At least 8 characters. Cannot be entirely numeric.</p>
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
                placeholder="Confirm Password *"
                value={coachForm.confirm_password}
                onChange={handleCoachChange}
                error={errors.confirm_password}
                autoComplete="new-password"
              />
              {errors.confirm_password && <p className="form-error">{errors.confirm_password}</p>}
            </div>

            <h3 style={{ fontSize: "1rem", margin: "1.2rem 0 0.5rem", color: "#1E293B" }}>Personal & Coach Details</h3>

            <div style={{ display: "flex", gap: "0.75rem" }}>
              <div className="form-field" style={{ flex: 1 }}>
                <input
                  type="text"
                  name="first_name"
                  placeholder="First Name *"
                  value={coachForm.first_name}
                  onChange={handleCoachChange}
                  className={`auth-input ${errors.first_name ? "input-error" : ""}`}
                  autoComplete="given-name"
                />
                {errors.first_name && <p className="form-error">{errors.first_name}</p>}
              </div>

              <div className="form-field" style={{ flex: 1 }}>
                <input
                  type="text"
                  name="last_name"
                  placeholder="Last Name *"
                  value={coachForm.last_name}
                  onChange={handleCoachChange}
                  className={`auth-input ${errors.last_name ? "input-error" : ""}`}
                  autoComplete="family-name"
                />
                {errors.last_name && <p className="form-error">{errors.last_name}</p>}
              </div>
            </div>

            <div className="form-field">
              <textarea
                name="expertise"
                placeholder="Areas of Expertise (e.g. Algorithms, Data Science, Web Development) *"
                value={coachForm.expertise}
                onChange={handleCoachChange}
                className={`auth-textarea ${errors.expertise ? "input-error" : ""}`}
                rows={3}
              />
              <p className="form-hint">Specify the subjects and domains you are qualified to coach.</p>
              {errors.expertise && <p className="form-error">{errors.expertise}</p>}
            </div>

            <div className="form-field">
              <textarea
                name="experience"
                placeholder="Relevant Teaching / Coaching Experience *"
                value={coachForm.experience}
                onChange={handleCoachChange}
                className={`auth-textarea ${errors.experience ? "input-error" : ""}`}
                rows={3}
              />
              <p className="form-hint">Describe your teaching, tutoring, or practical mentoring background.</p>
              {errors.experience && <p className="form-error">{errors.experience}</p>}
            </div>

            <div className="form-field">
              <input
                type="text"
                name="qualifications"
                placeholder="Qualifications / Credentials (Optional)"
                value={coachForm.qualifications}
                onChange={handleCoachChange}
                className={`auth-input ${errors.qualifications ? "input-error" : ""}`}
              />
              <p className="form-hint">Degrees, certifications, or licenses (optional).</p>
              {errors.qualifications && <p className="form-error">{errors.qualifications}</p>}
            </div>

            <div className="form-field">
              <textarea
                name="bio"
                placeholder="Short Bio / Introduction (Optional)"
                value={coachForm.bio}
                onChange={handleCoachChange}
                className={`auth-textarea ${errors.bio ? "input-error" : ""}`}
                rows={3}
              />
              <p className="form-hint">A brief introductory note for prospective learners.</p>
              {errors.bio && <p className="form-error">{errors.bio}</p>}
            </div>

            <Button type="submit" loading={loading}>
              Submit Application
            </Button>
          </form>
        </div>
      ) : (
        /* LEARNER REGISTRATION FLOW */
        <div>
          <h2 className="auth-title">Create a learner account</h2>
          <p className="auth-subtitle" style={{ fontSize: "0.88rem", color: "#64748B", marginBottom: "1rem" }}>
            Join Cohortiva to connect with coaches and book learning sessions.
          </p>

          <ProgressIndicator currentStep={step} totalSteps={2} />

          {/* STEP 1: Account Credentials */}
          {step === 1 && (
            <div className="registration-step">
              <div className="form-field">
                <input
                  type="text"
                  name="username"
                  placeholder="Username *"
                  value={learnerForm.username}
                  onChange={handleLearnerChange}
                  className={`auth-input ${errors.username ? "input-error" : ""}`}
                  autoComplete="username"
                />
                {errors.username && <p className="form-error">{errors.username}</p>}
              </div>

              <div className="form-field">
                <input
                  type="email"
                  name="email"
                  placeholder="Email Address *"
                  value={learnerForm.email}
                  onChange={handleLearnerChange}
                  className={`auth-input ${errors.email ? "input-error" : ""}`}
                  autoComplete="email"
                />
                {errors.email && <p className="form-error">{errors.email}</p>}
              </div>

              <div className="form-field">
                <PasswordInput
                  name="password"
                  placeholder="Password *"
                  value={learnerForm.password}
                  onChange={handleLearnerChange}
                  error={errors.password}
                  autoComplete="new-password"
                />
                <p className="form-hint">At least 8 characters. Avoid common passwords and personal information.</p>
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
                  placeholder="Confirm Password *"
                  value={learnerForm.confirm_password}
                  onChange={handleLearnerChange}
                  error={errors.confirm_password}
                  autoComplete="new-password"
                />
                {errors.confirm_password && <p className="form-error">{errors.confirm_password}</p>}
              </div>

              <Button
                type="button"
                onClick={() => {
                  if (validateLearnerStep1()) setStep(2);
                }}
              >
                Next: Personal & Academic Details
              </Button>
            </div>
          )}

          {/* STEP 2: Personal & Academic Details */}
          {step === 2 && (
            <form onSubmit={handleLearnerSubmit} className="registration-step">
              <div className="form-field">
                <input
                  type="text"
                  name="first_name"
                  placeholder="First Name *"
                  value={learnerForm.first_name}
                  onChange={handleLearnerChange}
                  className={`auth-input ${errors.first_name ? "input-error" : ""}`}
                  autoComplete="given-name"
                />
                {errors.first_name && <p className="form-error">{errors.first_name}</p>}
              </div>

              <div className="form-field">
                <input
                  type="text"
                  name="last_name"
                  placeholder="Last Name *"
                  value={learnerForm.last_name}
                  onChange={handleLearnerChange}
                  className={`auth-input ${errors.last_name ? "input-error" : ""}`}
                  autoComplete="family-name"
                />
                {errors.last_name && <p className="form-error">{errors.last_name}</p>}
              </div>

              <div className="form-field">
                <input
                  type="text"
                  name="student_id"
                  placeholder="Student ID (Optional)"
                  value={learnerForm.student_id}
                  onChange={handleLearnerChange}
                  className={`auth-input ${errors.student_id ? "input-error" : ""}`}
                  autoComplete="off"
                />
                <p className="form-hint">Optional institutional ID (alphanumeric, 3-30 characters).</p>
                {errors.student_id && <p className="form-error">{errors.student_id}</p>}
              </div>

              {/* Faculty Selection with explicit states */}
              <div className="form-field">
                <label className="form-label" style={{ fontSize: "0.85rem", color: "#475569", marginBottom: "0.35rem" }}>
                  Faculty / Department <span className="optional-badge">(Optional)</span>
                </label>
                <select
                  name="faculty"
                  value={learnerForm.faculty}
                  onChange={handleLearnerChange}
                  className={`auth-select ${errors.faculty ? "input-error" : ""}`}
                  disabled={facultiesLoading}
                >
                  {facultiesLoading ? (
                    <option value="">Loading faculties...</option>
                  ) : facultiesError ? (
                    <option value="">Academic faculties unavailable (Optional)</option>
                  ) : faculties.length === 0 ? (
                    <option value="">No faculties configured (Optional)</option>
                  ) : (
                    <>
                      <option value="">Select Faculty (Optional)</option>
                      {faculties.map((f) => (
                        <option key={f.id} value={f.id}>
                          {f.name}
                        </option>
                      ))}
                    </>
                  )}
                </select>
                {facultiesError && (
                  <p className="form-hint" style={{ color: "#D97706" }}>
                    {facultiesError} You may continue without selecting a faculty.
                  </p>
                )}
                {!facultiesLoading && !facultiesError && faculties.length === 0 && (
                  <p className="form-hint" style={{ color: "#64748B" }}>
                    No academic catalogue is currently configured. You may proceed without choosing a faculty.
                  </p>
                )}
                {errors.faculty && <p className="form-error">{errors.faculty}</p>}
              </div>

              {/* Major Selection with explicit states */}
              <div className="form-field">
                <label className="form-label" style={{ fontSize: "0.85rem", color: "#475569", marginBottom: "0.35rem" }}>
                  Major / Field of Study <span className="optional-badge">(Optional)</span>
                </label>
                <select
                  name="major"
                  value={learnerForm.major}
                  onChange={handleLearnerChange}
                  className={`auth-select ${errors.major ? "input-error" : ""}`}
                  disabled={!learnerForm.faculty || majorsLoading}
                >
                  {!learnerForm.faculty ? (
                    <option value="">Select a faculty first</option>
                  ) : majorsLoading ? (
                    <option value="">Loading majors...</option>
                  ) : majorsError ? (
                    <option value="">Unable to load majors (Optional)</option>
                  ) : majors.length === 0 ? (
                    <option value="">No majors available for this faculty (Optional)</option>
                  ) : (
                    <>
                      <option value="">Select Major (Optional)</option>
                      {majors.map((m) => (
                        <option key={m.id} value={m.id}>
                          {m.name}
                        </option>
                      ))}
                    </>
                  )}
                </select>
                {majorsError && (
                  <p className="form-hint" style={{ color: "#D97706" }}>
                    {majorsError}
                  </p>
                )}
                {errors.major && <p className="form-error">{errors.major}</p>}
              </div>

              <div className="academic-status-banner info">
                Academic information is optional. You can complete registration now and update your profile later.
              </div>

              <div className="button-group" style={{ display: "flex", gap: "0.75rem", marginTop: "1rem" }}>
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => {
                    setStep(1);
                    setErrors({});
                  }}
                >
                  Back
                </Button>
                <Button type="submit" loading={loading}>
                  Register as Learner
                </Button>
              </div>
            </form>
          )}
        </div>
      )}

      {/* Footer navigation */}
      <p className="auth-link" style={{ marginTop: "1.5rem" }}>
        Already have an account? <Link to="/">Login</Link>
      </p>
    </div>
  );
}
