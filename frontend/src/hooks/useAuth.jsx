import { createContext, useContext, useState, useEffect } from "react";
// import { getCurrentUser } from "../services/member";
import { devPrint } from "../RandomUtils";
import api, { getCSRF } from "../api";

const AuthContext = createContext(undefined);

const getCurrentUser = () => {
  return;
};

export const useAuth = () => {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }

  return context;
};

// eslint-disable-next-line react/prop-types
export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [error, setError] = useState("");
  const [member, setMember] = useState();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getSession();
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      getCurrentUser()
        .then((mem) => setMember(mem))
        .catch((err) => {
          devPrint("Failed to get current user:", err);
          setMember(undefined);
        });
    } else {
      setMember(undefined);
    }
  }, [isAuthenticated]);

  const getSession = async () => {
    try {
      await api.get("/auth/session/");
      setIsAuthenticated(true);
      setLoading(false);
    } catch (err) {
      setIsAuthenticated(false);
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    console.log("testing");
    try {
      const res = await api.post("/auth/login/", { username, password });

      if (res.status === 200) {
        console.log("Login successful");
        getCSRF();
        setIsAuthenticated(true);
        setError("");
      } else {
        handleLoginError(res.data);
      }
    } catch (err) {
      handleLoginError(err.response?.data);
    }
  };

  const handleLoginError = (errorData) => {
    if (
      errorData?.detail ===
      "Your account does not have a Discord ID associated with it."
    ) {
      setError(
        `Your discord is not verified. Please type /auth ${errorData.username} in the swecc server`
      );
    } else {
      setError("Invalid credentials. Please try again.");
      setIsAuthenticated(false);
    }
  };

  const logout = async () => {
    try {
      const res = await api.post("/auth/logout/");

      if (res.status === 200) {
        devPrint("Logout successful");
        getCSRF();
        setIsAuthenticated(false);
      } else {
        devPrint("Logout failed");
      }
    } catch (err) {
      devPrint("Logout failed");
    }
  };

  const register = async (username, password, discord_username) => {
    try {
      const res = await api.post("/auth/register/", {
        username,
        password,
        discord_username,
      });

      if (res.status !== 201) throw new Error("Registration failed.");

      const data = res.data;
      setError("");
      setError(
        `Registration successful. Please type /auth ${username} in the swecc server`
      );
      getCSRF();
      return data.id;
    } catch (err) {
      devPrint("Registration failed:", err.response?.data);
      setError(
        err.response?.data?.detail || "Registration failed. Please try again."
      );
      return null;
    }
  };

  const clearError = () => {
    setError("");
  };

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        error,
        loading,
        member,
        login,
        logout,
        register,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
