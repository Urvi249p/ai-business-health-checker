function ReportsPage({ completedReports, handleDownload, downloadingJobId, getBusinessLabel }) {
  return (
    <div className="dashboard-grid">
      <section className="card card--hero">
        <div className="card__header">
          <div>
            <p className="eyebrow">Completed reports</p>
            <h2>Audit reports</h2>
          </div>
        </div>
        <div className="report-list">
          {completedReports.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state__icon">📄</div>
              <h3>No reports available</h3>
              <p>Completed reports are available for 30 minutes after 
              generation. Start a new audit to generate one.</p>
              <button
                className="btn btn--primary"
                type="button"
                onClick={() => window.location.assign('/audit')}
              >
                Start New Audit
              </button>
            </div>
          ) : (
            completedReports.map((job) => (
              <div className="report-item" key={job.job_id}>
                <div>
                  <p className="history-id">{getBusinessLabel(job)}</p>
                  <span className="history-subtext">
                    {new Date(job.updated_at || job.created_at).toLocaleString()}
                  </span>
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
    </div>
  );
}

export default ReportsPage;
