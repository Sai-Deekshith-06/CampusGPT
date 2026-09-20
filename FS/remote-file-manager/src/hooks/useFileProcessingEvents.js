import { useState, useEffect, useRef } from 'react';

const API = import.meta.env.VITE_API_URL || "http://localhost:3000";
const TERMINAL_STATES = ["completed", "completed_with_warnings", "failed", "registration_failed"];

export function useFileProcessingEvents(file) {
  const [status, setStatus] = useState(file?.processing_status || "not_started");
  const [stage, setStage] = useState(file?.processing_stage || "unknown");
  const [error, setError] = useState(file?.processing_error || null);
  const [connectionState, setConnectionState] = useState("idle");
  const [reconnectCounter, setReconnectCounter] = useState(0);
  const [isLoading, setIsLoading] = useState(true); // Loading on mount
  
  const statusRef = useRef(status);
  
  useEffect(() => {
    statusRef.current = status;
  }, [status]);

  const prevStatusProp = useRef(file?.processing_status);
  const prevStageProp = useRef(file?.processing_stage);
  const prevErrorProp = useRef(file?.processing_error);

  // Sync state ONLY if the prop itself has changed from its previous value
  useEffect(() => {
    if (file?.processing_status && file.processing_status !== prevStatusProp.current) {
        prevStatusProp.current = file.processing_status;
        setStatus(file.processing_status);
    }
    if (file?.processing_stage && file.processing_stage !== prevStageProp.current) {
        prevStageProp.current = file.processing_stage;
        setStage(file.processing_stage);
    }
    if (file?.processing_error && file.processing_error !== prevErrorProp.current) {
        prevErrorProp.current = file.processing_error;
        setError(file.processing_error);
    }
  }, [file?.processing_status, file?.processing_stage, file?.processing_error]);

  useEffect(() => {
    const currentStatus = statusRef.current;
    
    if (!file?.campusgpt_job_id) {
        setIsLoading(false);
        return;
    }
    
    let source = null;
    let isCancelled = false;

    const connect = async () => {
      // ALWAYS reconcile state first before relying on anything
      try {
        const res = await fetch(`${API}/files/processing-status?path=${encodeURIComponent(file.path)}`, { credentials: "include" });
        if (res.ok) {
          const data = await res.json();
          if (!isCancelled) {
              if (data.processing_status) {
                setStatus(data.processing_status);
                statusRef.current = data.processing_status;
                window.dispatchEvent(new CustomEvent('file-status-update', { 
                  detail: { path: file.path, status: data.processing_status, hasJob: !!data.campusgpt_job_id }
                }));
              }
              if (data.processing_stage) setStage(data.processing_stage);
              if (data.processing_error) setError(data.processing_error);
          }
        }
      } catch (e) {
        console.error("Status fetch failed", e);
      }
      
      if (!isCancelled) {
          setIsLoading(false);
      }

      if (isCancelled || TERMINAL_STATES.includes(statusRef.current)) {
          setConnectionState("disconnected");
          return;
      }

      const url = `${API}/files/processing-events?path=${encodeURIComponent(file.path)}`;
      source = new EventSource(url, { withCredentials: true });
      setConnectionState(reconnectCounter > 0 ? "reconnecting" : "connecting");

      source.onopen = () => {
        setConnectionState("connected");
      };

      const handleEvent = (e) => {
        try {
          const data = JSON.parse(e.data);
          if (data.status) {
              setStatus(data.status);
              window.dispatchEvent(new CustomEvent('file-status-update', { 
                  detail: { path: file.path, status: data.status, hasJob: true }
              }));
          }
          if (data.stage) setStage(data.stage);
          if (data.error_message || data.error) setError(data.error_message || data.error);
          if (data.errors && data.errors.length > 0) setError(data.errors.join(", "));
          
          if (data.status && TERMINAL_STATES.includes(data.status)) {
            source.close();
            setConnectionState("disconnected");
          }
        } catch (err) {
          console.error("Failed to parse SSE event", err);
        }
      };

      source.addEventListener("processing_status", handleEvent);
      source.addEventListener("processing_stage", handleEvent);
      
      source.onerror = (e) => {
        // Transport error / Proxy timeout. Do NOT set processing status to failed.
        source.close();
        if (!TERMINAL_STATES.includes(statusRef.current) && reconnectCounter < 5) {
           setConnectionState("disconnected");
           if (!isCancelled) {
             // trigger reconnect
             setTimeout(() => {
               if (!isCancelled) setReconnectCounter(c => c + 1);
             }, 2000);
           }
        } else {
           setConnectionState("disconnected");
        }
      };
    };

    connect();

    return () => {
      isCancelled = true;
      if (source) source.close();
      setConnectionState("idle");
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [file?.path, file?.campusgpt_job_id, reconnectCounter]); 

  return { status, stage, error, connectionState, isLoading };
}
