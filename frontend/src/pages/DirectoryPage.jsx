import { useState, useEffect } from 'react';
import api from '../api';


const DirectoryEntry = ({ entry }) => {
  if (!entry || !entry.first_name || !entry.last_name)
    throw new Error("bad dirent")

  return (
    <div>
      <h2>{entry.first_name} {entry.last_name}</h2>
      {entry.linkedin && entry.linkedin.username && (
        <p>LinkedIn: {entry.linkedin.username}</p>
      )}
      {entry.github && entry.github.username && (
        <p>GitHub: {entry.github.username}</p>
      )}
      {entry.leetcode && entry.leetcode.username && (
        <p>LeetCode: {entry.leetcode.username}</p>
      )}
      {entry.email && (
        <p>Email: {entry.email}</p>
      )}
      {entry.role && (
        <p>Role: {entry.role}</p>
      )}
      {entry.major && (
        <p>Major: {entry.major}</p>
      )}
      {entry.grad_date && (
        <p>Graduation Date: {entry.grad_date}</p>
      )}
      {entry.discord_username && (
        <p>Discord: {entry.discord_username}</p>
      )}
      {entry.resume_url && (
        <p>Resume URL: {entry.resume_url}</p>
      )}
      {entry.local && (
        <p>Location: {entry.local}</p>
      )}
      {entry.bio && (
        <p>Bio: {entry.bio}</p>
      )}
      {entry.discord_id && (
        <p>Discord ID: {entry.discord_id}</p>
      )}
    </div>
  )
}

const DirectoryPage = () => {
  const [directoryEntries, setDirectoryEntries] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [query, setQuery] = useState('');

  console.log('Directory: ', directoryEntries);

  useEffect(() => {
    fetchDirectoryEntries('');
  }, []);

  const fetchDirectoryEntries = (q) => {
    const url = '/api/directory/search' + (q.length > 0 ? '?q=' + q : '');

    api.get(url)
      .then(response => {
        setDirectoryEntries(response.data);
        setIsLoading(false);
      })
      .catch(error => {
        console.error('Error fetching data: ', error);
      });
  }

  const handleQueryUpdate = (event) => {
    setQuery(event.target.value);
  }

  const handleSearch = () => {
    fetchDirectoryEntries(query);
  }

  return (
    <div>
      <h1>Directory</h1>
      <input type="text" value={query} onChange={handleQueryUpdate} />
      <button onClick={handleSearch}>Search</button>
      {isLoading ? (
        <p>Loading...</p>
      ) : (
        <ul>
          {directoryEntries.map(entry => (
            <li key={entry.user}>
              <DirectoryEntry entry={entry} />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default DirectoryPage;
