import { useCallback, useEffect, useState } from "react";

import {
  FileManager,
} from "@huongda-group/react-file-manager";

import "@huongda-group/react-file-manager/dist/style.css";

import {
  getChildren,
  getTree,
  createFolder,
  renameFile,
  deleteFile,
  copyFile,
  moveFile,
  uploadFile,
  getDownloadUrl,
} from "./api/files";
import Login from "./Login"
import FilePreview from "./components/FilePreview";
import "./index.css";

import useCustomIcons from "./useCustomIcons";
import ProcessingStatus from "./components/ProcessingStatus";
import Actions from "./components/Actions";
import Notifications from "./components/Notifications";

function App() {

  const [authenticated, setAuthenticated] = useState(() => localStorage.getItem("isAuthenticated") === "true");
  const [files, setFiles] = useState([]);
  const [currentPath, setCurrentPath] = useState(() => {
    const hash = window.location.hash.replace(/^#/, '');
    return hash ? decodeURIComponent(hash) : "/";
  });

  const [loading, setLoading] = useState(false);

  useEffect(() => {
    window.location.hash = currentPath;
  }, [currentPath]);

  // Initialize custom icons
  useCustomIcons(authenticated);


  // -------------------------------------------------------
  // LOAD DIRECTORY
  // -------------------------------------------------------

  const loadDirectory = useCallback(async (rawPath = "/") => {
    let path = typeof rawPath === "string" ? rawPath : "/";
    if (!path.startsWith("/")) path = "/" + path;
    if (path.length > 1 && path.endsWith("/")) path = path.slice(0, -1);
    if (path === "") path = "/";

    try {
      setLoading(true);
      const data = await getChildren(path);

      setFiles((prevFiles) => {
        const getParentPath = (p) => {
          if (p === "/") return null;
          const lastSlash = p.lastIndexOf("/");
          if (lastSlash === 0) return "/";
          return p.substring(0, lastSlash);
        };

        const filteredFiles = prevFiles.filter(
          (f) => getParentPath(f.path) !== path
        );

        const newChildren = data.children.map((f) => ({ ...f, id: f.path }));

        return [...filteredFiles, ...newChildren];
      });
      setCurrentPath(path);
    } catch (error) {
      console.error(error);
      alert(error.message);
      if (error.message.includes("401") || error.message.includes("403") || error.message.toLowerCase().includes("unauthorized")) {
        setAuthenticated(false);
        localStorage.removeItem("isAuthenticated");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  // -------------------------------------------------------
  // INITIAL LOAD
  // -------------------------------------------------------

  useEffect(() => {
    if (authenticated) {
      const init = async () => {
        try {
          setLoading(true);
          const treeData = await getTree();
          const rootData = await getChildren(currentPath);

          const fileMap = new Map();
          treeData.tree.forEach(f => fileMap.set(f.path, { ...f, id: f.path }));
          rootData.children.forEach(f => fileMap.set(f.path, { ...f, id: f.path }));

          setFiles(Array.from(fileMap.values()));
        } catch (error) {
          console.error(error);
          if (error.message.includes("401") || error.message.includes("403") || error.message.toLowerCase().includes("unauthorized")) {
            setAuthenticated(false);
            localStorage.removeItem("isAuthenticated");
          }
        } finally {
          setLoading(false);
        }
      };
      init();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authenticated]);



  // -------------------------------------------------------
  // FOLDER CHANGE
  // -------------------------------------------------------

  const handleFolderChange = useCallback(async (path) => {
    await loadDirectory(path);
  }, [loadDirectory]);

  // -------------------------------------------------------
  // CREATE FOLDER
  // -------------------------------------------------------

  const handleCreateFolder = useCallback(async (name, parentFolder) => {
    try {
      setLoading(true);
      await createFolder(parentFolder.path, name);
      await loadDirectory(parentFolder.path);
    } catch (error) {
      console.error(error);
      alert(error.message);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [loadDirectory]);

  // -------------------------------------------------------
  // RENAME
  // -------------------------------------------------------

  const handleRename = useCallback(async (file, newName) => {
    try {
      setLoading(true);
      await renameFile(file.path, newName);
      await loadDirectory(currentPath);
    } catch (error) {
      console.error(error);
      alert(error.message);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [currentPath, loadDirectory]);

  // -------------------------------------------------------
  // DELETE
  // -------------------------------------------------------

  const handleDelete = useCallback(async (selectedFiles) => {
    try {
      setLoading(true);
      for (const file of selectedFiles) {
        await deleteFile(file.path);
      }
      await loadDirectory(currentPath);
    } catch (error) {
      console.error(error);
      alert(error.message);
    } finally {
      setLoading(false);
    }
  }, [currentPath, loadDirectory]);

  // -------------------------------------------------------
  // DOWNLOAD
  // -------------------------------------------------------

  const handleDownload = useCallback((selectedFiles) => {
    for (const file of selectedFiles) {
      if (file.isDirectory) continue;
      const url = getDownloadUrl(file.path);
      const link = document.createElement("a");
      link.href = url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      document.body.appendChild(link);
      link.click();
      link.remove();
    }
  }, []);

  // -------------------------------------------------------
  // UPLOAD
  // -------------------------------------------------------

  const handleUpload = useCallback(async (file, onProgress) => {
    const result = await uploadFile(currentPath, file, onProgress);
    await loadDirectory(currentPath);
    return result.file;
  }, [currentPath, loadDirectory]);

  // -------------------------------------------------------
  // COPY
  // -------------------------------------------------------

  const handlePaste = useCallback(async (selectedFiles, destinationFolder, operationType) => {
    try {
      setLoading(true);
      for (const file of selectedFiles) {
        if (operationType === "copy") {
          await copyFile(file.path, destinationFolder.path);
        } else {
          await moveFile(file.path, destinationFolder.path);
        }
      }
      await loadDirectory(currentPath);
    } catch (error) {
      console.error(error);
      alert(error.message);
    } finally {
      setLoading(false);
    }
  }, [currentPath, loadDirectory]);

  // -------------------------------------------------------
  // REFRESH
  // -------------------------------------------------------

  const handleRefresh = useCallback(() => {
    loadDirectory(currentPath);
  }, [currentPath, loadDirectory]);



  const filePreviewComponent = useCallback((file) => <FilePreview file={file} />, []);

  const onError = useCallback((error) => {
    console.error("File Manager error:", error);
  }, []);

  if (!authenticated) {
    return (
      <Login
        onLogin={() => {
          localStorage.setItem("isAuthenticated", "true");
          setAuthenticated(true);
        }}
      />
    );
  }

  // -------------------------------------------------------
  // RENDER
  // -------------------------------------------------------

  const customColumns = [
    {
      id: "processing",
      title: "Processing Status",
      width: 450,
      render: (file) => <ProcessingStatus file={file} />,
    },
    {
      id: "actions",
      title: "Actions",
      width: 150,
      render: (file) => <Actions file={file} onRefresh={handleRefresh} />,
    },
  ];

  return (
    <div className="app">
      <div style={{ position: 'absolute', top: 10, right: 20, zIndex: 1000 }}>
        <Notifications />
      </div>
      <FileManager

        files={files}
        columns={customColumns}

        initialPath={currentPath}

        height="100%"

        width="100%"

        layout="list"

        theme="light"

        language="en-US"

        isLoading={loading}

        collapsibleNav

        defaultNavExpanded

        onFolderChange={handleFolderChange}

        onCreateFolder={handleCreateFolder}

        onRename={handleRename}

        onDelete={handleDelete}

        onDownload={handleDownload}

        onUpload={handleUpload}

        onPaste={handlePaste}

        onRefresh={handleRefresh}

        filePreviewComponent={filePreviewComponent}

        onError={onError}

      />

    </div>

  );

}


export default App;