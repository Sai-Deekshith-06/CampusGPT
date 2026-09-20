import { useState } from "react";

import { login } from "./api/auth";


function Login({ onLogin }) {

  const [username, setUsername] = useState("admin");

  const [password, setPassword] = useState(
    "PeergosRules!"
  );

  const [error, setError] = useState("");

  const [loading, setLoading] = useState(false);


  const handleSubmit = async (event) => {

    event.preventDefault();

    setError("");

    setLoading(true);

    try {

      await login(username, password);

      onLogin();

    } catch (error) {

      setError(error.message);

    } finally {

      setLoading(false);

    }

  };


  return (

    <div className="login">

      <form onSubmit={handleSubmit}>

        <h2>File Manager</h2>

        <input
          value={username}
          onChange={(event) =>
            setUsername(event.target.value)
          }
          placeholder="Username"
        />

        <input
          type="password"
          value={password}
          onChange={(event) =>
            setPassword(event.target.value)
          }
          placeholder="Password"
        />

        {error && (
          <div className="login-error">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
        >
          {loading ? "Logging in..." : "Login"}
        </button>

      </form>

    </div>

  );

}


export default Login;