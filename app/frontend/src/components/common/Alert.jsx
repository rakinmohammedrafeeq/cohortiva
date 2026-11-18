import React from 'react';

export default function Alert({ type = 'info', message }) {
  if (!message) return null;
  
  const className = type === 'error' ? 'auth-error' : 'auth-success';
  
  return (
    <div className={className}>
      {message}
    </div>
  );
}
