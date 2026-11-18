import { useEffect, useState, useCallback } from "react";
import authService from "../../services/authService";

export default function GenerateReport({ profile }) {
  const isAdmin = (profile?.role_name || profile?.role || "").toString().toLowerCase() === "admin";
  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState(null);
  const [error, setError] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await authService.getReportOverview({ from, to });
      setOverview(data || {});
    } catch {
      setError("Failed to load report.");
    } finally {
      setLoading(false);
    }
  }, [from, to]);

  useEffect(() => { load(); }, [load]);

  if (!isAdmin) {
    return (
      <div className="panel">
        <h3 className="section-title">Reports</h3>
        <p className="empty-info">Only admins can view comprehensive reports.</p>
      </div>
    );
  }

  const sessions = overview?.sessions || {};
  const completed = sessions.completed || 0;
  const total = sessions.total || (completed + (sessions.cancelled || 0) + (sessions.scheduled || 0));
  const completionRate = total ? ((completed / total) * 100).toFixed(1) : "0.0";

  const feedback = overview?.feedback || {};
  const avgRating = feedback.average_rating ?? (feedback.count ? (feedback.sum_rating / feedback.count).toFixed(2) : "—");
  const dist = feedback.distribution || {};
  const tutors = Array.isArray(overview?.tutors) ? overview.tutors : [];

  return (
    <div className="panel report-panel">
      <h3 className="section-title">System Reports</h3>
      <p className="small-note">Analytics to support decision-making (attendance & feedback).</p>
      <div className="report-filters">
        <label>
          From Date
          <input
            type="date"
            className="inline-input"
            value={from}
            onChange={e => setFrom(e.target.value)}
          />
        </label>
        <label>
          To Date
          <input
            type="date"
            className="inline-input"
            value={to}
            onChange={e => setTo(e.target.value)}
          />
        </label>
        <button
          type="button"
          className="auth-button"
          disabled={refreshing || loading}
          onClick={async () => {
            setRefreshing(true);
            await load();
            setRefreshing(false);
          }}
          style={{ maxWidth: "160px" }}
        >
          {refreshing ? "Loading..." : "Refresh"}
        </button>
      </div>

      {error && <p className="auth-message error">{error}</p>}
      {loading && <p>Loading report...</p>}
      {!loading && !error && (
        <div className="report-grid">
          <div className="report-card">
            <h4>Sessions</h4>
            <ul className="stat-list">
              <li>Total: {total}</li>
              <li>Completed: {completed}</li>
              <li>Cancelled: {sessions.cancelled || 0}</li>
              <li>Scheduled: {sessions.scheduled || 0}</li>
              <li>Completion Rate: {completionRate}%</li>
            </ul>
          </div>
          <div className="report-card">
            <h4>Feedback</h4>
            <ul className="stat-list">
              <li>Count: {feedback.count || 0}</li>
              <li>Avg Rating: {avgRating || "—"}</li>
            </ul>
            <div className="rating-dist">
              {[1,2,3,4,5].map(r => {
                const val = dist[r] || 0;
                const percent = feedback.count ? ((val / feedback.count) * 100) : 0;
                return (
                  <div key={r} className="rating-row">
                    <span className="r-label">{r}★</span>
                    <div className="r-bar-wrap">
                      <div className="r-bar" style={{ width: `${percent}%` }} />
                    </div>
                    <span className="r-val">{val}</span>
                  </div>
                );
              })}
            </div>
          </div>
          <div className="report-card" style={{ gridColumn: "1 / -1" }}>
            <h4>Top Coaches (Completed Sessions)</h4>
            {tutors.length === 0 && <p className="empty-info">No coach data available.</p>}
            <div className="tutor-rank-list">
              {tutors.slice(0, 8).map(t => (
                <div key={t.id} className="tutor-rank-item">
                  <span className="t-name">{t.name || t.id}</span>
                  <span className="t-completed">Completed: {t.completed_sessions ?? t.completed ?? 0}</span>
                  <span className="t-rating">Avg ★ {t.avg_rating ?? "—"}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}