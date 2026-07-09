import { useEffect, useState } from 'react';
import OverviewPage from '../components/OverviewPage';
import ReportsPage from '../components/ReportsPage';
import HistoryPage from '../components/HistoryPage';
import SettingsPage from '../components/SettingsPage';
import {
  agentSteps,
  initialFormState,
  businessModelOptions,
  customerTypeOptions,
  revenueOptions,
  tagOptions,
  challengeOptions,
  goalOptions,
} from '../constants/auditOptions';

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
      setPipelineStatus('queued');
      setActiveAgentIndex(-1);
      setFailedAgentIndex(-1);
      setMessage(`Audit queued with job id ${data.job_id}`);
      setFormData(initialFormState);
      setCurrentStep(1);
      setStepErrors({});
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

  const completedReports = history.filter((job) => formatStatus(job.status) === 'completed' && job.report_available);
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

  if (view === 'reports') {
    return (
      <ReportsPage
        completedReports={completedReports}
        handleDownload={handleDownload}
        downloadingJobId={downloadingJobId}
        getBusinessLabel={getBusinessLabel}
      />
    );
  }

  if (view === 'history') {
    return (
      <HistoryPage
        history={history}
        handleDownload={handleDownload}
        downloadingJobId={downloadingJobId}
        getBusinessLabel={getBusinessLabel}
        formatStatus={formatStatus}
      />
    );
  }

  if (view === 'settings') {
    return <SettingsPage apiBaseUrl={apiBaseUrl} token={token} />;
  }

  return (
    <OverviewPage
      apiBaseUrl={apiBaseUrl}
      token={token}
      formData={formData}
      setFormData={setFormData}
      currentStep={currentStep}
      setCurrentStep={setCurrentStep}
      stepErrors={stepErrors}
      setStepErrors={setStepErrors}
      loading={loading}
      error={error}
      setError={setError}
      message={message}
      activeJobId={activeJobId}
      pipelineStatus={pipelineStatus}
      activeAgentIndex={activeAgentIndex}
      failedAgentIndex={failedAgentIndex}
      handleSubmit={handleSubmit}
      handleNext={handleNext}
      handleBack={handleBack}
      updateField={updateField}
      toggleTagSelection={toggleTagSelection}
      agentSteps={agentSteps}
      businessModelOptions={businessModelOptions}
      customerTypeOptions={customerTypeOptions}
      revenueOptions={revenueOptions}
      tagOptions={tagOptions}
      challengeOptions={challengeOptions}
      goalOptions={goalOptions}
    />
  );
}

export default DashboardPage;
