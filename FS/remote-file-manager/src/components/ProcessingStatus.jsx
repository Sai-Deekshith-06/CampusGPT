import React from "react";
import "./ProcessingStatus.css";
import { useFileProcessingEvents } from "../hooks/useFileProcessingEvents";

const STAGES = [
  { id: "uploaded", label: "Uploaded" },
  { id: "starting", label: "Start" },
  { id: "conversion", label: "Convert" },
  { id: "classification", label: "Classify" },
  { id: "chunking", label: "Chunk" },
  { id: "extraction", label: "Extract" },
  { id: "completed", label: "Complete" }
];

const ProcessingStatus = ({ file }) => {
  const { status, stage, error, connectionState, isLoading } = useFileProcessingEvents(file);

  const getStageState = (stageId) => {
    // If we're uploaded and pending, we are in the 'uploaded' stage implicitly
    let currentStage = stage || "uploaded";
    if (status === "pending" && currentStage === "unknown") currentStage = "uploaded";
    
    // Treat "completed" as special stage mapping
    if (status === "completed" || status === "completed_with_warnings") {
      currentStage = "completed";
    }

    const stageIndex = STAGES.findIndex(s => s.id === currentStage);
    const checkIndex = STAGES.findIndex(s => s.id === stageId);
    
    if (checkIndex < stageIndex) return "passed";
    if (checkIndex === stageIndex) {
      if (status === "failed" || status === "registration_failed") return "failed";
      if (status === "completed" || status === "completed_with_warnings") return "passed";
      return "active";
    }
    return "pending";
  };

  const getBadge = () => {
    if (status === "completed") return <span className="badge badge-success" title="Processing Completed Successfully">Completed</span>;
    if (status === "completed_with_warnings") return <span className="badge badge-warning" title={error || "Completed with warnings"}>Completed (Warnings)</span>;
    if (status === "failed") return <span className="badge badge-danger" title={error || "Processing failed"}>Failed</span>;
    if (status === "registration_failed") return <span className="badge badge-danger" title={error || "Registration failed"}>Registration Failed</span>;
    if (status === "running" || status === "converting" || status === "pending" || status === "processing") {
      return (
        <span className="badge badge-primary">
          {status === "pending" ? "Pending..." : "Processing..."} 
          {connectionState === "disconnected" && " (Disconnected)"}
        </span>
      );
    }
    if (status === "disconnected") return <span className="badge badge-secondary">Disconnected</span>;
    return <span className="badge badge-secondary">Not Started</span>;
  };

  if (file.isDirectory) {
    return <div className="processing-status-empty">-</div>;
  }

  if (isLoading) {
    return (
      <div className="processing-status-container" style={{ justifyContent: "flex-start", paddingLeft: "10px" }}>
        <div className="loading-spinner" style={{ width: "16px", height: "16px", border: "2px solid #e2e8f0", borderTop: "2px solid #3b82f6", borderRadius: "50%", animation: "spin 1s linear infinite" }}></div>
        <span style={{ marginLeft: "8px", color: "#64748b", fontSize: "13px" }}>Verifying status...</span>
        <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  return (
    <div className="processing-status-container">
      {(status === "not_started" || !status || !file.campusgpt_job_id) && status !== "registration_failed" ? (
        <div className="badge-container" style={{ margin: 0, paddingLeft: "10px" }}>
          {getBadge()}
        </div>
      ) : (
        <>
          <div className="stepper">
            {STAGES.map((s, index) => {
              const state = getStageState(s.id);
              return (
                <React.Fragment key={s.id}>
                  <div className={`step step-${state}`}>
                    <div className="step-circle" title={state === "failed" ? error : ""}>
                      {state === "passed" ? (
                        <svg viewBox="0 0 24 24" width="12" height="12" stroke="currentColor" strokeWidth="3" fill="none" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
                      ) : state === "failed" ? (
                        <svg viewBox="0 0 24 24" width="12" height="12" stroke="currentColor" strokeWidth="3" fill="none" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                      ) : state === "active" ? (
                        <div className="active-dot"></div>
                      ) : null}
                    </div>
                    <div className="step-label">{s.label}</div>
                  </div>
                  {index < STAGES.length - 1 && (
                    <div className={`step-connector ${getStageState(STAGES[index + 1].id) !== "pending" ? "connected" : ""}`}></div>
                  )}
                </React.Fragment>
              );
            })}
          </div>
          <div className="badge-container" title={error || ""}>
            {getBadge()}
          </div>
        </>
      )}
    </div>
  );
};

export default ProcessingStatus;
