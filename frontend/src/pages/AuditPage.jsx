import {
  agentSteps,
  businessModelOptions,
  customerTypeOptions,
  revenueOptions,
  tagOptions,
  challengeOptions,
  goalOptions
} from '../constants/auditOptions';

function AuditPage({
  formData, currentStep, stepErrors, loading, error, message,
  interviewStep, interviewQuestions, interviewAnswers,
  currentQuestionIndex, currentAnswer, setCurrentAnswer,
  interviewLoading, interviewError,
  pipelineStatus, activeAgentIndex, failedAgentIndex,
  updateField, toggleTagSelection,
  handleNext, handleBack, handleSubmit,
  handleAnswerNext, handleAnswerBack, handleInterviewComplete,
  retryProfile, retryLoading, handleRetrySubmit,
}) {

  const renderRetryConfirm = () => {
    const profile = retryProfile || {};
    const fields = [
      { label: 'Business Name', value: profile.business_name },
      { label: 'Business Type', value: profile.business_type },
      { label: 'Location', value: profile.location },
      { label: 'Years in Business', value: profile.years_in_business },
      { label: 'Team Size', value: profile.team_size },
      { label: 'Business Model', value: profile.business_model },
      { label: 'Customer Type', value: profile.customer_type },
      { label: 'Monthly Revenue', value: profile.monthly_revenue_range },
      { label: 'Customer Sources', value: (profile.customer_sources || []).join(', ') },
      { label: 'Challenges', value: (profile.biggest_challenges || []).join(', ') },
      { label: 'Goals', value: (profile.goals || []).join(', ') },
    ].filter((f) => f.value);

    return (
      <div className="dashboard-grid">
        <section className="card card--wide">
          <div className="card__header">
            <div>
              <p className="eyebrow">RETRY AUDIT</p>
              <h3>Review your business profile</h3>
            </div>
          </div>

          <p className="helper-text">
            We found your previous business profile. 
            Review the details below and click 
            "Start Audit" to generate a new report 
            with fresh AI analysis.
          </p>

          <div className="retry-profile">
            {fields.map((field) => (
              <div className="retry-profile__row" key={field.label}>
                <span className="retry-profile__label">
                  {field.label}
                </span>
                <span className="retry-profile__value">
                  {String(field.value)}
                </span>
              </div>
            ))}
          </div>

          {error ? (
            <p className="error-text" style={{ marginTop: 12 }}>
              {error}
            </p>
          ) : null}

          <div className="retry-actions">
            <button
              className="btn btn--secondary"
              type="button"
              onClick={() => window.location.assign('/history')}
            >
              ← Back to History
            </button>
            <button
              className="btn btn--primary"
              type="button"
              onClick={handleRetrySubmit}
              disabled={loading || retryLoading}
            >
              {loading ? 'Starting...' : 'Start Audit with This Profile →'}
            </button>
          </div>
        </section>
      </div>
    );
  };

  const renderInterview = () => {
    const question = interviewQuestions[currentQuestionIndex];
    const totalQuestions = interviewQuestions.length;
    const progress = ((currentQuestionIndex) / totalQuestions) * 100;
    const isLast = currentQuestionIndex === totalQuestions - 1;

    return (
      <div className="dashboard-grid">
        <section className="card card--wide">
          <div className="interview-header">
            <p className="eyebrow">QUICK FOLLOW-UP</p>
            <h3>A few targeted questions about {formData.business_name}</h3>
            <p className="helper-text">
              These questions help the AI generate a more
              accurate, personalized report based on your
              specific situation.
            </p>
          </div>

          <div className="interview-progress">
            <span className="interview-progress__label">
              Question {currentQuestionIndex + 1} of {totalQuestions}
            </span>
            <div className="interview-progress__bar">
              <div
                className="interview-progress__fill"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          <div className="interview-question-card">
            <p className="interview-question__text">{question}</p>
          </div>

          <div className="interview-answer">
            <textarea
              className="interview-answer__input"
              placeholder="Type your answer here..."
              value={currentAnswer}
              onChange={(e) => setCurrentAnswer(e.target.value)}
              rows={4}
              disabled={interviewLoading}
            />
          </div>

          {interviewError ? (
            <p className="error-text">{interviewError}</p>
          ) : null}

          <div className="interview-actions">
            <button
              className="btn btn--secondary"
              type="button"
              onClick={handleAnswerBack}
              disabled={currentQuestionIndex === 0 || interviewLoading}
            >
              ← Back
            </button>
            <button
              className="btn btn--primary"
              type="button"
              onClick={handleAnswerNext}
              disabled={!currentAnswer.trim() || interviewLoading}
            >
              {interviewLoading
                ? 'Starting audit...'
                : isLast
                  ? 'Start My Audit →'
                  : 'Next →'}
            </button>
          </div>

          <div className="interview-skip">
            <button
              className="interview-skip__btn"
              type="button"
              onClick={handleInterviewComplete}
              disabled={interviewLoading}
            >
              Skip interview and start audit now
            </button>
          </div>
        </section>
      </div>
    );
  };

  const renderPipeline = () => (
    <div className="dashboard-grid">
      <section className="card card--wide card--pipeline">
        <div className="card__header">
          <div>
            <p className="eyebrow">Five-agent workflow</p>
            <h3>Audit pipeline — {formData.business_name}</h3>
          </div>
          <span className={`status-pill status-pill--${pipelineStatus}`}>
            {pipelineStatus.charAt(0).toUpperCase() + pipelineStatus.slice(1)}
          </span>
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
                  {state === 'completed' ? '✓'
                    : state === 'active' ? '●'
                    : state === 'failed' ? '!'
                    : index + 1}
                </div>
                <div className="pipeline-step__body">
                  <p className={`pipeline-step__name pipeline-step__name--${state}`}>
                    {step.name}
                  </p>
                  <span className="pipeline-step__meta">
                    {step.description}
                  </span>
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
            );
          })}
        </div>

        {pipelineStatus === 'completed' ? (
          <div className="pipeline-complete">
            <p className="pipeline-complete__text">
              ✅ Your audit report is ready!
            </p>
            <button
              className="btn btn--success"
              type="button"
              onClick={() => window.location.assign('/reports')}
            >
              View & Download Report →
            </button>
          </div>
        ) : null}

        {pipelineStatus === 'failed' ? (
          <div className="pipeline-failed">
            <p className="pipeline-failed__text">
              ❌ The audit encountered an error.
              Please try again.
            </p>
            <button
              className="btn btn--secondary"
              type="button"
              onClick={() => {
                window.location.reload();
              }}
            >
              ← Start New Audit
            </button>
          </div>
        ) : null}
      </section>
    </div>
  );

  if (interviewStep === 'retry_confirm') {
    return renderRetryConfirm();
  }

  if (interviewStep === 'interview') {
    return renderInterview();
  }

  if (interviewStep === 'pipeline') {
    return renderPipeline();
  }

  return (
    <div className="dashboard-grid">
      <section className="card card--hero audit-form-card">
        <div className="card__header audit-form-card__header">
          <div>
            <p className="eyebrow">New audit</p>
            <h2>
              {currentStep === 1
                ? 'Tell us about your business'
                : currentStep === 2
                  ? 'How does your business operate?'
                  : currentStep === 3
                    ? 'Where do your customers come from?'
                    : 'What are you trying to solve?'}
            </h2>
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
    </div>
  );
}

export default AuditPage;
