// src/components/Button.jsx
export default function Button({ 
  children, 
  variant = "primary", 
  loading = false, 
  disabled = false,
  type = "button",
  onClick,
  ...props 
}) {
  const className = variant === "secondary" 
    ? "auth-button-secondary" 
    : "auth-button";

  return (
    <button
      type={type}
      className={`${className} ${loading ? 'button-loading' : ''}`}
      disabled={disabled || loading}
      onClick={onClick}
      {...props}
    >
      {loading ? <span className="loading-dots">Loading...</span> : children}
    </button>
  );
}
