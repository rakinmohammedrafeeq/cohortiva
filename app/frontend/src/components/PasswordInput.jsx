// src/components/PasswordInput.jsx
import { useState } from "react";

export default function PasswordInput({ value, onChange, placeholder, name, error, autoComplete = "off" }) {
  const [showPassword, setShowPassword] = useState(false);

  return (
    <div className="password-input-wrapper">
      <input
        type={showPassword ? "text" : "password"}
        name={name}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        className={`auth-input ${error ? 'input-error' : ''}`}
        autoComplete={autoComplete}
      />
      <button
        type="button"
        className="password-toggle"
        onClick={() => setShowPassword(!showPassword)}
        aria-label={showPassword ? "Hide password" : "Show password"}
      >
        {showPassword ? "👁️" : "👁️‍🗨️"}
      </button>
    </div>
  );
}
