import { useState } from 'react';
import { CopyToClipboard } from 'react-copy-to-clipboard';
import { ACCESS_TOKEN, REFRESH_TOKEN } from '../constants';
import api from '../api';
import '../styles/StupidAuthDebug.css';

export default function StupidAuthDebug() {
  const accessToken = localStorage.getItem(ACCESS_TOKEN);
  const refreshToken = localStorage.getItem(REFRESH_TOKEN);
  const authenticatedCurlString = `
    curl -X GET \\
    -H "Authorization: Bearer ${accessToken}" \\
    http://localhost:8000/api/
  `;

  const [endpoint, setEndpoint] = useState('http://localhost:8000/api/');
  const [method, setMethod] = useState('GET');
  const [body, setBody] = useState('');
  const [response, setResponse] = useState('');

  const sendRequest = async () => {
    try {
      let res;
      switch (method) {
        case 'GET':
          res = await api.get(endpoint);
          break;
        case 'POST':
          res = body !== ""
            ? await api.post(endpoint, JSON.parse(body))
            : await api.post(endpoint);
          break;
        case 'PUT':
          res = body !== ""
            ? await api.put(endpoint, JSON.parse(body))
            : await api.put(endpoint);
          break;
        case 'PATCH':
          res = body !== ""
            ? await api.patch(endpoint, JSON.parse(body))
            : await api.patch(endpoint);
          break;
        case 'DELETE':
          res = await api.delete(endpoint);
          break;
        default:
          throw new Error('Invalid method');
      }
      setResponse(JSON.stringify(res.data, null, 2));
    } catch (error) {
      setResponse(error.toString());
    }
  };

  return (
    <div className='auth-debug'>
      <h2>Access token:</h2>
      <div className='token-container'>
        <p className='token'>{accessToken}</p>
        <CopyToClipboard text={accessToken}>
          <button>Copy</button>
        </CopyToClipboard>
      </div>
      <h2>Refresh token:</h2>
      <div className='token-container'>
        <p className='token'>{refreshToken}</p>
        <CopyToClipboard text={refreshToken}>
          <button>Copy</button>
        </CopyToClipboard>
      </div>
      <div className='token-container'>
        <h2>Authenticated cURL request:</h2>
        <pre className='curl-string'>{authenticatedCurlString}</pre>
        <CopyToClipboard text={authenticatedCurlString}>
          <button>Copy</button>
        </CopyToClipboard>
      </div>
      <div className='request-container'>
        <h2>Send a Request</h2>
        <div className='input-group'>
          <label htmlFor='endpoint'>Endpoint URL:</label>
          <input
            id='endpoint'
            type='text'
            value={endpoint}
            onChange={(e) => setEndpoint(e.target.value)}
          />
        </div>
        <div className='input-group'>
          <label htmlFor='method'>HTTP Method:</label>
          <select
            id='method'
            value={method}
            onChange={(e) => setMethod(e.target.value)}
          >
            <option value='GET'>GET</option>
            <option value='POST'>POST</option>
            <option value='PUT'>PUT</option>
            <option value='PATCH'>PATCH</option>
            <option value='DELETE'>DELETE</option>
          </select>
        </div>
        {method !== 'GET' && method !== 'DELETE' && (
          <div className='input-group'>
            <label htmlFor='body'>Request Body:</label>
            <textarea
              id='body'
              value={body}
              onChange={(e) => setBody(e.target.value)}
            />
          </div>
        )}
        <button onClick={sendRequest}>Send Request</button>
        {response && (
          <div className='response'>
            <h3>Response</h3>
            <pre>{response}</pre>
          </div>
        )}
      </div>
    </div>
  );
}
