function OverviewPage({
  apiBaseUrl,
  token,
  formData,
  setFormData,
  currentStep,
  setCurrentStep,
  stepErrors,
  setStepErrors,
  loading,
  error,
  setError,
  message,
  activeJobId,
  pipelineStatus,
  activeAgentIndex,
  failedAgentIndex,
  handleSubmit,
  handleNext,
  handleBack,
  updateField,
  toggleTagSelection,
  agentSteps,
  businessModelOptions,
  customerTypeOptions,
  revenueOptions,
  tagOptions,
  challengeOptions,
  goalOptions,
}) {
  return (
    <div className="dashboard-grid">
      <section className="card card--hero audit-form-card">
        <div className="card__header audit-form-card__header">
          <div>
            <p className="eyebrow">New audit</p>
            <h2>{currentStep === 1 ? 'Tell us about your business' : currentStep === 2 ? 'How does your business operate?' : currentStep === 3 ? 'Where do your customers come from?' : 'What are you trying to solve?'}</h2>
          </div>
          <div className="audit-progress">
            <span className="audit-progress__label">Step {currentStep} of 4</span>
            <div className="audit-progress__bar">
              <div className="audit-progress__fill" style={{ width: `${(currentStep / 4) * 100}%` }} />
            </div>
          </div>
        </div>

        <div className="audit-form-card__body">
          <p className="helper-text">
            {currentStep === 1
              ? 'We\'ll use this to personalize your audit.'
              : currentStep === 2
                ? 'This helps us tailor the strategy to your model.'
                : currentStep === 3
                  ? 'Select all that apply.'
                  : 'Be honest — this directly shapes your audit recommendations.'}
          </p>

          <form onSubmit={(e) => e.preventDefault()}>
            {currentStep === 1 ? (
              <div className="audit-step">
                <div className="audit-grid">
                  <label>
                    Business Name
                    <input
                      value={formData.business_name}
                      onChange={(event) => updateField('business_name', event.target.value)}
                      placeholder="e.g. Northstar Studio"
                      className={stepErrors.business_name ? 'audit-input audit-input--error' : 'audit-input'}
                    />
                    {stepErrors.business_name ? <span className="error-text">Business name is required</span> : null}
                  </label>
                  <label>
                    Business Type
                    <input
                      value={formData.business_type}
                      onChange={(event) => updateField('business_type', event.target.value)}
                      placeholder="e.g. Bakery, SaaS, Consulting"
                      className={stepErrors.business_type ? 'audit-input audit-input--error' : 'audit-input'}
                    />
                    {stepErrors.business_type ? <span className="error-text">Business type is required</span> : null}
                  </label>
                </div>
                <div className="audit-grid">
                  <label>
                    Location
                    <input value={formData.location} onChange={(event) => updateField('location', event.target.value)} placeholder="e.g. Mumbai, Delhi" />
                  </label>
                  <label>
                    Years in Business
                    <input type="number" value={formData.years_in_business} onChange={(event) => updateField('years_in_business', event.target.value)} min="0" />
                  </label>
                </div>
                <div className="audit-grid">
                  <label>
                    Team Size
                    <input type="number" value={formData.team_size} onChange={(event) => updateField('team_size', event.target.value)} min="0" placeholder="Number of employees" />
                  </label>
                </div>
              </div>
            ) : null}

            {currentStep === 2 ? (
              <div className="audit-step">
                <label>Business Model</label>
                <div className="pill-group">
                  {businessModelOptions.map((option) => (
                    <button
                      key={option}
                      type="button"
                      className={`pill-button ${formData.business_model === option ? 'pill-button--selected' : ''}`}
                      onClick={() => updateField('business_model', option)}
                    >
                      {option}
                    </button>
                  ))}
                </div>

                <label>Customer Type</label>
                <div className="pill-group">
                  {customerTypeOptions.map((option) => (
                    <button
                      key={option}
                      type="button"
                      className={`pill-button ${formData.customer_type === option ? 'pill-button--selected' : ''}`}
                      onClick={() => updateField('customer_type', option)}
                    >
                      {option}
                    </button>
                  ))}
                </div>

                <label>Monthly Revenue Range</label>
                <div className="pill-group">
                  {revenueOptions.map((option) => (
                    <button
                      key={option}
                      type="button"
                      className={`pill-button ${formData.monthly_revenue_range === option ? 'pill-button--selected' : ''}`}
                      onClick={() => updateField('monthly_revenue_range', option)}
                    >
                      {option}
                    </button>
                  ))}
                </div>
              </div>
            ) : null}

            {currentStep === 3 ? (
              <div className="audit-step">
                <label>Customer Sources</label>
                <div className="pill-group">
                  {tagOptions.map((option) => (
                    <button
                      key={option}
                      type="button"
                      className={`pill-button ${formData.customer_sources.includes(option) ? 'pill-button--selected' : ''}`}
                      onClick={() => toggleTagSelection('customer_sources', option)}
                    >
                      {option}
                    </button>
                  ))}
                </div>

                <label>Which channels are you actively marketing on?</label>
                <div className="pill-group">
                  {tagOptions.map((option) => (
                    <button
                      key={option}
                      type="button"
                      className={`pill-button ${formData.current_marketing_channels.includes(option) ? 'pill-button--selected' : ''}`}
                      onClick={() => toggleTagSelection('current_marketing_channels', option)}
                    >
                      {option}
                    </button>
                  ))}
                </div>
              </div>
            ) : null}

            {currentStep === 4 ? (
              <div className="audit-step">
                <label>Biggest Challenges</label>
                <div className="pill-group">
                  {challengeOptions.map((option) => (
                    <button
                      key={option}
                      type="button"
                      className={`pill-button ${formData.biggest_challenges.includes(option) ? 'pill-button--selected' : ''}`}
                      onClick={() => toggleTagSelection('biggest_challenges', option)}
                    >
                      {option}
                    </button>
                  ))}
                </div>

                <label>Goals</label>
                <div className="pill-group">
                  {goalOptions.map((option) => (
                    <button
                      key={option}
                      type="button"
                      className={`pill-button ${formData.goals.includes(option) ? 'pill-button--selected' : ''}`}
                      onClick={() => toggleTagSelection('goals', option)}
                    >
                      {option}
                    </button>
                  ))}
                </div>

                <label>
                  Additional Notes
                  <textarea
                    value={formData.additional_notes}
                    onChange={(event) => updateField('additional_notes', event.target.value)}
                    maxLength={500}
                    placeholder="Anything else you'd like the AI to know about your business?"
                  />
                  <span className="helper-text helper-text--tight">{formData.additional_notes.length} / 500 characters</span>
                </label>
              </div>
            ) : null}

            <div className="audit-step-actions">
              {currentStep > 1 ? (
                <button type="button" className="btn btn--secondary" onClick={handleBack}>
                  Back
                </button>
              ) : <div />}
              {currentStep < 4 ? (
                <button type="button" className="btn btn--primary" onClick={handleNext} disabled={loading}>
                  Next
                </button>
              ) : (
                <button
                  className="btn btn--primary"
                  disabled={loading}
                  type="button"
                  onClick={handleSubmit}
                >
                  {loading ? 'Starting...' : 'Start My Audit →'}
                </button>
              )}
            </div>
          </form>

          {message ? <p className="success-text">{message}</p> : null}
          {error ? <p className="error-text">{error}</p> : null}
        </div>
      </section>

      <section className="card card--pipeline">
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
              <div key={step.name}
                className={`pipeline-step pipeline-step--${state}`}>
                <div className={`pipeline-step__icon pipeline-step__icon--${state}`}>
                  {state === 'completed'
                    ? '✓'
                    : state === 'failed'
                      ? '!'
                      : <span className="pipeline-step__number">{index + 1}</span>}
                </div>
                <div className="pipeline-step__body">
                  <div>
                    <p className={`pipeline-step__name pipeline-step__name--${state}`}>
                      {step.name}
                    </p>
                    <span className="pipeline-step__meta">{step.description}</span>
                  </div>
                  <div>
                    {state === 'active'
                      ? <span className="pipeline-step__badge">Running...</span>
                      : null}
                    {state === 'failed'
                      ? <span className="pipeline-step__badge pipeline-step__badge--failed">
                          Failed
                        </span>
                      : null}
                    {state === 'completed'
                      ? <span className="pipeline-step__badge"
                          style={{background:'#ECFDF5', color:'#10B981'}}>
                          Done
                        </span>
                      : null}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      <section className="card card--wide">
        <div className="card__header">
          <div>
            <p className="eyebrow">What to expect</p>
            <h3>What your audit covers</h3>
          </div>
        </div>

        <p className="helper-text">Our AI analyses your business across 4 dimensions and delivers a professional PDF report.</p>

        <div className="expectation-list">
          <div className="expectation-item">
            <div className="expectation-item__icon">◻</div>
            <div className="expectation-item__content">
              <h4>SWOT Analysis</h4>
              <p>Strengths, weaknesses, opportunities and threats specific to your business — grounded in facts, not generic templates.</p>
            </div>
          </div>
          <div className="expectation-item">
            <div className="expectation-item__icon">🏷</div>
            <div className="expectation-item__content">
              <h4>Pricing Strategy</h4>
              <p>The optimal pricing model and specific price points for your market, customer type, and goals.</p>
            </div>
          </div>
          <div className="expectation-item">
            <div className="expectation-item__icon">↗</div>
            <div className="expectation-item__content">
              <h4>90-Day Growth Plan</h4>
              <p>A phase-by-phase action plan with clear owners, success metrics and expected outcomes for each phase.</p>
            </div>
          </div>
          <div className="expectation-item">
            <div className="expectation-item__icon">📄</div>
            <div className="expectation-item__content">
              <h4>PDF Report</h4>
              <p>A professionally formatted report ready to present to partners, investors or your team.</p>
            </div>
          </div>
        </div>

        <div className="expectation-strip">
          <div className="expectation-strip__item">
            <span className="expectation-strip__icon">🕒</span>
            <span>Estimated time: 3–5 minutes depending on business complexity</span>
          </div>
          <div className="expectation-strip__item expectation-strip__item--secondary">
            <span className="expectation-strip__icon">✓</span>
            <span>Report auto-deleted after 30 minutes — download promptly</span>
          </div>
        </div>
      </section>
    </div>
  );
}

export default OverviewPage;
