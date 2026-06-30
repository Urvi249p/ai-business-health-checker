import { useState } from 'react';

function AuthPage({ apiBaseUrl, onLogin }) {
  const [mode, setMode] = useState('login');
  const [form, setForm] = useState({ username: '', email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (event) => {
    setForm((prev) => ({ ...prev, [event.target.name]: event.target.value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setLoading(true);

    try {
      const endpoint = mode === 'login' ? '/auth/login' : '/auth/register';
      const body = mode === 'login'
        ? new URLSearchParams({ username: form.username, password: form.password })
        : JSON.stringify({ email: form.email, username: form.username, password: form.password });

      const response = await fetch(`${apiBaseUrl}${endpoint}`, {
        method: 'POST',
        headers: mode === 'login'
          ? { 'Content-Type': 'application/x-www-form-urlencoded' }
          : { 'Content-Type': 'application/json' },
        body,
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Authentication failed');

      onLogin(data);
    } catch (err) {
      setError(err.message || 'Unable to complete authentication');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-card">
      <h2>{mode === 'login' ? 'Welcome back' : 'Create your account'}</h2>
      <p className="helper-text">Sign in to submit a business description and review audit progress.</p>

      <div className="actions" style={{ marginBottom: 16 }}>
        <button className="secondary-btn" onClick={() => setMode('login')}>Login</button>
        <button className="secondary-btn" onClick={() => setMode('register')}>Register</button>
      </div>

      {error ? <p className="error-text">{error}</p> : null}

      <form onSubmit={handleSubmit}>
        <label>
          Username
          <input name="username" value={form.username} onChange={handleChange} required />
        </label>

        {mode === 'register' ? (
          <label>
            Email
            <input name="email" type="email" value={form.email} onChange={handleChange} required />
          </label>
        ) : null}

        <label>
          Password
          <input name="password" type="password" value={form.password} onChange={handleChange} required minLength={8} />
        </label>

        <button className="primary-btn" disabled={loading}>
          {loading ? 'Working...' : mode === 'login' ? 'Login' : 'Register'}
        </button>
      </form>
    </div>
  );
}

export default AuthPage;
