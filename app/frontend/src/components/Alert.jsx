// src/components/Alert.jsx
export default function Alert({ type = "info", children, onClose }) {
  const typeClass = {
    success: "alert-success",
    error: "alert-error",
    info: "alert-info",
    warning: "alert-warning"
  }[type] || "alert-info";

  return (
    <div className={`alert ${typeClass}`} role="alert">
      <div className="alert-content">{children}</div>
      {onClose && (
        <button className="alert-close" onClick={onClose} aria-label="Close">
          ×
        </button>
      )}
    </div>
  );
}
