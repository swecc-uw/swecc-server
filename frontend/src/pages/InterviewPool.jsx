import { useEffect } from "react";
import api from "../api";

const InterviewPoolSignUp = () => {
  useEffect(() => {
    async function fetchData() {
      const result = await api.get("/api/interview/status/");
      console.log(result.data);
    }
    fetchData();
  }, []);

  const handleSignUp = async (e) => {
    e.preventDefault();
    const result = await api.post("/api/interview/pool/");
    console.log(result.data);
  };

  const handleCancleSignUp = async (e) => {
    e.preventDefault();
    const result = await api.delete("/api/interview/pool/");
    console.log(result.data);
  };

  return (
    <div>
      <h1>Interview Pool Sign Up</h1>
      <form onSubmit={handleSignUp}>
        <button type="submit">Sign Up</button>
      </form>
      <form onSubmit={handleCancleSignUp}>
        <button type="submit">Cancel Sign Up</button>
      </form>
    </div>
  );
};

export default InterviewPoolSignUp;
