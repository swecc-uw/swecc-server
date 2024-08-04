import { useState, useEffect } from 'react'
import api from '../api'
import Question from '../components/Question'
import '../styles/Home.css'

function Home () {
  const [questions, setQuestions] = useState([])
  const [topic, setTopic] = useState('')
  const [prompt, setPrompt] = useState('')
  const [solution, setSolution] = useState('')
  const [follow_ups, setFollowUps] = useState('')
  const [source, setSource] = useState('')
  const [topics, setTopics] = useState([])

  useEffect(() => {
    getTopics()
    getQuestions()
  }, [])

  const getQuestions = () => {
    api
      .get('/api/questions/technical/all/')
      .then(res => res.data)
      .then(data => {
        setQuestions(data)
        console.log(data)
      })
      .catch(err => alert(err))
  }

  const getTopics = () => {
    api
      .get('/api/questions/topics/')
      .then(res => res.data)
      .then(data => {
        setTopics(data)
        console.log(data)
      })
      .catch(err => alert(err))
  }

  const createQuestion = e => {
    e.preventDefault()
    api
      .post('/api/questions/technical/', {
        topic,
        prompt,
        solution,
        follow_ups,
        source
      })
      .then(res => {
        if (res.status === 201) alert('Question created!')
        else alert('Failed to make question.')
        getQuestions()
      })
      .catch(err => alert(err))
  }

  return (
    <div>
      <div>
        <h2>Questions</h2>
        {questions.map(question => (
          <Question question={question} key={question.question_id} />
        ))}
      </div>
      <h2>Create a Question</h2>
      <form onSubmit={createQuestion}>
        <label htmlFor='topic'>Topic:</label>
        <br />
        <select
          id='topic'
          name='topic'
          value={topic}
          required
          onChange={e => setTopic(e.target.value)}
        >
          <option value=''>Select a topic</option>
          {topics.map(topic => (
            <option value={topic.topic_id} key={topic.topic_id}>
              {topic.name}
            </option>
          ))}
        </select>
        <br />
        <label htmlFor='prompt'>Prompt:</label>
        <br />
        <textarea
          id='prompt'
          name='prompt'
          required
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
        ></textarea>
        <br />
        <label htmlFor='solution'>Solution:</label>
        <br />
        <textarea
          id='solution'
          name='solution'
          required
          value={solution}
          onChange={e => setSolution(e.target.value)}
        ></textarea>
        <br />
        <label htmlFor='follow_ups'>Follow ups:</label>
        <br />
        <textarea
          id='follow_ups'
          name='follow_ups'
          value={follow_ups}
          onChange={e => setFollowUps(e.target.value)}
        ></textarea>
        <br />
        <label htmlFor='source'>Source:</label>
        <br />
        <textarea
          id='source'
          name='source'
          value={source}
          onChange={e => setSource(e.target.value)}
        ></textarea>
        <br />
        <input type='submit' value='Submit'></input>
      </form>
    </div>
  )
}

export default Home
