import React from 'react';

export default function Spinner() {
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      padding: '2rem'
    }}>
      <div style={{
        border: '4px solid #f3f3f3',
        borderTop: '4px solid #1a90f8',
        borderRadius: '50%',
        width: '40px',
        height: '40px',
        animation: 'spin 1s linear infinite'
      }}></div>
    </div>
  );
}
