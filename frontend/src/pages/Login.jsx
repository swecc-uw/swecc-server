// LoginPage.js
import React, { useState } from "react";
import { useAuth } from "../hooks/useAuth";

const LoginPage = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const { login, error } = useAuth();

  const handlePasswordChange = (event) => {
    setPassword(event.target.value);
  };

  const handleUserNameChange = (event) => {
    setUsername(event.target.value);
  };

  // Updated handleSubmit to call login with username and password
  const handleSubmit = async (event) => {
    event.preventDefault();
    const success = await login(username, password);
    if (!success) {
      console.error("Login failed");
    }
  };

  return (
    <div className="container mt-3">
      <h1>React Cookie Auth</h1>
      <br />
      <h2>Login</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="username">Username</label>
          <input
            type="text"
            className="form-control"
            id="username"
            name="username"
            value={username}
            onChange={handleUserNameChange}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input
            type="password"
            className="form-control"
            id="password"
            name="password"
            value={password}
            onChange={handlePasswordChange}
            required
          />
          <div>
            {error && <small className="text-danger">{error}</small>}
          </div>
        </div>
        <button type="submit" className="btn btn-primary">Login</button>
      </form>
    </div>
  );
};

export default LoginPage;
