import { useEffect, useState } from 'react';
import { Routes, Route, Navigate, NavLink, useLocation } from 'react-router-dom';
import AuthPage from './pages/AuthPage';
import DashboardPage from './pages/DashboardPage';
import SettingsPage from './pages/SettingsPage';
import AuditlyBrand from './components/AuditlyBrand';
import { apiFetch as apiFetchClient } from './utils/apiClient';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';

function App() {
  const location = useLocation();
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [refreshToken, setRefreshToken] = useState(localStorage.getItem('refreshToken') || '');
  const [user, setUser] = useState(() => {
    const storedUser = localStorage.getItem('user');
    return storedUser ? JSON.parse(storedUser) : null;
  });

  useEffect(() => {
    if (token) {
      localStorage.setItem('token', token);
      localStorage.setItem('refreshToken', refreshToken);
    } else {
      localStorage.removeItem('token');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('user');
      setUser(null);
    }
  }, [token, refreshToken]);

  const getTokens = () => ({ accessToken: token, refreshToken });

  const setTokens = ({ accessToken: newAccessToken, refreshToken: newRefreshToken }) => {
    if (newAccessToken) {
      setToken(newAccessToken);
    }
    if (newRefreshToken) {
      setRefreshToken(newRefreshToken);
    }
  };

  const handleLogin = (authData) => {
    const authUser = {
      user_id: authData.user_id,
      email: authData.email,
      username: authData.username,
    };

    localStorage.setItem('token', authData.access_token);
    localStorage.setItem('refreshToken', authData.refresh_token || '');
    localStorage.setItem('user', JSON.stringify(authUser));

    setToken(authData.access_token);
    setRefreshToken(authData.refresh_token || '');
    setUser(authUser);
  };

  const handleLogout = async () => {
    try {
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
    } catch (e) {
      // ignore network errors and still clear local state
    } finally {
      localStorage.removeItem('token');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('user');
      setToken('');
      setRefreshToken('');
      setUser(null);
    }
  };

  const apiFetch = (path, options = {}) =>
    apiFetchClient(API_BASE_URL, path, options, getTokens, setTokens, handleLogout);

  return (
    <div className={`app-shell ${token ? 'app-shell--authenticated' : ''}`}>
      {token ? (
        <>
          <aside className="sidebar">
            <div className="sidebar__brand">
              <AuditlyBrand size={32} className="sidebar__brand-logo" wordmarkClassName="sidebar__brand-wordmark" />
            </div>

            <nav className="sidebar__nav" aria-label="Primary navigation">
              <NavLink to="/overview" className={({ isActive }) => `sidebar__link ${isActive ? 'is-active' : ''}`} end>
                <span className="sidebar__icon">⌂</span>
                <span>Overview</span>
              </NavLink>
              <NavLink to="/audit" className={({ isActive }) => `sidebar__link ${isActive ? 'is-active' : ''}`}>
                <span className="sidebar__icon">✦</span>
                <span>New Audit</span>
              </NavLink>
              <NavLink to="/reports" className={({ isActive }) => `sidebar__link ${isActive ? 'is-active' : ''}`}>
                <span className="sidebar__icon">▣</span>
                <span>Reports</span>
              </NavLink>
              <NavLink to="/history" className={({ isActive }) => `sidebar__link ${isActive ? 'is-active' : ''}`}>
                <span className="sidebar__icon">◌</span>
                <span>History</span>
              </NavLink>
              <NavLink to="/settings" 
                className={({ isActive }) => 
                  `sidebar__link ${isActive ? 'is-active' : ''}`}>
                <span className="sidebar__icon">⚙</span>
                <span>Settings</span>
              </NavLink>
            </nav>

            <div className="sidebar__footer">
              <div className="sidebar__profile">
                <div className="profile-avatar">
                  {(user?.username || 'U').slice(0, 1).toUpperCase()}
                </div>
                <div>
                  <p className="profile-name">{user?.username || 'Signed in'}</p>
                  {user?.role ? <span className="profile-role">{user.role}</span> : null}
                </div>
              </div>
              <button className="sidebar__logout" onClick={handleLogout}>Log out</button>
            </div>
          </aside>

          <div className="main-panel">
            <header className="page-header">
              <div>
                <p className="eyebrow">AUDITLY DASHBOARD</p>
                <h1>
                  {location.pathname === '/audit'
                    ? 'Start a new audit'
                    : location.pathname === '/reports'
                      ? 'Your reports'
                      : location.pathname === '/history'
                        ? 'Audit history'
                        : location.pathname === '/settings'
                          ? 'Account settings'
                          : 'Business health at a glance'}
                </h1>
              </div>
            </header>

            <main className="page-content">
              <Routes>
                <Route path="/" element={<Navigate to="/overview" replace />} />
                <Route path="/overview" element={<DashboardPage apiBaseUrl={API_BASE_URL} token={token} apiFetch={apiFetch} view="home" />} />
                <Route path="/audit" element={<DashboardPage apiBaseUrl={API_BASE_URL} token={token} apiFetch={apiFetch} view="overview" />} />
                <Route path="/reports" element={<DashboardPage apiBaseUrl={API_BASE_URL} token={token} apiFetch={apiFetch} view="reports" />} />
                <Route path="/history" element={<DashboardPage apiBaseUrl={API_BASE_URL} token={token} apiFetch={apiFetch} view="history" />} />
                <Route path="/settings" element={
                  <SettingsPage 
                    apiBaseUrl={API_BASE_URL} 
                    token={token} 
                    apiFetch={apiFetch}
                    user={user}
                    onLogout={handleLogout}
                  />} 
                />
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
