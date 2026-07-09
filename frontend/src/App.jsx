import { useEffect, useState } from 'react';
import { Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom';
import AuthPage from './pages/AuthPage';
import DashboardPage from './pages/DashboardPage';
import Sidebar from './components/Sidebar';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [user, setUser] = useState(() => {
    const storedUser = localStorage.getItem('user');
    return storedUser ? JSON.parse(storedUser) : null;
  });
  const location = useLocation();
  const navigate = useNavigate();
  const currentView = location.pathname.slice(1) || 'overview';

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
          <Sidebar
            currentView={currentView}
            onNavigate={(view) => navigate(`/${view}`)}
            username={user?.username}
            onLogout={handleLogout}
          />

          <div className="main-panel">
            <header className="page-header">
              <div>
                <p className="eyebrow">AUDITLY DASHBOARD</p>
                <h1>Business health at a glance</h1>
              </div>
            </header>

            <main className="page-content">
              <Routes>
                <Route path="/" element={<Navigate to="/overview" replace />} />
                <Route path="/overview" element={<DashboardPage apiBaseUrl={API_BASE_URL} token={token} view="overview" />} />
              <Route path="/reports" element={<DashboardPage apiBaseUrl={API_BASE_URL} token={token} view="reports" />} />
              <Route path="/history" element={<DashboardPage apiBaseUrl={API_BASE_URL} token={token} view="history" />} />
              <Route path="/settings" element={<DashboardPage apiBaseUrl={API_BASE_URL} token={token} view="settings" />} />
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
