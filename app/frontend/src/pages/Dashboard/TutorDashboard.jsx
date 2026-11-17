// src/pages/Dashboard/TutorDashboard.jsx

export default function TutorDashboard({ profile }) {
  return (
    <div>
      <h2 className="section-title">Coach Dashboard</h2>
      <p className="auth-message">Welcome {profile.first_name}, manage your schedule and learners.</p>
      <div className="tutor-section">
        <div className="tutor-box">
          <h3>My Schedule</h3>
          <p>Update your availability so learners can book sessions.</p>
        </div>
        <div className="tutor-box">
          <h3>Learners</h3>
          <p>View the list of booked sessions.</p>
        </div>
      </div>
    </div>
  );
}
