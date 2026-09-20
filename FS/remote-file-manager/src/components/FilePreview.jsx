import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import ReactMarkdown from 'react-markdown';

const API = import.meta.env.VITE_API_URL || "http://localhost:3000";
const LARGE_FILE_LIMIT = 5 * 1024 * 1024; // 5 MB

const FilePreview = ({ file }) => {
  const [loadRequested, setLoadRequested] = useState(false);

  // Click outside to close hack & dynamic CSS classes
  useEffect(() => {
    const modal = document.querySelector('.hdgrfm-fm-modal.dialog');
    if (!modal) return;

    // Inject specific classes so our CSS doesn't break other modals
    modal.classList.add('is-preview-modal');
    const body = modal.querySelector('.hdgrfm-fm-modal-body');
    if (body) body.classList.add('is-preview-modal-body');

    const handleClickOutside = (e) => {
      const rect = modal.getBoundingClientRect();
      const isInDialog = (
        rect.top <= e.clientY &&
        e.clientY <= rect.top + rect.height &&
        rect.left <= e.clientX &&
        e.clientX <= rect.left + rect.width
      );

      if (!isInDialog) {
        const closeBtn = document.querySelector('.hdgrfm-close-icon');
        if (closeBtn) closeBtn.click();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      modal.classList.remove('is-preview-modal');
      if (body) body.classList.remove('is-preview-modal-body');
    };
  }, []);

  const ext = file.name.split('.').pop().toLowerCase();

  const isImage = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp'].includes(ext);
  const isPdf = ext === 'pdf';
  const isMarkdown = ext === 'md' || ext === 'markdown';
  const isTextDocument = ['txt', 'csv', 'json', 'log', 'js', 'jsx'].includes(ext);
  const isOfficeDocument = ['doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'].includes(ext);

  const isPreviewable = isImage || isPdf || isTextDocument || isMarkdown;

  // Cloud-like large file check
  // Note: if file.size is undefined, we assume it's small or we just load it
  const isLargeFile = file.size && file.size > LARGE_FILE_LIMIT;

  const url = `${API}/files/content?path=${encodeURIComponent(file.path)}`;

  if (isOfficeDocument) {
    return (
      <div style={styles.container}>
        <div style={styles.card}>
          <h3>Office Document</h3>
          <p>Browsers do not natively support previewing Office documents (.{ext}).</p>
          <a href={url} download target="_blank" rel="noreferrer" style={styles.button}>
            Download File
          </a>
        </div>
      </div>
    );
  }

  if (!isPreviewable) {
    return (
      <div style={styles.container}>
        <div style={styles.card}>
          <h3>Preview Not Available</h3>
          <p>We do not support previews for .{ext} files yet.</p>
          <a href={url} download target="_blank" rel="noreferrer" style={styles.button}>
            Download File
          </a>
        </div>
      </div>
    );
  }

  if (isLargeFile && !loadRequested) {
    return (
      <div style={styles.container}>
        <div style={styles.card}>
          <h3>Large File Preview</h3>
          <p>This file is quite large ({(file.size / (1024 * 1024)).toFixed(2)} MB).</p>
          <p>Previewing it may take some time or consume bandwidth.</p>
          <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', marginTop: '1rem' }}>
            <button onClick={() => setLoadRequested(true)} style={styles.button}>
              Load Preview Anyway
            </button>
            <a href={url} download target="_blank" rel="noreferrer" style={{ ...styles.button, background: '#fff', color: '#6155b4', border: '1px solid #6155b4' }}>
              Download Instead
            </a>
          </div>
        </div>
      </div>
    );
  }

  // If it's previewable and either small enough OR user requested it
  return (
    <div style={{ width: '80vw', maxWidth: '1200px', height: '80vh', minHeight: '400px', background: '#f9f9f9', display: 'flex', flexDirection: 'column' }}>
      {isImage && <ImagePreview url={url} name={file.name} />}
      {isPdf && <PdfPreview url={url} name={file.name} />}
      {isTextDocument && <TextPreview url={url} />}
      {isMarkdown && <MarkdownPreview url={url} />}
    </div>
  );
};

// --- Sub-components for specific types ---

const ImagePreview = ({ url, name }) => {
  const [loading, setLoading] = useState(true);

  return (
    <div style={styles.viewerContainer}>
      {loading && <LoadingSpinner />}
      <img
        src={url}
        alt={name}
        onLoad={() => setLoading(false)}
        style={{ ...styles.media, opacity: loading ? 0 : 1 }}
      />
    </div>
  );
};

const PdfPreview = ({ url, name }) => {
  const [loading, setLoading] = useState(true);

  return (
    <div style={styles.viewerContainer}>
      {loading && <LoadingSpinner />}
      <iframe
        src={url}
        title={name}
        onLoad={() => setLoading(false)}
        style={{ ...styles.media, width: '100%', height: '100%', opacity: loading ? 0 : 1, border: 'none', backgroundColor: '#fff' }}
      />
    </div>
  );
};

const TextPreview = ({ url }) => {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetch(url, { credentials: 'include' })
      .then(r => r.text())
      .then(data => {
        setText(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setError(true);
        setLoading(false);
      });
  }, [url]);

  if (loading) return <div style={styles.viewerContainer}><LoadingSpinner /></div>;
  if (error) return <div style={styles.container}>Failed to load document.</div>;

  return (
    <div style={{ height: '100%', overflow: 'auto', padding: '1rem', background: '#fff', margin: 0 }}>
      <pre style={{ whiteSpace: 'pre-wrap', wordWrap: 'break-word', fontFamily: 'monospace', fontSize: '14px' }}>
        {text}
      </pre>
    </div>
  );
};

