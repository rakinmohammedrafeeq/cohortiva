// src/pages/Dashboard/StudentDashboard.jsx
import { useState, useEffect } from "react";
import authService from "../../services/authService";

export default function StudentDashboard({ profile }) {
  const [tutors, setTutors] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    authService.getTutors()
      .then(data => setTutors(data))
      .finally(()=>setLoading(false));
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("token");
    window.location.href = "/";
  };

  return (
    <div>
      <h2 className="section-title">Available Coaches</h2>
      <p className="auth-message">Hello {profile.first_name}. You can book coaching sessions below.</p>
      {loading && <div className="loading-block">Loading coaches...</div>}
      {!loading && tutors.length === 0 && <div className="panel"><p>No coaches available at the moment.</p></div>}
      <div className="tutor-grid">
        {tutors.map((tutor) => (
          <div key={tutor.id || tutor.username} className="tutor-card">
            <h3>{tutor.name || tutor.username}</h3>
            <p>Subject: {tutor.subject || tutor.major || "—"}</p>
            <p>Slots: {Array.isArray(tutor.available_slots) ? tutor.available_slots.join(", ") : "—"}</p>
            <button className="auth-button">Book Session</button>
          </div>
        ))}
      </div>
    </div>
  );
}
