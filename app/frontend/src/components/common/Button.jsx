import React from 'react';

export default function Button({ 
  children, 
  onClick, 
  type = 'button', 
  variant = 'primary', 
  loading = false, 
  disabled = false,
  fullWidth = false 
}) {
  const baseClass = 'auth-button';
  const variantClass = variant === 'secondary' ? 'auth-button-secondary' : '';
  const widthClass = fullWidth ? 'auth-button-full' : '';
  
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={`${baseClass} ${variantClass} ${widthClass}`.trim()}
    >
      {loading ? 'Loading...' : children}
    </button>
  );
}
