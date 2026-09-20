import { useState, useEffect } from "react";
import "./Actions.css";

const API = import.meta.env.VITE_API_URL || "http://localhost:3000";

const Actions = ({ file, onRefresh }) => {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(file.processing_status || "not_started");
  const [hasJob, setHasJob] = useState(!!file.campusgpt_job_id);

  useEffect(() => {
    setStatus(file.processing_status || "not_started");
    setHasJob(!!file.campusgpt_job_id);
  }, [file.processing_status, file.campusgpt_job_id]);
  useEffect(() => {
    const handleUpdate = (e) => {
      if (e.detail.path === file.path) {
        setStatus(e.detail.status);
        if (e.detail.hasJob !== undefined) {
          setHasJob(e.detail.hasJob);
        }
      }
    };
    window.addEventListener('file-status-update', handleUpdate);
    return () => window.removeEventListener('file-status-update', handleUpdate);
  }, [file.path]);

  if (file.isDirectory) return null;

  const handleAction = async (endpoint) => {
    try {
      setLoading(true);
      const res = await fetch(`${API}/files/${endpoint}?path=${encodeURIComponent(file.path)}`, {
        method: "POST",
        credentials: "include"
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Action failed");
      }
      if (onRefresh) onRefresh();
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  let actionButton = null;
  if (["pending", "running", "processing"].includes(status)) {
    actionButton = (
      <button className="action-btn" disabled title="Processing">
        Processing...
      </button>
    );
  } else if (["completed", "completed_with_warnings"].includes(status)) {
    actionButton = (
      <button className="action-btn play-btn" disabled={loading} onClick={() => handleAction("retry")} title="Reprocess">
        Reprocess
      </button>
    );
  } else if (["failed", "registration_failed"].includes(status)) {
    actionButton = (
      <button className="action-btn play-btn" disabled={loading} onClick={() => handleAction(hasJob ? "retry" : "process")} title="Retry">
        Retry
      </button>
    );
  } else {
    // not_started or unknown
    actionButton = (
      <button className="action-btn play-btn" disabled={loading || !hasJob} onClick={() => handleAction("process")} title="Process">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
      </button>
    );
  }

  return (
    <div className="custom-actions-container">
      {actionButton}
    </div>
  );
};

export default Actions;
