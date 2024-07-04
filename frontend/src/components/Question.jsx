import React from "react";
import "../styles/Question.css"

function Question({ question }) {
    const formattedDate = new Date(question.created).toLocaleDateString("en-US")

    return (
        <div className="question-container">
            <p className="question-title">{question.topic}</p>
            <p className="question-content">{question.prompt}</p>
            <p className="question-date">{formattedDate}</p>
        </div>
    );
}

export default Question;
