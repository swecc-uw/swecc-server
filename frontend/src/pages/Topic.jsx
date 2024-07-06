import { useState, useEffect } from "react";
import api from "../api";
import Topics from "../components/Topics"
import "../styles/Home.css"

function Topic() {
    const [topics, setTopics] = useState([]);
    const [topic, setTopic] = useState("");  


    useEffect(() => {
        getTopics();
    }, []);

    const getTopics = () => {
        api
            .get("/api/questions/topics/")
            .then((res) => res.data)
            .then((data) => {
                setTopics(data);
                console.log(data);
            })
            .catch((err) => alert(err));
    };

    const createTopic = (e) => {
        e.preventDefault();
        api
            .post("/api/questions/topics/", { name: topic })
            .then((res) => {
                if (res.status === 201) alert("Topic created!");
                else alert("Failed to make topic.");
                getTopics();
            })
            .catch((err) => alert(err));
    };

    return (
        <div>
            <div>
                <h2>Topics</h2>
                {topics.map((topic) => (
                    <Topics topic={topic} key={topic.topic_id} />
                ))}
            </div>
            <h2>Create a Question</h2>
            <form onSubmit={createTopic}>
                <label htmlFor="name">Topic:</label>
                <br />
                <input
                    type="text"
                    id="name"
                    name="name"
                    required
                    onChange={(e) => setTopic(e.target.value)}
                    value={topic}
                />
                <br />
                <input type="submit" value="Submit"></input>
            </form>
        </div>
    );
}

export default Topic;
