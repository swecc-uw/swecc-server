import React, { createContext, useContext, useState, useEffect } from "react";
import { devPrint } from "../components/utils/Dev";

const API_URL = import.meta.env.VITE_API_URL;

const AuthContext = createContext();

export const useAuth = () => {
  return useContext(AuthContext);
};

export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [csrf, setCsrf] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getSession(); 
  }, []);

  const getSession = () => {
    fetch(`${API_URL}/api/user/session/`, {
      credentials: "include",
    })
      .then((res) => res.json())
      .then((data) => {
        devPrint("Session data:", data); 
        if (data.isAuthenticated) {
          setIsAuthenticated(true);
        } else {
          setIsAuthenticated(false);
          getCSRF();
        }
        setLoading(false); 
      })
      .catch((err) => {
        console.error("Failed to fetch session data:", err);
        setIsAuthenticated(false);
        setLoading(false); 
      });
  };

  const getCSRF = async () => {
    try {
      const res = await fetch(`${API_URL}/api/user/csrf/`, {
        credentials: "include",
      });

      if (!res.ok) {
        throw new Error("Failed to fetch CSRF token");
      }

      const csrfToken = res.headers.get("X-CSRFToken");
      if (csrfToken) {
        setCsrf(csrfToken);
        devPrint("CSRF Token fetched and set:", csrfToken);
      } else {
        throw new Error("CSRF token not found in response headers");
      }
    } catch (err) {
      console.error("Failed to fetch CSRF token:", err);
    }
  };

  const login = async (username, password) => {
    try {
      const res = await fetch(`${API_URL}/api/user/login/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrf, 
        },
        credentials: "include",
        body: JSON.stringify({ username, password }),
      });

      if (res.ok) {
        const data = await res.json();
        devPrint("Login successful:", data);
        setIsAuthenticated(true);
        setError("");
        return true;
      } else {
        const errorData = await res.json();
        console.error("Login failed:", errorData);
        setError("Invalid credentials. Please try again.");
        setIsAuthenticated(false);
        return false;
      }
    } catch (err) {
      console.error("Error during login:", err);
      setError("An error occurred. Please try again later.");
      setIsAuthenticated(false);
      return false;
    }
  };

  const logout = async () => {
    try {
      const res = await fetch(`${API_URL}/api/user/logout`, {
        credentials: "include",
      });

      if (res.ok) {
        devPrint("Logout successful");
        setIsAuthenticated(false);
        await getCSRF(); 
      } else {
        console.error("Logout failed");
      }
    } catch (err) {
      console.error("Error during logout:", err);
    }
  };

  const register = (username, password) => {
  fetch(`${API_URL}/api/user/register/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ username, password }),
  })
    .then((res) => {
      if (!res.ok) {
        throw new Error("Registration failed.");
      }
      return res.json();
    })
    .then((data) => {
      devPrint("Registration successful:", data);
      setError(""); 
      login(username, password);
    })
    .catch((err) => {
      console.error("Error during registration:", err);
      setError("Registration failed. Please try again.");
    });
};

  return (
    <AuthContext.Provider
      value={{ isAuthenticated, csrf, error, loading, login, logout, register }}
    >
      {children}
    </AuthContext.Provider>
  );
};
