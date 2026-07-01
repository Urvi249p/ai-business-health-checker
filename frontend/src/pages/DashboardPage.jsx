import { useEffect, useState } from 'react';

const agentSteps = [
  { name: 'Business Analyst', description: 'Extract and structure key business information' },
  { name: 'Competitor Intelligence Researcher', description: 'Research and analyze 3 competitors' },
  { name: 'Strategic SWOT Analyst', description: 'Produce a detailed SWOT analysis' },
  { name: 'Pricing Strategy Consultant', description: 'Recommend the optimal pricing model' },
  { name: 'Growth Strategy Consultant', description: 'Create a detailed 90-day action plan' },
  { name: 'Business Report Writer', description: 'Assemble all research into a final report' },
];

function DashboardPage({ apiBaseUrl, token, view = 'overview' }) {
  const [description, setDescription] = useState('');
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [countdown, setCountdown] = useState(48);
  const [downloadingJobId, setDownloadingJobId] = useState(null);
  const [activeJobId, setActiveJobId] = useState('');
  const [pipelineStatus, setPipelineStatus] = useState('queued');
  const [activeAgentIndex, setActiveAgentIndex] = useState(-1);
  const [failedAgentIndex, setFailedAgentIndex] = useState(-1);

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

  useEffect(() => {
    const interval = setInterval(() => {
      setCountdown((value) => (value > 0 ? value - 1 : 0));
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (!activeJobId || !token) return;

    let cancelled = false;

    const pollStatus = async () => {
      try {
        const response = await fetch(`${apiBaseUrl}/audit/${activeJobId}/status`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Unable to refresh audit status');

        if (cancelled) return;

        const normalizedStatus = formatStatus(data.status);
        setPipelineStatus(normalizedStatus);

        if (normalizedStatus === 'queued') {
          setActiveAgentIndex(-1);
          setFailedAgentIndex(-1);
        } else if (normalizedStatus === 'completed') {
          setActiveAgentIndex(agentSteps.length - 1);
          setFailedAgentIndex(-1);
        } else if (normalizedStatus === 'failed') {
          setFailedAgentIndex((current) => current >= 0 ? current : (activeAgentIndex >= 0 ? activeAgentIndex : 0));
        } else if (normalizedStatus === 'processing') {
          setFailedAgentIndex(-1);
          setActiveAgentIndex((current) => (current < 0 ? 0 : current));
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message || 'Unable to refresh audit status');
        }
      }
    };

    pollStatus();
    const intervalId = window.setInterval(pollStatus, 5000);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [activeJobId, token, apiBaseUrl]);

  useEffect(() => {
    if (pipelineStatus !== 'processing' || activeAgentIndex >= agentSteps.length - 1) return;

    const intervalId = window.setInterval(() => {
      setActiveAgentIndex((current) => {
        if (current < 0) return 0;
        return current + 1 >= agentSteps.length ? current : current + 1;
      });
    }, 15000);

    return () => window.clearInterval(intervalId);
  }, [pipelineStatus, activeAgentIndex]);

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
      setActiveJobId(data.job_id);
      setPipelineStatus('queued');
      setActiveAgentIndex(-1);
      setFailedAgentIndex(-1);
      setMessage(`Audit queued with job id ${data.job_id}`);
      setDescription('');
      await loadHistory();
    } catch (err) {
      setError(err.message || 'Unable to start audit');
    } finally {
      setLoading(false);
    }
  };

  const formatStatus = (status) => {
    const normalized = String(status || 'queued').toLowerCase();
    if (normalized === 'completed' || normalized === 'success') return 'completed';
    if (normalized === 'processing' || normalized === 'running') return 'processing';
    if (normalized === 'failed' || normalized === 'error') return 'failed';
    return 'queued';
  };

  const latestCompletedJob = [...history].reverse().find((job) => formatStatus(job.status) === 'completed');

  const handleDownload = async (jobId) => {
    if (!jobId) return;

    setDownloadingJobId(jobId);
    setError('');

    try {
      const response = await fetch(`${apiBaseUrl}/audit/${jobId}/download`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || 'Unable to download report');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `audit-report-${jobId}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.message || 'Unable to download report');
    } finally {
      setDownloadingJobId(null);
    }
  };

  const countdownLabel = `${String(Math.floor(countdown / 60)).padStart(2, '0')}:${String(countdown % 60).padStart(2, '0')}`;

  const renderOverview = () => (
    <div className="dashboard-grid">
      <section className="card card--hero">
        <div className="card__header">
          <div>
            <p className="eyebrow">New audit</p>
            <h2>Describe your business</h2>
          </div>
        </div>

        <p className="helper-text">Paste a concise overview of your company, market, and growth goals to generate a polished health report.</p>

        <form onSubmit={handleSubmit}>
          <label>
            Business description
            <textarea value={description} onChange={(event) => setDescription(event.target.value)} required minLength={20} />
          </label>
          <button className="btn btn--primary" disabled={loading}>
            {loading ? 'Submitting...' : 'Start audit'}
          </button>
        </form>

        {message ? <p className="success-text">{message}</p> : null}
        {error ? <p className="error-text">{error}</p> : null}
      </section>

      <section className="card">
        <div className="card__header">
          <div>
            <p className="eyebrow">Six-agent workflow</p>
            <h3>Audit pipeline</h3>
          </div>
          <span className={`status-pill status-pill--${pipelineStatus}`}>{pipelineStatus}</span>
        </div>

        <div className="pipeline-timeline">
          {agentSteps.map((step, index) => {
            let state = 'waiting';

            if (pipelineStatus === 'completed') {
              state = 'completed';
            } else if (pipelineStatus === 'failed') {
              state = index === failedAgentIndex ? 'failed' : 'waiting';
            } else if (pipelineStatus === 'processing') {
              if (index < activeAgentIndex) {
                state = 'completed';
              } else if (index === activeAgentIndex) {
                state = 'active';
              }
            }

            return (
              <div key={step.name} className={`pipeline-step pipeline-step--${state}`}>
                <div className={`pipeline-step__icon pipeline-step__icon--${state}`}>
                  {state === 'completed' ? '✓' : state === 'active' ? '●' : state === 'failed' ? '!' : '○'}
                </div>
                <div className="pipeline-step__body">
                  <p className={`pipeline-step__name pipeline-step__name--${state}`}>{step.name}</p>
                  <span className="pipeline-step__meta">{step.description}</span>
                  {state === 'active' ? <span className="pipeline-step__badge">Running...</span> : null}
                  {state === 'failed' ? <span className="pipeline-step__badge pipeline-step__badge--failed">Failed</span> : null}
                </div>
              </div>
            );
          })}
        </div>
      </section>

      <section className="card card--wide">
        <div className="card__header">
          <div>
            <p className="eyebrow">Download report</p>
            <h3>PDF summary</h3>
          </div>
          <button
            className="btn btn--success"
            type="button"
            onClick={() => handleDownload(latestCompletedJob?.job_id)}
            disabled={!latestCompletedJob || downloadingJobId === latestCompletedJob?.job_id}
          >
            {downloadingJobId === latestCompletedJob?.job_id ? 'Preparing...' : 'Download PDF'}
          </button>
        </div>

        <div className="pdf-panel">
          <div>
            <p className="helper-text">Your latest report remains available for the next</p>
            <div className="countdown-value">{countdownLabel}</div>
          </div>
          <div className="pdf-pill">Expires soon</div>
        </div>
      </section>

      <section className="card">
        <div className="card__header">
          <div>
            <p className="eyebrow">Recent activity</p>
            <h3>Audit history</h3>
          </div>
        </div>

        {history.length === 0 ? (
          <p className="helper-text">No audits yet. Submit one above to see it here.</p>
        ) : (
          <div className="history-table">
            <div className="history-table__head">
              <span>Job ID</span>
              <span>Status</span>
              <span>Created</span>
            </div>
            {history.map((job) => (
              <div className="history-table__row" key={job.job_id}>
                <div>
                  <p className="history-id">{job.job_id}</p>
                  <span className="history-subtext">Business health audit</span>
                </div>
                <span className={`status-pill status-pill--${formatStatus(job.status)}`}>
                  {job.status}
                </span>
                <span className="history-date">{new Date(job.created_at).toLocaleString()}</span>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );

  const renderReports = () => (
    <div className="dashboard-grid">
      <section className="card card--hero">
        <div className="card__header">
          <div>
            <p className="eyebrow">Completed reports</p>
            <h2>Audit reports</h2>
          </div>
        </div>

        <p className="helper-text">Download the latest completed audit reports whenever you need a shareable summary.</p>

        <div className="report-list">
          {history.filter((job) => formatStatus(job.status) === 'completed').length === 0 ? (
            <p className="helper-text">Completed reports will appear here once an audit finishes.</p>
          ) : (
            history
              .filter((job) => formatStatus(job.status) === 'completed')
              .map((job) => (
                <div className="report-item" key={job.job_id}>
                  <div>
                    <p className="history-id">{job.job_id}</p>
                    <span className="history-subtext">Completed audit report</span>
                  </div>
                  <button
                    className="btn btn--success"
                    type="button"
                    onClick={() => handleDownload(job.job_id)}
                    disabled={downloadingJobId === job.job_id}
                  >
                    {downloadingJobId === job.job_id ? 'Preparing...' : 'Download PDF'}
                  </button>
                </div>
              ))
          )}
        </div>
      </section>

      <section className="card">
        <div className="card__header">
          <div>
            <p className="eyebrow">Report availability</p>
            <h3>Download options</h3>
          </div>
        </div>

        <p className="helper-text">Each report includes a concise executive summary, the audit pipeline status, and next-step recommendations.</p>
      </section>
    </div>
  );

  const renderHistory = () => (
    <div className="dashboard-grid">
      <section className="card card--wide">
        <div className="card__header">
          <div>
            <p className="eyebrow">All activity</p>
            <h2>Audit history</h2>
          </div>
        </div>

        {history.length === 0 ? (
          <p className="helper-text">No audits yet. Start one from Overview to populate this history.</p>
        ) : (
          <div className="history-table">
            <div className="history-table__head">
              <span>Job ID</span>
              <span>Status</span>
              <span>Created</span>
            </div>
            {history.map((job) => (
              <div className="history-table__row" key={job.job_id}>
                <div>
                  <p className="history-id">{job.job_id}</p>
                  <span className="history-subtext">Business health audit</span>
                </div>
                <span className={`status-pill status-pill--${formatStatus(job.status)}`}>
                  {job.status}
                </span>
                <span className="history-date">{new Date(job.created_at).toLocaleString()}</span>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );

  if (view === 'reports') return renderReports();
  if (view === 'history') return renderHistory();
  return renderOverview();
}

export default DashboardPage;
