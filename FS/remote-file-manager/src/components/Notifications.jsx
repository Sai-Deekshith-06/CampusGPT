import { useState, useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import "./Notifications.css";

const API = import.meta.env.VITE_API_URL || "http://localhost:3000";

const Notifications = () => {
  const [notifications, setNotifications] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const bellRef = useRef(null);
  const panelRef = useRef(null);

  const fetchNotifications = async () => {
    try {
      const res = await fetch(`${API}/notifications`, { credentials: "include" });
      if (res.ok) {
        const data = await res.json();
        setNotifications(data);
      }
    } catch (err) {
      console.error("Failed to fetch notifications", err);
    }
  };

  useEffect(() => {
    fetchNotifications();

    const url = `${API}/notifications/stream`;
    const source = new EventSource(url, { withCredentials: true });
    
    source.addEventListener("notification", (e) => {
      try {
        const newNotif = JSON.parse(e.data);
        setNotifications(prev => [newNotif, ...prev]);
      } catch (err) {
        console.error(err);
      }
    });

    return () => {
      source.close();
    };
  }, []);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (
        panelRef.current && !panelRef.current.contains(e.target) &&
        bellRef.current && !bellRef.current.contains(e.target)
      ) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isOpen]);

  const handleMarkRead = async (id) => {
    try {
      await fetch(`${API}/notifications/${id}/read`, { method: "POST", credentials: "include" });
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
    } catch (err) {}
  };

  const handleDelete = async (id) => {
    try {
      await fetch(`${API}/notifications/${id}`, { method: "DELETE", credentials: "include" });
      setNotifications(prev => prev.filter(n => n.id !== id));
    } catch (err) {}
  };

  const handleClearRead = async () => {
    try {
      await fetch(`${API}/notifications/read`, { method: "DELETE", credentials: "include" });
      setNotifications(prev => prev.filter(n => !n.is_read));
    } catch (err) {}
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;

  return (
    <div className="notifications-wrapper">
      <button 
        ref={bellRef} 
        className="notifications-bell" 
        onClick={() => setIsOpen(!isOpen)}
        title="Notifications"
      >
        <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
          <path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.89 2 2 2zm6-6v-5c0-3.07-1.64-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.63 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z"/>
        </svg>
        {unreadCount > 0 && <span className="unread-badge">{unreadCount}</span>}
      </button>

      {isOpen && createPortal(
        <div ref={panelRef} className="notifications-panel">
          <div className="notifications-header">
            <h3>Notifications</h3>
            <div className="notifications-header-actions">
              <button onClick={fetchNotifications} className="refresh-notif-btn" title="Refresh Notifications">
                <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="23 4 23 10 17 10"></polyline>
                  <polyline points="1 20 1 14 7 14"></polyline>
                  <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
                </svg>
              </button>
              {unreadCount < notifications.length && (
                <button onClick={handleClearRead} className="clear-read-btn">Clear Read</button>
              )}
            </div>
          </div>
          <div className="notifications-list">
            {notifications.length === 0 ? (
              <div className="no-notifications">No notifications</div>
            ) : (
              notifications.map(n => (
                <div key={n.id} className={`notification-item ${!n.is_read ? 'unread' : ''}`} onClick={() => handleMarkRead(n.id)}>
                  <div className="notification-title">
                    {n.type === "failed" ? "❌ " : (n.type === "completed_with_warnings" ? "⚠️ " : "✅ ")}
                    {n.title}
                  </div>
                  <div className="notification-message">{n.message}</div>
                  <button className="delete-notif-btn" onClick={(e) => { e.stopPropagation(); handleDelete(n.id); }}>×</button>
                </div>
              ))
            )}
          </div>
        </div>,
        document.body
      )}
    </div>
  );
};

export default Notifications;
