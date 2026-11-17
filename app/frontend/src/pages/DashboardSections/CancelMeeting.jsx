import { useEffect, useState, useCallback, useMemo } from "react";
import { useLocation } from "react-router-dom";
import authService from "../../services/authService";

export default function CancelMeeting({ profile, roleName }) {
  const location = useLocation();
  const inCancelPage = location.pathname.endsWith("/cancel");
  const roleLower = (roleName || profile?.role_name || "").toString().toLowerCase();
  const isAdmin = roleLower === "admin";
  const isTutor = roleLower === "tutor";

  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [cancelingId, setCancelingId] = useState(null);
  const [reasons, setReasons] = useState({}); // { [id]: reason }
  const [myTutorId, setMyTutorId] = useState(null);
  const [myTutorLoading, setMyTutorLoading] = useState(false);

  useEffect(() => {
    if (!isTutor) {
      setMyTutorId(null);
      setMyTutorLoading(false);
      return;
    }
    setMyTutorLoading(true);
    authService
      .getMyTutor()
      .then((data) => setMyTutorId(data?.id ?? null))
      .catch(() => setMyTutorId(null))
      .finally(() => setMyTutorLoading(false));
  }, [isTutor]);

  const load = useCallback(() => {
    setLoading(true);
    setError("");
    authService.getSessions()
      .then(data => setSessions(Array.isArray(data) ? data : []))
      .catch(() => setError("Không tải được danh sách phiên."))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const sessionsVisible = useMemo(() => {
    if (isAdmin) return sessions;
    if (isTutor) {
      if (!myTutorId) return [];
      return sessions.filter(s => String(s.tutor) === String(myTutorId));
    }
    return sessions;
  }, [sessions, isAdmin, isTutor, myTutorId]);

  const sessionLoading = loading || (isTutor && myTutorLoading);

  const now = new Date();
  const statusLabel = (status) => {
    switch ((status || "").toLowerCase()) {
      case "scheduled": return "Đã lên lịch";
      case "ongoing": return "Đang diễn ra";
      case "completed": return "Đã hoàn thành";
      case "cancelled": return "Đã hủy";
      default: return status || "—";
    }
  };

  const upcoming = sessionsVisible
    .filter(s => s.status === "scheduled")
    .sort((a, b) => new Date(a.start_time) - new Date(b.start_time));

  const ongoing = sessionsVisible
    .filter(s => s.status === "ongoing")
    .sort((a, b) => new Date(a.start_time) - new Date(b.start_time));

  const completed = sessionsVisible
    .filter(s => s.status === "completed")
    .sort((a, b) => new Date(b.start_time) - new Date(a.start_time));

  const fmt = (dt) => {
    try { return new Date(dt).toLocaleString("vi-VN", { hour12: false }); }
    catch { return dt; }
  };

  const handleCancel = async (id) => {
    const reasonRaw = reasons[id];
    const trimmed = typeof reasonRaw === "string" ? reasonRaw.trim() : "";
    if (!isAdmin && !trimmed) {
      setMessage("Vui lòng nhập lý do hủy lịch.");
      return;
    }
    setCancelingId(id);
    setMessage("");
    try {
      if (isAdmin) {
        await authService.deleteSession(id);
        setSessions(prev => prev.filter(s => s.id !== id));
        setMessage("Xóa lịch thành công.");
      } else {
        await authService.cancelSession(id, trimmed);
        setSessions(prev => prev.map(s => s.id === id ? { ...s, status: "cancelled" } : s));
        setMessage("Hủy lịch thành công.");
        setReasons(prev => ({ ...prev, [id]: "" }));
      }
    } catch {
      setMessage(isAdmin ? "Xóa lịch thất bại." : "Hủy lịch thất bại.");
    } finally {
      setCancelingId(null);
    }
  };

  return (
    <div className="panel cancel-panel">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h3 className="section-title">{inCancelPage ? (isAdmin ? "Delete Sessions" : "Cancel Sessions") : "Schedule"}</h3>
      </div>
      <p className="small-note">
        {isAdmin ? "Admins can delete any session directly (including past sessions)." : "View and cancel booked sessions (cancellation reason required)."}
      </p>
      {message && (
        <p className={`auth-message ${message.includes("thành công") ? "success" : "error"}`}>
          {message}
        </p>
      )}
      {error && <p className="auth-message error">{error}</p>}
      {sessionLoading && <p>Loading...</p>}

      {!sessionLoading && (
        <>
          <div className="session-list">
            <div className="section-title" style={{ fontSize: ".95rem" }}>Upcoming Sessions</div>
            {upcoming.length === 0 && <p className="empty-info">No upcoming sessions.</p>}
            {upcoming.map(s => (
              <div key={s.id} className="session-item">
                <div className="session-times">
                  <strong>{fmt(s.start_time)}</strong>
                  <span>→ {fmt(s.end_time)}</span>
                </div>
                <div className="session-meta">
                  <span>Learner: {s.student_name || s.student_username || s.student}</span>
                  <span>Coach: {s.tutor}</span>
                  <span>Mode: {s.mode}</span>
                  {s.location && <span>Location: {s.location}</span>}
                  <span>Status: {statusLabel(s.status)}</span>
                </div>
                <div className="session-actions" style={{ gap: ".5rem", alignItems: "center" }}>
                  {!isAdmin && (
                    <input
                      type="text"
                      className="inline-input"
                      placeholder="Cancellation reason..."
                      value={reasons[s.id] || ""}
                      onChange={e => setReasons(prev => ({ ...prev, [s.id]: e.target.value }))}
                      style={{ flex: "1 1 auto", minWidth: "200px" }}
                    />
                  )}
                  <button
                    type="button"
                    className="mini-cancel-btn"
                    disabled={cancelingId === s.id}
                    onClick={() => handleCancel(s.id)}
                  >
                    {cancelingId === s.id ? (isAdmin ? "Deleting..." : "Canceling...") : (isAdmin ? "Delete" : "Cancel")}
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div className="session-list" style={{ marginTop: ".9rem" }}>
            <div className="section-title" style={{ fontSize: ".95rem" }}>Ongoing Sessions</div>
            {ongoing.length === 0 && <p className="empty-info">No ongoing sessions.</p>}
            {ongoing.map(s => (
              <div key={s.id} className="session-item">
                <div className="session-times">
                  <strong>{fmt(s.start_time)}</strong>
                  <span>→ {fmt(s.end_time)}</span>
                </div>
                <div className="session-meta">
                  <span>Learner: {s.student_name || s.student_username || s.student}</span>
                  <span>Coach: {s.tutor}</span>
                  <span>Mode: {s.mode}</span>
                  {s.location && <span>Location: {s.location}</span>}
                  <span>Status: {statusLabel(s.status)}</span>
                </div>
                {isAdmin && (
                  <div className="session-actions" style={{ gap: ".5rem", alignItems: "center" }}>
                    <button
                      type="button"
                      className="mini-cancel-btn"
                      disabled={cancelingId === s.id}
                      onClick={() => handleCancel(s.id)}
                    >
                      {cancelingId === s.id ? "Deleting..." : "Delete"}
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>

          <div className="session-list" style={{ marginTop: ".9rem" }}>
            <div className="section-title" style={{ fontSize: ".95rem" }}>Completed Sessions</div>
            {completed.length === 0 && <p className="empty-info">No completed sessions yet.</p>}
            {completed.map(s => (
              <div key={s.id} className="session-item">
                <div className="session-times">
                  <strong>{fmt(s.start_time)}</strong>
                  <span>→ {fmt(s.end_time)}</span>
                </div>
                <div className="session-meta">
                  <span>Learner: {s.student_name || s.student_username || s.student}</span>
                  <span>Coach: {s.tutor}</span>
                  <span>Mode: {s.mode}</span>
                  {s.location && <span>Location: {s.location}</span>}
                  <span>Status: {statusLabel(s.status)}</span>
                </div>
                {isAdmin && (
                  <div className="session-actions" style={{ gap: ".5rem", alignItems: "center" }}>
                    <button
                      type="button"
                      className="mini-cancel-btn"
                      disabled={cancelingId === s.id}
                      onClick={() => handleCancel(s.id)}
                    >
                      {cancelingId === s.id ? "Deleting..." : "Delete"}
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </>
      )}

      <div style={{ marginTop: ".75rem", textAlign: "right" }}>
        <button
          type="button"
          className="mini-refresh-btn"
          onClick={load}
          disabled={sessionLoading}
        >
          Refresh
        </button>
      </div>
    </div>
  );
}