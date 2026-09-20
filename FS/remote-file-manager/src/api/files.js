const API = import.meta.env.VITE_API_URL || "http://localhost:3000";

async function request(url, options = {}) {
  const response = await fetch(`${API}${url}`, {
    credentials: "include",
    ...options,
  });

  if (!response.ok) {
    let message = `Request failed: ${response.status}`;

    try {
      const data = await response.json();
      message = data.detail || message;
    } catch {
      // Ignore JSON parsing error
    }

    if (response.status === 401 || response.status === 403) {
      localStorage.removeItem("isAuthenticated");
      window.location.reload();
    }

    throw new Error(message);
  }

  return response;
}


// ---------------------------------------------------------
// LIST
// ---------------------------------------------------------

export async function getChildren(path = "/") {
  const response = await request(
    `/files/children?path=${encodeURIComponent(path)}`
  );

  return response.json();
}


// ---------------------------------------------------------
// TREE
// ---------------------------------------------------------

export async function getTree() {
  const response = await request("/files/tree");
  return response.json();
}


// ---------------------------------------------------------
// CREATE FOLDER
// ---------------------------------------------------------

export async function createFolder(path, name) {
  const response = await request("/files/mkdir", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      path,
      name,
    }),
  });

  return response.json();
}


// ---------------------------------------------------------
// RENAME
// ---------------------------------------------------------

export async function renameFile(path, name) {
  const response = await request("/files/rename", {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      path,
      name,
    }),
  });

  return response.json();
}


// ---------------------------------------------------------
// DELETE
// ---------------------------------------------------------

export async function deleteFile(path) {
  const response = await request(
    `/files?path=${encodeURIComponent(path)}`,
    {
      method: "DELETE",
    }
  );

  return response.json();
}


// ---------------------------------------------------------
// COPY
// ---------------------------------------------------------

export async function copyFile(source, destination) {
  const response = await request("/files/copy", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      source,
      destination,
    }),
  });

  return response.json();
}


// ---------------------------------------------------------
// MOVE
// ---------------------------------------------------------

export async function moveFile(source, destination) {
  const response = await request("/files/move", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      source,
      destination,
    }),
  });

  return response.json();
}


// ---------------------------------------------------------
// UPLOAD
// ---------------------------------------------------------

export async function uploadFile(path, file, onProgress) {
  const formData = new FormData();

  formData.append("file", file);

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    xhr.open(
      "POST",
      `${API}/files/upload?path=${encodeURIComponent(path)}`
    );

    xhr.withCredentials = true;

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable && onProgress) {
        const progress =
          (event.loaded / event.total) * 100;

        onProgress(progress);
      }
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText));
        } catch {
          reject(new Error("Invalid server response."));
        }
      } else {
        if (xhr.status === 401 || xhr.status === 403) {
          localStorage.removeItem("isAuthenticated");
          window.location.reload();
        }
        reject(
          new Error(
            `Upload failed: ${xhr.status}`
          )
        );
      }
    };

    xhr.onerror = () => {
      reject(new Error("Network error during upload."));
    };

    xhr.send(formData);
  });
}


// ---------------------------------------------------------
// DOWNLOAD
// ---------------------------------------------------------

export function getDownloadUrl(path) {
  return `${API}/files/content?path=${encodeURIComponent(path)}&download=true`;
}