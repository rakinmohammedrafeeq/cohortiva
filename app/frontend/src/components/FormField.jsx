// src/components/FormField.jsx
export default function FormField({ label, error, children }) {
  return (
    <div className="form-field">
      {label && <label className="form-label">{label}</label>}
      {children}
      {error && <p className="form-error">{error}</p>}
    </div>
  );
}
