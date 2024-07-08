import { useState } from "react";
import api from "../api";
import { useNavigate } from "react-router-dom";
import { ACCESS_TOKEN, ONBOARDED, REFRESH_TOKEN } from "../constants";
import "../styles/Form.css";
import LoadingIndicator from "./LoadingIndicator";

function RegisterForm({ route, method }) {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [authKey, setAuthKey] = useState("");
    const [verified, setVerified] = useState(false);
    const navigate = useNavigate();

    const checkIfVerified = async (e) => {
        e.preventDefault();
        try {
            const res = await api.get(`/api/discord/${authKey}/`);
            if (res.data.discord_id !== null && res.data.discord_username !== null) {
                setVerified(true);
            } else {
                alert("Verification failed. Please try again.");
            }
        } catch (error) {
            console.error("Error checking verification status:", error);
            alert("Error checking verification status. Please try again.");
        }
    };

    const getAuthKey = async (e) => {
        e.preventDefault();
        try {
            const res = await api.post('/api/discord/create/');
            setAuthKey(res.data.key);
        } catch (error) {
            console.error("Error getting auth key:", error);
            alert("Error getting auth key. Please try again.");
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        console.log("Submitting", username, password);

        try {
            const res = await api.post(route, { username, password });
            navigate("/login");
            localStorage.setItem(ONBOARDED, false);
        } catch (error) {
            console.error("Error creating account:", error);
            alert("Error creating account. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            {!authKey && (
                <div>
                    <form className="form-container" onSubmit={getAuthKey}>
                    <p>
                        We require users to verify their accounts with their Discord account. <br />
                        Click "Get Auth Key" to get an auth key, then on the swecc Discord server type /auth authkey.
                    </p>
                        <button className="form-button" type="submit">Get Auth Key</button>
                    </form>
                </div>
            )}
            {authKey && (
                <div>
                    <form className="form-container" onSubmit={checkIfVerified}>
                    <p>Auth Key: {authKey}</p>
                    <p>Click "Next" once you have verified on Discord.</p>
                        <button className="form-button" type="submit">Next</button>
                    </form>
                </div>
            )}
            {verified && (
                <form className="form-container" onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label>Username</label>
                        <input
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            required
                        />
                    </div>
                    <div className="form-group">
                        <label>Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                        />
                    </div>
                    <button className="form-button" type="submit">Create Account</button>
                </form>
            )}
            {loading && <LoadingIndicator />}
        </div>
    );
}

export default RegisterForm;
