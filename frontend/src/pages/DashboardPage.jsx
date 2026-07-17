import { useEffect, useState } from 'react';

const agentSteps = [
  { name: 'Business Analyst', description: 'Extract and structure key business information' },
  { name: 'Strategic SWOT Analyst', description: 'Produce a detailed SWOT analysis' },
  { name: 'Pricing Strategy Consultant', description: 'Recommend the optimal pricing model' },
  { name: 'Growth Strategy Consultant', description: 'Create a detailed 90-day action plan' },
  { name: 'Business Report Writer', description: 'Assemble all research into a final report' },
];

const initialFormState = {
  business_name: '',
  business_type: '',
  location: '',
  years_in_business: '',
  team_size: '',
  business_model: '',
  customer_type: '',
  monthly_revenue_range: '',
  customer_sources: [],
  current_marketing_channels: [],
  biggest_challenges: [],
  goals: [],
  additional_notes: '',
};

const businessModelOptions = ['B2B', 'B2C', 'D2C', 'Marketplace', 'Other'];
const customerTypeOptions = ['Retail', 'Enterprise', 'SME', 'Consumer', 'Mixed'];
const revenueOptions = ['Under ₹1L', '₹1L–₹5L', '₹5L–₹20L', '₹20L–₹50L', 'Above ₹50L', 'Prefer not to say'];
const tagOptions = ['Walk-ins', 'Instagram', 'Facebook', 'Google Ads', 'WhatsApp', 'Referrals', 'Website', 'LinkedIn', 'Cold Outreach', 'Other'];
const challengeOptions = ['Low sales', 'High costs', 'Low repeat customers', 'Poor online presence', 'Hiring', 'Cash flow', 'Pricing', 'Competition', 'Operations', 'Marketing ROI'];
const goalOptions = ['Increase revenue', 'Reduce costs', 'Expand to new markets', 'Build online presence', 'Improve retention', 'Launch new product', 'Raise funding', 'Automate operations'];

