import { useEffect, useState } from 'react';
import { Routes, Route, Navigate, Link } from 'react-router-dom';
import AuthPage from './pages/AuthPage';
import DashboardPage from './pages/DashboardPage';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [user, setUser] = useState(() => {
    const storedUser = localStorage.getItem('user');
    return storedUser ? JSON.parse(storedUser) : null;
  });

  useEffect(() => {
    localStorage.setItem('token', token);
    if (!token) {
      localStorage.removeItem('user');
      setUser(null);
    }
  }, [token]);

  const handleLogin = (authData) => {
    localStorage.setItem('token', authData.access_token);
    localStorage.setItem('user', JSON.stringify({
      user_id: authData.user_id,
      email: authData.email,
      username: authData.username,
    }));
    setToken(authData.access_token);
    setUser({
      user_id: authData.user_id,
      email: authData.email,
      username: authData.username,
    });
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setToken('');
    setUser(null);
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <h1>AI Business Health Checker</h1>
          <p>Turn a business description into an audit strategy report.</p>
        </div>
        <nav>
          {token ? (
            <>
              <span className="user-pill">{user?.username || 'Signed in'}</span>
              <button className="secondary-btn" onClick={handleLogout}>Logout</button>
            </>
          ) : (
            <Link className="nav-link" to="/auth">Sign in</Link>
          )}
        </nav>
      </header>

      <main>
        <Routes>
          <Route path="/" element={token ? <DashboardPage apiBaseUrl={API_BASE_URL} token={token} /> : <Navigate to="/auth" replace />} />
          <Route path="/auth" element={!token ? <AuthPage apiBaseUrl={API_BASE_URL} onLogin={handleLogin} /> : <Navigate to="/" replace />} />
          <Route path="*" element={<Navigate to={token ? '/' : '/auth'} replace />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
