import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import HomePage from './HomePage';
import AuditPage from './AuditPage';
import ReportsPage from './ReportsPage';
import HistoryPage from './HistoryPage';
import { 
  agentSteps, initialFormState,
  businessModelOptions, customerTypeOptions,
  revenueOptions, tagOptions, 
  challengeOptions, goalOptions 
} from '../constants/auditOptions';
import { useToast } from '../components/Toast';

function DashboardPage({ apiBaseUrl, token, apiFetch, view = 'home' }) {
  const navigate = useNavigate();
  const { showToast } = useToast();

  // ── Form state ──────────────────────────────────────
  const [formData, setFormData] = useState(initialFormState);
  const [currentStep, setCurrentStep] = useState(1);
  const [stepErrors, setStepErrors] = useState({});

  // ── Shared state ────────────────────────────────────
  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [downloadingJobId, setDownloadingJobId] = useState(null);

  // ── Pipeline state ──────────────────────────────────
  const [activeJobId, setActiveJobId] = useState('');
  const [pipelineStatus, setPipelineStatus] = useState('queued');
  const [activeAgentIndex, setActiveAgentIndex] = useState(-1);
  const [failedAgentIndex, setFailedAgentIndex] = useState(-1);

  // ── Interview state ─────────────────────────────────
  const [interviewStep, setInterviewStep] = useState('form');
  const [interviewQuestions, setInterviewQuestions] = useState([]);
  const [interviewAnswers, setInterviewAnswers] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [currentAnswer, setCurrentAnswer] = useState('');
  const [interviewLoading, setInterviewLoading] = useState(false);
  const [interviewError, setInterviewError] = useState('');
  const [retryProfile, setRetryProfile] = useState(null);
  const [retryLoading, setRetryLoading] = useState(false);
  const [retryParentJobId, setRetryParentJobId] = useState('');

  // ── Load history ────────────────────────────────────
  const loadHistory = async () => {
    setHistoryLoading(true);
    try {
      const response = await apiFetch('/audit/history');
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Unable to load audit history');
      setHistory(data);
    } catch (err) {
      setError(err.message || 'Unable to load history');
    } finally {
      setHistoryLoading(false);
    }
  };

  useEffect(() => { loadHistory(); }, [token]);

  // ── Autosave draft: load on mount
  useEffect(() => {
    try {
      const raw = localStorage.getItem('auditly_draft_form');
      if (!raw) return;
      const parsed = JSON.parse(raw);
      if (parsed && typeof parsed === 'object') {
        const { __currentStep, ...rest } = parsed;
        setFormData((current) => ({ ...current, ...rest }));
        if (__currentStep && Number.isFinite(__currentStep)) {
          setCurrentStep(__currentStep);
        }
      }
    } catch (err) {
      // ignore invalid JSON
      console.debug('Failed to load draft form', err);
    }
  }, []);

  // ── Autosave draft: debounce save when formData or currentStep change
  const _autosaveTimeout = useRef(null);
  useEffect(() => {
    // Skip saving untouched initial form on step 1
    try {
      const isInitial = currentStep === 1 && JSON.stringify(formData) === JSON.stringify(initialFormState);
      if (isInitial) return;
    } catch (e) {
      // fallthrough to save if stringify fails
    }

    if (_autosaveTimeout.current) {
      window.clearTimeout(_autosaveTimeout.current);
    }
    _autosaveTimeout.current = window.setTimeout(() => {
      try {
        const toSave = { ...formData, __currentStep: currentStep };
        localStorage.setItem('auditly_draft_form', JSON.stringify(toSave));
      } catch (err) {
        console.debug('Failed to save draft form', err);
      }
    }, 500);

    return () => {
      if (_autosaveTimeout.current) {
        window.clearTimeout(_autosaveTimeout.current);
        _autosaveTimeout.current = null;
      }
    };
  }, [formData, currentStep]);

  // ── Real-time updates via WebSocket (with polling fallback) ──
  useEffect(() => {
    if (!activeJobId || !token) return;

    let ws;
    let fallbackId = null;
    let connectTimeout = null;
    let closedByUs = false;

    const pollStatus = async () => {
      try {
        const response = await apiFetch(
          `/audit/${activeJobId}/status`,
          { headers: { } }
        );
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Unable to load status');

        const status = formatStatus(data.status);
        setPipelineStatus(status);

        if (status === 'queued') {
          setActiveAgentIndex(-1);
          setFailedAgentIndex(-1);
        } else if (status === 'completed') {
          setActiveAgentIndex(agentSteps.length - 1);
          setFailedAgentIndex(-1);
          await loadHistory();
        } else if (status === 'failed') {
          setFailedAgentIndex((c) => c >= 0 ? c : (activeAgentIndex >= 0 ? activeAgentIndex : 0));
        } else if (status === 'processing') {
          setFailedAgentIndex(-1);
          setActiveAgentIndex((c) => c < 0 ? 0 : c);
        }
      } catch (err) {
        setError(err.message || 'Unable to refresh status');
      }
    };

    const startFallbackPolling = (initial = true) => {
      if (fallbackId) return;
      if (initial) pollStatus();
      fallbackId = window.setInterval(pollStatus, 15000);
    };

    const stopFallbackPolling = () => {
      if (fallbackId) {
        window.clearInterval(fallbackId);
        fallbackId = null;
      }
    };

    try {
      // Build ws(s) URL from apiBaseUrl
      const wsProtocol = apiBaseUrl.startsWith('https') ? 'wss' : 'ws';
      const base = apiBaseUrl.replace(/^https?:/, '');
      const wsUrl = `${wsProtocol}:${base}/audit/${activeJobId}/ws?token=${encodeURIComponent(token)}`;

      ws = new WebSocket(wsUrl);

      // If connection doesn't open within ~3s, fall back to polling
      connectTimeout = window.setTimeout(() => {
        if (!ws || ws.readyState !== WebSocket.OPEN) {
          startFallbackPolling(true);
        }
      }, 3000);

      ws.onopen = () => {
        // server sends initial state; stop fallback polling if running
        stopFallbackPolling();
        if (connectTimeout) {
          window.clearTimeout(connectTimeout);
          connectTimeout = null;
        }
      };

      ws.onmessage = async (ev) => {
        try {
          const msg = JSON.parse(ev.data);
          if (msg.type === 'agent_update') {
            setPipelineStatus(formatStatus(msg.status || 'processing'));
            const idx = agentSteps.findIndex((s) => s.name === msg.current_agent);
            if (idx >= 0) {
              setActiveAgentIndex(idx);
            }
            setFailedAgentIndex(-1);
          } else if (msg.type === 'status_update') {
            const s = formatStatus(msg.status);
            setPipelineStatus(s);
            if (s === 'completed') {
              setActiveAgentIndex(agentSteps.length - 1);
              setFailedAgentIndex(-1);
              await loadHistory();
            } else if (s === 'failed') {
              setFailedAgentIndex((c) => c >= 0 ? c : (activeAgentIndex >= 0 ? activeAgentIndex : 0));
            }
          }
        } catch (err) {
          console.debug('Invalid WS message', err);
        }
      };

      ws.onerror = () => {
        startFallbackPolling(true);
      };

      ws.onclose = () => {
        if (!closedByUs) startFallbackPolling(true);
      };
    } catch (err) {
      startFallbackPolling(true);
    }

    return () => {
      closedByUs = true;
      if (connectTimeout) window.clearTimeout(connectTimeout);
      stopFallbackPolling();
      try { if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) ws.close(); } catch (e) {}
    };
  }, [activeJobId, token, apiBaseUrl]);

  // ── Helpers ─────────────────────────────────────────
  const formatStatus = (status) => {
    const s = String(status || 'queued').toLowerCase();
    if (s === 'completed' || s === 'success') return 'completed';
    if (s === 'processing' || s === 'running') return 'processing';
    if (s === 'failed' || s === 'error') return 'failed';
    return 'queued';
  };

  const getBusinessLabel = (job) => {
    const label = job.business_name || job.business_description || 'Untitled business';
    return label.length > 40 ? `${label.slice(0, 40)}...` : label;
  };

  const completedReports = history.filter(
    (job) => formatStatus(job.status) === 'completed' && job.report_available
  );

  // ── Form handlers ───────────────────────────────────
  const updateField = (field, value) => {
    setFormData((c) => ({ ...c, [field]: value }));
    setStepErrors((c) => ({ ...c, [field]: '' }));
    if (error) setError('');
  };

  const toggleTagSelection = (field, value) => {
    setFormData((c) => {
      const selected = c[field] || [];
      return {
        ...c,
        [field]: selected.includes(value)
          ? selected.filter((i) => i !== value)
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
        setError('Please complete the required fields.');
        return;
      }
    }
    setStepErrors({});
    setError('');
    setCurrentStep((c) => Math.min(c + 1, 4));
  };

  const handleBack = () => {
    setError('');
    setStepErrors({});
    setCurrentStep((c) => Math.max(c - 1, 1));
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
        years_in_business: formData.years_in_business ? Number(formData.years_in_business) : null,
        team_size: formData.team_size ? Number(formData.team_size) : null,
        business_model: formData.business_model || null,
        customer_type: formData.customer_type || null,
        monthly_revenue_range: formData.monthly_revenue_range || null,
        customer_sources: formData.customer_sources || [],
        current_marketing_channels: formData.current_marketing_channels || [],
        biggest_challenges: formData.biggest_challenges || [],
        goals: formData.goals || [],
        additional_notes: formData.additional_notes.trim() || null,
      };
      const response = await apiFetch('/audit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
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
      try { localStorage.removeItem('auditly_draft_form'); } catch (e) {}
      try { showToast('Audit started', 'success'); } catch (e) {}
    } catch (err) {
      setError(err.message || 'Unable to start audit');
    } finally {
      setLoading(false);
    }
  };

  // ── Interview handlers ──────────────────────────────
  const handleInterviewComplete = async () => {
    setInterviewLoading(true);
    setInterviewError('');
    try {
      const response = await apiFetch(
        `/audit/${activeJobId}/interview/complete`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ answers: interviewAnswers }),
        }
      );
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Unable to submit answers');
      setPipelineStatus('queued');
      setActiveAgentIndex(-1);
      setInterviewStep('pipeline');
      await loadHistory();
      try { showToast('Interview submitted, audit started', 'success'); } catch (e) {}
    } catch (err) {
      setInterviewError(err.message || 'Unable to submit answers');
    } finally {
      setInterviewLoading(false);
    }
  };

  const handleAnswerNext = () => {
    const updated = [...interviewAnswers];
    updated[currentQuestionIndex] = currentAnswer;
    setInterviewAnswers(updated);
    if (currentQuestionIndex < interviewQuestions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
      setCurrentAnswer(updated[currentQuestionIndex + 1] || '');
    } else {
      handleInterviewComplete();
    }
  };

  const handleAnswerBack = () => {
    if (currentQuestionIndex > 0) {
      const updated = [...interviewAnswers];
      updated[currentQuestionIndex] = currentAnswer;
      setInterviewAnswers(updated);
      setCurrentQuestionIndex(currentQuestionIndex - 1);
      setCurrentAnswer(updated[currentQuestionIndex - 1] || '');
    }
  };

  // ── Download ────────────────────────────────────────
  const handleDownload = async (jobId) => {
    if (!jobId) return;
    setDownloadingJobId(jobId);
    setError('');
    try {
      const response = await apiFetch(`/audit/${jobId}/download`);
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
      try { showToast('Report downloaded', 'success'); } catch (e) {}
    } catch (err) {
      setError(err.message || 'Unable to download report');
      try { showToast(err.message || 'Unable to download report', 'error'); } catch (e) {}
    } finally {
      setDownloadingJobId(null);
    }
  };

  const handleResume = async (jobId, businessName) => {
    setError('');
    setLoading(true);
    try {
      const response = await apiFetch(
        `/audit/${jobId}/status`,
        { headers: { } }
      );
      const data = await response.json();
      if (!response.ok) 
        throw new Error(data.detail || 'Unable to load audit');

      const questions = data.questions || [];
      if (questions.length === 0) {
        throw new Error('No interview questions found for this audit');
      }

      setActiveJobId(jobId);
      setInterviewQuestions(questions);
      setInterviewAnswers(new Array(questions.length).fill(''));
      setCurrentQuestionIndex(0);
      setCurrentAnswer('');
      setInterviewStep('interview');
      try { localStorage.removeItem('auditly_draft_form'); } catch (e) {}
      setFormData((current) => ({
        ...current,
        business_name: businessName || 'Your Business',
      }));

      navigate('/audit');

    } catch (err) {
      setError(err.message || 'Unable to resume audit');
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = async (jobId) => {
    setError('');
    setRetryLoading(true);
    try {
      // Fetch full job details including business_profile
      const response = await apiFetch(
        `/audit/${jobId}/detail`,
        { headers: { } }
      );
      const data = await response.json();
      if (!response.ok)
        throw new Error(data.detail || 'Unable to load audit details');

      const profile = data.business_profile || {};

      // Store the profile for retry confirmation screen
      setRetryProfile(profile);
      setRetryParentJobId(jobId);

      // Pre-fill formData with the original profile
      setFormData({
        business_name: profile.business_name || '',
        business_type: profile.business_type || '',
        location: profile.location || '',
        years_in_business: profile.years_in_business || '',
        team_size: profile.team_size || '',
        business_model: profile.business_model || '',
        customer_type: profile.customer_type || '',
        monthly_revenue_range: profile.monthly_revenue_range || '',
        customer_sources: profile.customer_sources || [],
        current_marketing_channels: profile.current_marketing_channels || [],
        biggest_challenges: profile.biggest_challenges || [],
        goals: profile.goals || [],
        additional_notes: profile.additional_notes || '',
      });

      // Reset state
      setCurrentStep(1);
      setActiveJobId('');
      setPipelineStatus('queued');
      setActiveAgentIndex(-1);
      setFailedAgentIndex(-1);
      setInterviewStep('retry_confirm');

      navigate('/audit');

    } catch (err) {
      setError(err.message || 'Unable to load audit for retry');
    } finally {
      setRetryLoading(false);
    }
  };

  const handleRetrySubmit = async () => {
    setLoading(true);
    setError('');
    setMessage('');
    try {
      const response = await apiFetch(
        `/audit/retry/${retryParentJobId}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );
      const data = await response.json();
      if (!response.ok)
        throw new Error(data.detail || 'Unable to retry audit');

      setActiveJobId(data.job_id);
      setInterviewQuestions(data.questions || []);
      setInterviewAnswers(
        new Array(data.questions?.length || 0).fill('')
      );
      setCurrentQuestionIndex(0);
      setCurrentAnswer('');
      setRetryProfile(null);
      setRetryParentJobId('');
      setInterviewStep('interview');
      try { localStorage.removeItem('auditly_draft_form'); } catch (e) {}
      try { showToast('Retry started', 'success'); } catch (e) {}

    } catch (err) {
      setError(err.message || 'Unable to retry audit');
    } finally {
      setLoading(false);
    }
  };

  // ── Shared props ────────────────────────────────────
  const sharedProps = {
    handleDownload,
    downloadingJobId,
    getBusinessLabel,
    formatStatus,
    handleResume,
    handleRetry,
  };

  const auditProps = {
    formData, currentStep, stepErrors, loading, error, message,
    interviewStep, interviewQuestions, interviewAnswers,
    currentQuestionIndex, currentAnswer, setCurrentAnswer,
    interviewLoading, interviewError,
    pipelineStatus, activeAgentIndex, failedAgentIndex,
    updateField, toggleTagSelection,
    handleNext, handleBack, handleSubmit,
    handleAnswerNext, handleAnswerBack, handleInterviewComplete,
    agentSteps,
    businessModelOptions, customerTypeOptions, revenueOptions,
    tagOptions, challengeOptions, goalOptions,
    retryProfile, retryLoading, handleRetrySubmit,
  };

  // ── View routing ────────────────────────────────────
  if (view === 'home') return <HomePage />;
  if (view === 'reports') return <ReportsPage completedReports={completedReports} {...sharedProps} loading={historyLoading} />;
  if (view === 'history') return <HistoryPage history={history} {...sharedProps} loading={historyLoading} />;
  return <AuditPage {...auditProps} />;
}

export default DashboardPage;
