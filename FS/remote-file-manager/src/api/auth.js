const API = import.meta.env.VITE_API_URL || "http://localhost:3000";


export async function login(username, password) {

  const response = await fetch(
    `${API}/auth/login`,
    {
      method: "POST",

      credentials: "include",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        username,
        password,
      }),
    }
  );


  if (!response.ok) {

    let message = "Login failed.";

    try {

      const data = await response.json();

      message = data.detail || message;

    } catch {
        // ignore
    }

    throw new Error(message);
  }


  return response.json();
}