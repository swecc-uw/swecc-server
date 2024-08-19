// ProtectedPage.js
import React, { useEffect } from "react";

const API_URL = import.meta.env.VITE_API_URL;

const ProtectedPage = () => {
  const whoami = () => {
    console.log("WhoAmI");
    fetch(`${API_URL}/api/user/whoami/`, {
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include",
    })
      .then((res) => res.json())
      .then((data) => {
        console.log("You are logged in as: " + data.username);
      })
      .catch((err) => {
        console.log(err);
      });
  };

  
  useEffect(() => {
    console.log('ProtectedPage rendered');
  });
  return (
    <div className="container mt-3">
      <h1>React Cookie Auth</h1>
      <p>You are logged in!</p>
      <button className="btn btn-primary mr-2" onClick={whoami}>WhoAmI</button>
    </div>
  );
};

export default ProtectedPage;
