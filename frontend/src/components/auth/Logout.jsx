import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";

const Logout = () => {
  const navigate = useNavigate();

    const { logout } = useAuth();

  useEffect(() => {
    // Execute the logout function
    logout();

    // Redirect to login page after logout
    navigate("/login");
  }, [logout, navigate]);

  return <div>Logging out...</div>; // Optionally display a message
};

export default Logout;