function DashboardPage({ apiBaseUrl, token, view = 'overview' }) {
  const [formData, setFormData] = useState(initialFormState);
  const [currentStep, setCurrentStep] = useState(1);
  const [stepErrors, setStepErrors] = useState({});
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
  const [interviewStep, setInterviewStep] = useState('form');
  const [interviewQuestions, setInterviewQuestions] = useState([]);
  const [interviewAnswers, setInterviewAnswers] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [currentAnswer, setCurrentAnswer] = useState('');
  const [interviewLoading, setInterviewLoading] = useState(false);
  const [interviewError, setInterviewError] = useState('');

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

  const updateField = (field, value) => {
    setFormData((current) => ({ ...current, [field]: value }));
    setStepErrors((current) => ({ ...current, [field]: '' }));
    if (error) setError('');
  };

  const toggleTagSelection = (field, value) => {
    setFormData((current) => {
      const selected = current[field] || [];
      return {
        ...current,
        [field]: selected.includes(value)
          ? selected.filter((item) => item !== value)
          : [...selected, value],
      };
    });
    if (error) setError('');
  };

  const handleNext = () => {
    if (currentStep === 1) {
      const errors = {};
      if (!formData.business_name.trim()) errors.business_name = 'Business name is required';
      if (!formData.business_type.trim()) errors.business_type = 'Business type is required';
      setStepErrors(errors);
      if (Object.keys(errors).length > 0) {
        setError('Please complete the required fields to continue.');
        return;
      }
    }

    setStepErrors({});
    setError('');
    setCurrentStep((current) => Math.min(current + 1, 4));
  };

  const handleBack = () => {
    setError('');
    setStepErrors({});
    setCurrentStep((current) => Math.max(current - 1, 1));
  };

  const handleSubmit = async (event) => {
    if (event && event.preventDefault) event.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');

    try {
      const payload = {
        business_name: formData.business_name.trim(),
        business_type: formData.business_type.trim(),
        location: formData.location.trim() || null,
        years_in_business: formData.years_in_business
          ? Number(formData.years_in_business) : null,
        team_size: formData.team_size
          ? Number(formData.team_size) : null,
        business_model: formData.business_model || null,
        customer_type: formData.customer_type || null,
        monthly_revenue_range: formData.monthly_revenue_range || null,
        customer_sources: formData.customer_sources || [],
        current_marketing_channels: formData.current_marketing_channels || [],
        biggest_challenges: formData.biggest_challenges || [],
        goals: formData.goals || [],
        additional_notes: formData.additional_notes.trim() || null,
      };

      const response = await fetch(`${apiBaseUrl}/audit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Unable to start audit');

      setActiveJobId(data.job_id);
      setInterviewQuestions(data.questions || []);
      setInterviewAnswers(new Array(data.questions?.length || 0).fill(''));
      setCurrentQuestionIndex(0);
      setCurrentAnswer('');
      setInterviewStep('interview');

    } catch (err) {
      setError(err.message || 'Unable to start audit');
    } finally {
      setLoading(false);
    }
  };

  const handleInterviewComplete = async () => {
    setInterviewLoading(true);
    setInterviewError('');

    try {
      const response = await fetch(
        `${apiBaseUrl}/audit/${activeJobId}/interview/complete`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ answers: interviewAnswers }),
        }
      );

      const data = await response.json();
      if (!response.ok) 
        throw new Error(data.detail || 'Unable to submit answers');

      setPipelineStatus('queued');
      setActiveAgentIndex(-1);
      setInterviewStep('pipeline');
      await loadHistory();

    } catch (err) {
      setInterviewError(err.message || 'Unable to submit answers');
    } finally {
      setInterviewLoading(false);
    }
  };

  const handleAnswerNext = () => {
    const updatedAnswers = [...interviewAnswers];
    updatedAnswers[currentQuestionIndex] = currentAnswer;
    setInterviewAnswers(updatedAnswers);

    if (currentQuestionIndex < interviewQuestions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
      setCurrentAnswer(
        updatedAnswers[currentQuestionIndex + 1] || ''
      );
    } else {
      handleInterviewComplete();
    }
  };

  const handleAnswerBack = () => {
    if (currentQuestionIndex > 0) {
      const updatedAnswers = [...interviewAnswers];
      updatedAnswers[currentQuestionIndex] = currentAnswer;
      setInterviewAnswers(updatedAnswers);
      setCurrentQuestionIndex(currentQuestionIndex - 1);
      setCurrentAnswer(
        updatedAnswers[currentQuestionIndex - 1] || ''
      );
    }
  };

  const formatStatus = (status) => {
    const normalized = String(status || 'queued').toLowerCase();
    if (normalized === 'completed' || normalized === 'success') return 'completed';
    if (normalized === 'processing' || normalized === 'running') return 'processing';
    if (normalized === 'failed' || normalized === 'error') return 'failed';
    return 'queued';
  };

  const completedReports = history.filter((job) => formatStatus(job.status) === 'completed' && job.report_available);
  const latestCompletedJob = completedReports[0] || null;
  const getBusinessLabel = (job) => {
    const label = job.business_name || job.business_description || 'Untitled business';
    return label.length > 40 ? `${label.slice(0, 40)}...` : label;
  };

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
                setInterviewStep('form');
                setActiveJobId('');
                setPipelineStatus('queued');
                setActiveAgentIndex(-1);
              }}
            >
              ← Start New Audit
            </button>
          </div>
        ) : null}
      </section>
    </div>
  );

  const renderOverview = () => {
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
              disabled={!latestCompletedJob || !latestCompletedJob.report_available || downloadingJobId === latestCompletedJob?.job_id}
            >
              {downloadingJobId === latestCompletedJob?.job_id ? 'Preparing...' : latestCompletedJob?.report_available ? 'Download PDF' : 'Unavailable'}
            </button>
          </div>

          <div className="pdf-panel">
            <div>
              <p className="helper-text">{latestCompletedJob?.report_available ? 'Your latest report remains available for the next' : 'The latest report has expired and will be removed automatically.'}</p>
              <div className="countdown-value">{latestCompletedJob?.report_available ? countdownLabel : '00:00'}</div>
            </div>
            <div className="pdf-pill">{latestCompletedJob?.report_available ? 'Expires soon' : 'Unavailable'}</div>
          </div>
        </section>

        <section className="card">
          <div className="card__header">
            <div>
              <p className="eyebrow">What to expect</p>
              <h3>What your audit covers</h3>
            </div>
          </div>

          <p className="helper-text">Our AI analyses your business across 4 dimensions and delivers a professional PDF report.</p>

          <div className="expectation-grid">
            <div className="expectation-card">
              <div className="expectation-card__icon">◻</div>
              <h4>SWOT Analysis</h4>
              <p>Strengths, weaknesses, opportunities and threats specific to your business</p>
            </div>
            <div className="expectation-card">
              <div className="expectation-card__icon">🏷</div>
              <h4>Pricing Strategy</h4>
              <p>The optimal pricing model and specific price points for your market and goals</p>
            </div>
            <div className="expectation-card">
              <div className="expectation-card__icon">↗</div>
              <h4>90-Day Growth Plan</h4>
              <p>A phase-by-phase action plan with clear owners, metrics and expected outcomes</p>
            </div>
            <div className="expectation-card">
              <div className="expectation-card__icon">📄</div>
              <h4>PDF Report</h4>
              <p>A professionally formatted report ready to present to partners, investors or your team</p>
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
  };

  const renderReports = () => (
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
              <p>Completed reports are available for 30 minutes after generation. Start a new audit to generate one.</p>
              <button className="btn btn--primary" type="button" onClick={() => window.location.assign('/overview')}>
                Start New Audit
              </button>
            </div>
          ) : (
            completedReports.map((job) => (
              <div className="report-item" key={job.job_id}>
                <div>
                  <p className="history-id">{getBusinessLabel(job)}</p>
                  <span className="history-subtext">{new Date(job.updated_at || job.created_at).toLocaleString()}</span>
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

  if (view === 'reports') return renderReports();
  if (view === 'history') return renderHistory();
  return renderOverview();
}

export default DashboardPage;
