// src/components/Input.jsx
export default function Input({ error, ...props }) {
  return (
    <input
      className={`auth-input ${error ? 'input-error' : ''}`}
      {...props}
    />
  );
}
