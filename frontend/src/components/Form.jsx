import { useState } from "react";
import api from "../api";
import { useNavigate } from "react-router-dom";
import { ACCESS_TOKEN, ONBOARDED, REFRESH_TOKEN } from "../constants";
import "../styles/Form.css"
import LoadingIndicator from "./LoadingIndicator";

function Form({ route, method }) {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const name = method === "login" ? "Login" : "Register";

    const checkIfMemberExists = async () => {
        console.log("checking if member exists")
        try {
            const res = await api.get('/api/members/profile/')
            console.log(res)
            alert(res.status)
            return res.status === 200
        } catch (error) {
            console.log(error)
            return false
        }
    }

    const handleSubmit = async (e) => {
        setLoading(true);
        e.preventDefault();
        console.log("submitting", username, password);

        try {
            const res = await api.post(route, { username, password })
            if (method === "login") {
                localStorage.setItem(ACCESS_TOKEN, res.data.access);
                localStorage.setItem(REFRESH_TOKEN, res.data.refresh);

                if (await checkIfMemberExists()) {
                    alert('exists')
                    navigate("/")
                } else {
                    alert('does not exist')
                    navigate("/onboarding")
                }

            } else {
                navigate("/login")

                localStorage.setItem(ONBOARDED, false)
            }
        } catch (error) {
            alert(error)
        } finally {
            setLoading(false)
        }
    };

    return (
        <form onSubmit={handleSubmit} className="form-container">
            <h1>{name}</h1>
            <input
                className="form-input"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Username"
            />
            <input
                className="form-input"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
            />
            {loading && <LoadingIndicator />}
            <button className="form-button" type="submit">
                {name}
            </button>
            <a href={method === "login" ? "/register" : "/login"}>
                Or, {method === "login" ? "register" : "login"}
            </a>
        </form>
    );
}

export default Form