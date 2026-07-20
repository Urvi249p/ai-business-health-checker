import { useEffect, useState } from 'react';
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

function DashboardPage({ apiBaseUrl, token, view = 'home' }) {

  // ── Form state ──────────────────────────────────────
  const [formData, setFormData] = useState(initialFormState);
  const [currentStep, setCurrentStep] = useState(1);
  const [stepErrors, setStepErrors] = useState({});

  // ── Shared state ────────────────────────────────────
  const [history, setHistory] = useState([]);
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

  // ── Load history ────────────────────────────────────
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

  useEffect(() => { loadHistory(); }, [token]);

  // ── Status polling ──────────────────────────────────
  useEffect(() => {
    if (!activeJobId || !token) return;
    let cancelled = false;

    const pollStatus = async () => {
      try {
        const response = await fetch(
          `${apiBaseUrl}/audit/${activeJobId}/status`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail);
        if (cancelled) return;

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
        if (!cancelled) setError(err.message || 'Unable to refresh status');
      }
    };

    pollStatus();
    const id = window.setInterval(pollStatus, 5000);
    return () => { cancelled = true; window.clearInterval(id); };
  }, [activeJobId, token, apiBaseUrl]);

  // ── Agent progress simulation ───────────────────────
  useEffect(() => {
    if (pipelineStatus !== 'processing' || activeAgentIndex >= agentSteps.length - 1) return;
    const id = window.setInterval(() => {
      setActiveAgentIndex((c) => c < 0 ? 0 : c + 1 >= agentSteps.length ? c : c + 1);
    }, 15000);
    return () => window.clearInterval(id);
  }, [pipelineStatus, activeAgentIndex]);

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

  // ── Interview handlers ──────────────────────────────
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
      if (!response.ok) throw new Error(data.detail || 'Unable to submit answers');
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

  const handleResume = async (jobId, businessName) => {
    setError('');
    setLoading(true);
    try {
      const response = await fetch(
        `${apiBaseUrl}/audit/${jobId}/status`,
        { headers: { Authorization: `Bearer ${token}` } }
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
      setFormData((current) => ({
        ...current,
        business_name: businessName || 'Your Business',
      }));

      window.location.assign('/audit');

    } catch (err) {
      setError(err.message || 'Unable to resume audit');
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
  };

  // ── View routing ────────────────────────────────────
  if (view === 'home') return <HomePage />;
  if (view === 'reports') return <ReportsPage completedReports={completedReports} {...sharedProps} />;
  if (view === 'history') return <HistoryPage history={history} {...sharedProps} />;
  return <AuditPage {...auditProps} />;
}

export default DashboardPage;
