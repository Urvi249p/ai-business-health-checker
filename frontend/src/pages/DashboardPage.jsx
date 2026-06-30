import { useEffect, useState } from 'react';

function DashboardPage({ apiBaseUrl, token }) {
  const [description, setDescription] = useState('');
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const loadHistory = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/audit/history`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Unable to load audit history');
      setHistory(data);
    } catch (err) {
      setError(err.message || 'Unable to load history');
    }
  };

  useEffect(() => {
    loadHistory();
  }, [token]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');

    try {
      const response = await fetch(`${apiBaseUrl}/audit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ business_description: description }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Unable to start audit');
      setMessage(`Audit queued with job id ${data.job_id}`);
      setDescription('');
      await loadHistory();
    } catch (err) {
      setError(err.message || 'Unable to start audit');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dashboard-grid">
      <section className="dashboard-card">
        <span className="badge">New audit</span>
        <h2>Describe your business</h2>
        <p className="helper-text">Paste a short summary of your company, industry, and goals to generate a health report.</p>

        <form onSubmit={handleSubmit}>
          <label>
            Business description
            <textarea value={description} onChange={(event) => setDescription(event.target.value)} required minLength={20} />
          </label>
          <button className="primary-btn" disabled={loading}>
            {loading ? 'Submitting...' : 'Start audit'}
          </button>
        </form>

        {message ? <p className="success-text">{message}</p> : null}
        {error ? <p className="error-text">{error}</p> : null}
      </section>

      <section className="history-card">
        <span className="badge">Recent audits</span>
        <h3>Audit history</h3>
        {history.length === 0 ? (
          <p className="helper-text">No audits yet. Submit one above to see it here.</p>
        ) : (
          <ul className="history-list">
            {history.map((job) => (
              <li key={job.job_id}>
                <strong>{job.job_id}</strong>
                <div className={`status-pill ${job.status === 'queued' ? 'pending' : job.status === 'failed' ? 'failed' : ''}`}>
                  {job.status}
                </div>
                <p className="helper-text">Created: {new Date(job.created_at).toLocaleString()}</p>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

export default DashboardPage;
