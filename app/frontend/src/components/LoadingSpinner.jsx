// src/components/LoadingSpinner.jsx
export default function LoadingSpinner({ size = "medium" }) {
  return (
    <div className={`spinner spinner-${size}`}>
      <div className="spinner-circle"></div>
    </div>
  );
}
