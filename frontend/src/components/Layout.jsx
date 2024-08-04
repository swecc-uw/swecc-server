import { Link } from 'react-router-dom';
import '../styles/Layout.css';

const Layout = ({ children }) => {
  return (
    <div className="layout">
      <nav className="navbar">
        <ul>
          <li><Link to="/">Home</Link></li>
          <li><Link to="/profile">Profile</Link></li>
          <li><Link to="/topics">Topics</Link></li>
          <li><Link to="/onboarding">Onboarding</Link></li>
          <li><Link to="/api">API Debug</Link></li>
          <li><Link to="/interview">Interview Pool</Link></li>
          <li><Link to="/directory">Directory</Link></li>
          <li><Link to="/logout">Logout</Link></li>
        </ul>
      </nav>
      <main>
        {children}
      </main>
    </div>
  );
};

export default Layout;
