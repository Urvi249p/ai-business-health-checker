import { useEffect, useState } from 'react';
import { Routes, Route, Navigate, NavLink } from 'react-router-dom';
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
    <div className={`app-shell ${token ? 'app-shell--authenticated' : ''}`}>
      {token ? (
        <>
          <aside className="sidebar">
            <div className="sidebar__brand">
              <div className="brand-mark">AH</div>
              <div>
                <p className="brand-title">AI Business</p>
                <span className="brand-subtitle">Health Checker</span>
              </div>
            </div>

            <nav className="sidebar__nav" aria-label="Primary navigation">
              <NavLink to="/overview" className={({ isActive }) => `sidebar__link ${isActive ? 'is-active' : ''}`} end>
                <span className="sidebar__icon">⌂</span>
                <span>Overview</span>
              </NavLink>
              <NavLink to="/reports" className={({ isActive }) => `sidebar__link ${isActive ? 'is-active' : ''}`}>
                <span className="sidebar__icon">▣</span>
                <span>Reports</span>
              </NavLink>
              <NavLink to="/history" className={({ isActive }) => `sidebar__link ${isActive ? 'is-active' : ''}`}>
                <span className="sidebar__icon">◌</span>
                <span>History</span>
              </NavLink>
            </nav>

            <div className="sidebar__footer">
              <div className="sidebar__profile">
                <div className="profile-avatar">
                  {(user?.username || 'U').slice(0, 1).toUpperCase()}
                </div>
                <div>
                  <p className="profile-name">{user?.username || 'Signed in'}</p>
                  <span className="profile-role">Business owner</span>
                </div>
              </div>
              <button className="sidebar__logout" onClick={handleLogout}>Log out</button>
            </div>
          </aside>

          <div className="main-panel">
            <header className="page-header">
              <div>
                <p className="eyebrow">Operations dashboard</p>
                <h1>Business health at a glance</h1>
              </div>
              <div className="page-header__meta">
                <span className="meta-pill">Live reports</span>
                <span className="meta-pill meta-pill--accent">Trusted by founders</span>
              </div>
            </header>

            <main className="page-content">
              <Routes>
                <Route path="/" element={<Navigate to="/overview" replace />} />
                <Route path="/overview" element={<DashboardPage apiBaseUrl={API_BASE_URL} token={token} view="overview" />} />
                <Route path="/reports" element={<DashboardPage apiBaseUrl={API_BASE_URL} token={token} view="reports" />} />
                <Route path="/history" element={<DashboardPage apiBaseUrl={API_BASE_URL} token={token} view="history" />} />
                <Route path="*" element={<Navigate to="/overview" replace />} />
              </Routes>
            </main>
          </div>
        </>
      ) : (
        <div className="auth-layout">
          <Routes>
            <Route path="/auth" element={<AuthPage apiBaseUrl={API_BASE_URL} onLogin={handleLogin} />} />
            <Route path="*" element={<Navigate to="/auth" replace />} />
          </Routes>
        </div>
      )}
    </div>
  );
}

export default App;
