function HistoryPage({ history, handleDownload, downloadingJobId, getBusinessLabel, formatStatus, handleResume, handleRetry }) {
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
          <p className="helper-text">
            No audits yet. Start one from New Audit to populate this history.
          </p>
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
                  <span className="history-subtext history-subtext--mono">
                    {job.job_id || ''}
                  </span>
                </div>
                <span className={`status-pill ${
                  job.status === 'interview_pending'
                    ? 'status-pill--interview'
                    : `status-pill--${formatStatus(job.status)}`
                }`}>
                  {job.status === 'interview_pending'
                    ? 'Interview Pending'
                    : job.status}
                </span>
                <div className="history-date-cell">
                  <span className="history-date">
                    {new Date(job.created_at).toLocaleString()}
                  </span>
                  {job.status === 'interview_pending' ? (
                    <button
                      className="history-link history-link--resume"
                      type="button"
                      onClick={() => handleResume(
                        job.job_id,
                        job.business_name || job.business_description
                      )}
                    >
                      Resume Interview →
                    </button>
                  ) : formatStatus(job.status) === 'failed' ? (
                    <button
                      className="history-link history-link--retry"
                      type="button"
                      onClick={() => handleRetry(
                        job.job_id,
                        job.business_name || job.business_description
                      )}
                    >
                      Retry Audit →
                    </button>
                  ) : formatStatus(job.status) === 'completed' ? (
                    job.report_available ? (
                      <button
                        className="history-link"
                        type="button"
                        onClick={() => handleDownload(job.job_id)}
                      >
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
