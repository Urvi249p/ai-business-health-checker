function HistoryPage({ history, handleDownload, downloadingJobId, getBusinessLabel, formatStatus }) {
  return (
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
              <span>Business</span>
              <span>Status</span>
              <span>Created</span>
            </div>
            {history.map((job) => (
              <div className="history-table__row" key={job.job_id}>
                <div>
                  <p className="history-id">{getBusinessLabel(job)}</p>
                  <span className="history-subtext history-subtext--mono">{job.job_id || ''}</span>
                </div>
                <span className={`status-pill status-pill--${formatStatus(job.status)}`}>
                  {job.status}
                </span>
                <div className="history-date-cell">
                  <span className="history-date">{new Date(job.created_at).toLocaleString()}</span>
                  {formatStatus(job.status) === 'completed' ? (
                    job.report_available ? (
                      <button className="history-link" type="button" onClick={() => handleDownload(job.job_id)}>
                        Download
                      </button>
                    ) : (
                      <span className="history-expired">Expired</span>
                    )
                  ) : null}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

export default HistoryPage;
