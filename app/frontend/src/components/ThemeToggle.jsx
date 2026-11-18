import { useEffect, useState } from "react";
import "../styles.css";

export default function ThemeToggle() {
  const [darkMode, setDarkMode] = useState(false);

  // Load dark mode state on page load
  useEffect(() => {
    const saved = localStorage.getItem("darkMode") === "true";
    setDarkMode(saved);
    document.body.classList.toggle("dark-mode", saved);
  }, []);

  // Update body + save to localStorage when mode changes
  useEffect(() => {
    document.body.classList.toggle("dark-mode", darkMode);
    localStorage.setItem("darkMode", darkMode);
  }, [darkMode]);

  return (
    <div className="theme-toggle-global">
      <button
        className="theme-button"
        onClick={() => setDarkMode(!darkMode)}
      >
        {darkMode ? "☀️ Light Mode" : "🌙 Dark Mode"}
      </button>
    </div>
  );
}
