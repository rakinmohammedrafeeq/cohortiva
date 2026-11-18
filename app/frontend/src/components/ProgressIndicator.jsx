// src/components/ProgressIndicator.jsx
export default function ProgressIndicator({ currentStep, totalSteps }) {
  return (
    <div className="progress-indicator">
      <div className="progress-bar">
        <div 
          className="progress-fill" 
          style={{ width: `${(currentStep / totalSteps) * 100}%` }}
        />
      </div>
      <p className="progress-text">
        Step {currentStep} of {totalSteps}
      </p>
    </div>
  );
}
