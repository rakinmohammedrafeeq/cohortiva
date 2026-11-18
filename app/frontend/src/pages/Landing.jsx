// src/pages/Landing.jsx
import { Link } from "react-router-dom";
import "../styles.css";

export default function Landing() {
  return (
    <div className="landing-container">
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content">
          <h1 className="hero-title">
            Welcome to <span className="brand-name">Cohortiva</span>
          </h1>
          <p className="hero-subtitle">
            Connect with expert coaches, book personalized learning sessions, and accelerate your academic journey.
          </p>
          <div className="hero-cta">
            <Link to="/register" className="cta-button primary">
              Get Started as Learner
            </Link>
            <Link to="/apply-coach" className="cta-button secondary">
              Apply as Coach
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features-section">
        <h2 className="section-heading">Why Choose Cohortiva?</h2>
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">📚</div>
            <h3 className="feature-title">Expert Coaching</h3>
            <p className="feature-description">
              Connect with qualified coaches who bring real-world experience and proven teaching expertise.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">📅</div>
            <h3 className="feature-title">Flexible Scheduling</h3>
            <p className="feature-description">
              Book sessions at times that work for you. View real-time availability and schedule instantly.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">💡</div>
            <h3 className="feature-title">Personalized Learning</h3>
            <p className="feature-description">
              Get one-on-one attention tailored to your learning style, pace, and academic goals.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">⭐</div>
            <h3 className="feature-title">Quality Feedback</h3>
            <p className="feature-description">
              Rate your sessions and provide feedback to help maintain high-quality coaching standards.
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <p>
          Already have an account?{" "}
          <Link to="/login" className="footer-link">
            Login here
          </Link>
        </p>
      </footer>
    </div>
  );
}
