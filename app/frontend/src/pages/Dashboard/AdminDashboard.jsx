// src/pages/Dashboard/AdminDashboard.jsx

export default function AdminDashboard({ profile }) {
  return (
    <div>
      <h2 className="section-title">System Administration</h2>
      <p className="auth-message success">Hello {profile.first_name}. Manage users & reports.</p>
      <div className="admin-section">
        <div className="admin-card">
          <h3>User Management</h3>
          <p>View, approve, and update accounts.</p>
        </div>
        <div className="admin-card">
          <h3>System Reports</h3>
          <p>Monitor booking activity & coach performance.</p>
        </div>
      </div>
    </div>
  );
}
