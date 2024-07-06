import React from "react";
import "../styles/Question.css"

function Topics({ topic }) {
    const formattedDate = new Date(topic.created).toLocaleDateString("en-US")

    return (
        <div className="question-container">
            <p className="question-title">{topic.name}</p>
            <p className="question-date">{formattedDate}</p>
        </div>
    );
}

export default Topics;