const MarkdownPreview = ({ url }) => {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [showRaw, setShowRaw] = useState(false);
  const [headerNode, setHeaderNode] = useState(null);

  // Setup Portal container for the toggle button
  useEffect(() => {
    // Target the specific open dialog's header
    const header = document.querySelector('.hdgrfm-fm-modal.dialog .hdgrfm-fm-modal-header');

    if (header) {
      const closeBtn = header.querySelector('.hdgrfm-close-icon');

      const container = document.createElement('div');
      container.style.marginLeft = 'auto'; // Push to the right if flex
      container.style.marginRight = '15px'; // Space before close button
      container.style.display = 'flex';
      container.style.alignItems = 'center';

      if (closeBtn) {
        // The close icon might be nested inside a button/wrapper. 
        // We must find the direct child of `header` to use insertBefore.
        let targetChild = closeBtn;
        while (targetChild && targetChild.parentNode !== header) {
          targetChild = targetChild.parentNode;
        }

        if (targetChild) {
          header.insertBefore(container, targetChild);
        } else {
          header.appendChild(container);
        }
      } else {
        header.appendChild(container);
      }

      // eslint-disable-next-line react-hooks/set-state-in-effect
      setHeaderNode(container);

      return () => {
        if (header.contains(container)) {
          header.removeChild(container);
        }
      };
    }
  }, []);

  useEffect(() => {
    fetch(url, { credentials: 'include' })
      .then(r => r.text())
      .then(data => {
        setText(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setError(true);
        setLoading(false);
      });
  }, [url]);

  if (loading) return <div style={styles.viewerContainer}><LoadingSpinner /></div>;
  if (error) return <div style={styles.container}>Failed to load Markdown document.</div>;

  return (
    <>
      {headerNode && createPortal(
        <button
          onClick={() => setShowRaw(!showRaw)}
          style={{ ...styles.button, padding: '4px 10px', fontSize: '12px', borderRadius: '4px' }}
        >
          {showRaw ? "Preview Formatted" : "View Raw Source"}
        </button>,
        headerNode
      )}

      <div style={{ height: '100%', overflow: 'auto', padding: '2rem', background: '#fff', margin: 0, textAlign: 'left', lineHeight: '1.6' }}>
        {showRaw ? (
          <pre style={{ whiteSpace: 'pre-wrap', wordWrap: 'break-word', fontFamily: 'monospace', fontSize: '14px', margin: 0 }}>
            {text}
          </pre>
        ) : (
          <ReactMarkdown>{text}</ReactMarkdown>
        )}
      </div>
    </>
  );
};

const LoadingSpinner = () => (
  <div style={styles.container}>
    <style>
      {`
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
      `}
    </style>
    <div style={{ width: '40px', height: '40px', border: '4px solid #f3f3f3', borderTop: '4px solid #6155b4', borderRadius: '50%', animation: 'spin 1s linear infinite' }}></div>
    <span style={{ marginTop: '10px', color: '#666' }}>Loading preview...</span>
  </div>
);

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    width: '100%',
    textAlign: 'center',
    padding: '20px',
    boxSizing: 'border-box'
  },
  card: {
    background: '#fff',
    padding: '2rem',
    borderRadius: '8px',
    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
    maxWidth: '400px',
  },
  button: {
    padding: '10px 20px',
    background: '#6155b4',
    color: '#fff',
    textDecoration: 'none',
    borderRadius: '4px',
    border: 'none',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: 'bold',
  },
  viewerContainer: {
    position: 'relative',
    width: '100%',
    height: '100%',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center'
  },
  media: {
    maxWidth: '100%',
    maxHeight: '100%',
    objectFit: 'contain',
    transition: 'opacity 0.3s ease-in-out'
  }
};

export default FilePreview;
