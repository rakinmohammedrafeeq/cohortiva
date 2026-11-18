import { useEffect, useState, useMemo } from "react";
import authService from "../../services/authService";

const dayMap = ["sunday","monday","tuesday","wednesday","thursday","friday","saturday"];

export default function BookMeeting({ profile }) {
  const [tutors, setTutors] = useState([]);
  const [loadingTutors, setLoadingTutors] = useState(true);
  const [selectedTutor, setSelectedTutor] = useState("");
  const [date, setDate] = useState("");
  const [mode, setMode] = useState("offline");
  const [location, setLocation] = useState("");
  const [slot, setSlot] = useState("");
  const [status, setStatus] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    authService.getTutors()
      .then(data => setTutors(data))
      .finally(() => setLoadingTutors(false));
  }, []);

  const selectedTutorObj = useMemo(
    () => tutors.find(t => String(t.id) === String(selectedTutor)),
    [selectedTutor, tutors]
  );

  const dayKey = useMemo(() => {
    if (!date) return null;
    const d = new Date(date + "T00:00:00");
    return dayMap[d.getDay()];
  }, [date]);

  const availableSlots = useMemo(() => {
    if (!selectedTutorObj || !dayKey) return [];
    const avail = selectedTutorObj.availability || {};
    const arr = avail[dayKey] || [];
    return Array.isArray(arr) ? arr : [];
  }, [selectedTutorObj, dayKey]);

  // helper: today in YYYY-MM-DD
  const todayStr = useMemo(() => {
    const d = new Date();
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    return `${yyyy}-${mm}-${dd}`;
  }, []);

  // Disallow past date
  const isPastDate = useMemo(() => {
    if (!date) return false;
    return new Date(date + "T00:00:00") < new Date(todayStr + "T00:00:00");
  }, [date, todayStr]);

  const hasRequired = selectedTutor && date && slot && mode && !isPastDate;
  const canSubmit = hasRequired && !submitting;

  const handleBook = async () => {
    if (!hasRequired) {
      if (isPastDate) {
        setStatus("Cannot book sessions for past dates.");
        return;
      }
      const missing = [];
      if (!selectedTutor) missing.push("select a coach");
      if (!date) missing.push("select a date");
      if (!slot) missing.push("select a time slot");
      setStatus(`Please ${missing.join(", ")} before booking.`);
      return;
    }
    setSubmitting(true);
    setStatus("");
    try {
      // slot format "HH:MM-HH:MM"
      const [startTimeRaw, endTimeRaw] = slot.split("-");
      const startISO = new Date(date + "T" + startTimeRaw + ":00").toISOString();
      const endISO = new Date(date + "T" + endTimeRaw + ":00").toISOString();
      const payload = {
        tutor: selectedTutor,
        // student: BE will auto-assign (student read_only in serializer)
        start_time: startISO,
        end_time: endISO,
        mode,
        location: mode === "offline" ? location || null : null
      };
      await authService.createSession(payload);
      setStatus("Session booked successfully.");
      setTutors(prev =>
        prev.map(t => {
          if (String(t.id) !== String(selectedTutor) || !t.availability) return t;
          const nextAvail = { ...t.availability };
          const list = Array.isArray(nextAvail[dayKey]) ? [...nextAvail[dayKey]] : [];
          const idx = list.indexOf(slot);
          if (idx !== -1) list.splice(idx, 1);
          if (list.length) {
            nextAvail[dayKey] = list;
          } else {
            delete nextAvail[dayKey];
          }
          return { ...t, availability: nextAvail };
        })
      );
      setSlot("");
    } catch (e) {
      const resp = e?.response?.data;
      let msg = "";
      if (resp) {
        if (typeof resp === "string") msg = resp;
        else if (resp.detail) msg = resp.detail;
        else if (Array.isArray(resp.non_field_errors)) msg = resp.non_field_errors.join(" ");
        else if (resp.non_field_errors) msg = String(resp.non_field_errors);
      }
      setStatus(msg || "Failed to book session.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="panel booking-panel">
      <h3 className="section-title">Book a Coaching Session</h3>
      <p className="small-note">
        Select a coach, date, and an available time slot from the coach's availability.
      </p>
      {status && (
        <p className={`auth-message ${status.includes("successfully") ? "success" : "error"}`}>
          {status}
        </p>
      )}
      {loadingTutors && <p>Loading coaches...</p>}
      {!loadingTutors && tutors.length === 0 && <p>No coaches available.</p>}

      <div className="booking-form">
        <label>
          Coach
          <select
            className="inline-select"
            value={selectedTutor}
            onChange={e => { setSelectedTutor(e.target.value); setSlot(""); }}
          >
            <option value="">-- Select Coach --</option>
            {tutors.map(t => {
              const label = t.name || t.username || `Coach #${t.id}`;
              return (
                <option key={t.id} value={t.id}>
                  {label}
                </option>
              );
            })}
          </select>
        </label>

        {selectedTutorObj && (
          <div className="coach-details" style={{ 
            marginTop: ".5rem", 
            padding: ".8rem", 
            background: "var(--panel-bg, #f9f9f9)", 
            borderRadius: "4px",
            fontSize: ".9rem"
          }}>
            <h4 style={{ marginTop: 0, marginBottom: ".5rem", fontSize: "1rem" }}>
              {selectedTutorObj.name || `Coach #${selectedTutorObj.id}`}
            </h4>
            {selectedTutorObj.expertise && (
              <p style={{ margin: ".3rem 0" }}>
                <strong>Expertise:</strong> {selectedTutorObj.expertise}
              </p>
            )}
            {selectedTutorObj.bio && (
              <p style={{ margin: ".3rem 0" }}>
                <strong>Bio:</strong> {selectedTutorObj.bio}
              </p>
            )}
          </div>
        )}

        <label>
          Date
          <input
            type="date"
            className="inline-input"
            value={date}
            min={todayStr}
            onChange={e => { setDate(e.target.value); setSlot(""); }}
          />
        </label>

        <label>
          Time Slot
          <select
            className="inline-select"
            value={slot}
            onChange={e => {
              setSlot(e.target.value);
              if (status) setStatus("");
            }}
            disabled={!availableSlots.length}
          >
            <option value="">
              {selectedTutor && date
                ? availableSlots.length
                  ? "-- Select Time Slot --"
                  : "No slots available"
                : "Select coach & date first"}
            </option>
            {availableSlots.map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </label>

        <label>
          Mode
          <select
            className="inline-select"
            value={mode}
            onChange={e => setMode(e.target.value)}
          >
            <option value="offline">Offline</option>
            <option value="online">Online</option>
          </select>
        </label>

        {mode === "offline" && (
          <label>
            Location (optional)
            <input
              type="text"
              className="inline-input"
              placeholder="e.g., Room B203"
              value={location}
              onChange={e => setLocation(e.target.value)}
            />
          </label>
        )}

        <div className="booking-actions">
          <button
            type="button"
            className="auth-button"
            disabled={submitting}
            onClick={handleBook}
            style={{ maxWidth: "170px" }}
          >
            {submitting ? "Booking..." : "Book Session"}
          </button>
        </div>
      </div>

      {selectedTutorObj && date && (
        <div className="small-note" style={{ marginTop: ".8rem" }}>
          {date} is a {dayKey || "?"}. Slots shown are based on coach availability.
        </div>
      )}

      {selectedTutorObj && date && isPastDate && (
        <div className="auth-message error" style={{ marginTop: ".5rem" }}>
          Cannot book sessions for past dates.
        </div>
      )}
    </div>
  );
}