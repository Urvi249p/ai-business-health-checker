import { useEffect, useRef, useState } from 'react';

function AuthPage({ apiBaseUrl, onLogin }) {
  const [mode, setMode] = useState('login');
  const [authStep, setAuthStep] = useState('login');
  const [form, setForm] = useState({ username: '', email: '', password: '' });
  const [tempToken, setTempToken] = useState('');
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [error, setError] = useState('');
  const [otpError, setOtpError] = useState('');
  const [loading, setLoading] = useState(false);
  const [otpShaking, setOtpShaking] = useState(false);
  const otpInputRefs = useRef([]);

  useEffect(() => {
    if (authStep === 'otp') {
      otpInputRefs.current[0]?.focus();
    }
  }, [authStep]);

  const handleChange = (event) => {
    setForm((prev) => ({ ...prev, [event.target.name]: event.target.value }));
  };

  const resetOtpState = () => {
    setOtp(['', '', '', '', '', '']);
    setOtpError('');
    setOtpShaking(false);
    setTempToken('');
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setLoading(true);

    try {
      const endpoint = mode === 'login' ? '/auth/login' : '/auth/register';
      const body = mode === 'login'
        ? new URLSearchParams({ username: form.username, password: form.password })
        : JSON.stringify({ email: form.email, username: form.username, password: form.password });

      const response = await fetch(`${apiBaseUrl}${endpoint}`, {
        method: 'POST',
        headers: mode === 'login'
          ? { 'Content-Type': 'application/x-www-form-urlencoded' }
          : { 'Content-Type': 'application/json' },
        body,
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Authentication failed');

      const requiresTwoFactor = Boolean(data?.temp_token) && !data?.access_token
        || data?.['2fa_required'] === true
        || data?.requires_2fa === true;

      if (requiresTwoFactor) {
        resetOtpState();
        setTempToken(data.temp_token || '');
        setAuthStep('otp');
        return;
      }

      onLogin(data);
    } catch (err) {
      setError(err.message || 'Unable to complete authentication');
    } finally {
      setLoading(false);
    }
  };

  const handleOtpChange = (index, value) => {
    if (!/^\d*$/.test(value)) return;

    const updatedOtp = [...otp];
    updatedOtp[index] = value;
    setOtp(updatedOtp);

    if (value && index < 5) {
      otpInputRefs.current[index + 1]?.focus();
    }

    if (otpError) {
      setOtpError('');
    }
  };

  const handleOtpKeyDown = (index, event) => {
    if (event.key === 'Backspace' && !otp[index] && index > 0) {
      event.preventDefault();
      const updatedOtp = [...otp];
      updatedOtp[index - 1] = '';
      setOtp(updatedOtp);
      otpInputRefs.current[index - 1]?.focus();
    }

    if (event.key === 'ArrowLeft' && index > 0) {
      otpInputRefs.current[index - 1]?.focus();
    }

    if (event.key === 'ArrowRight' && index < 5) {
      otpInputRefs.current[index + 1]?.focus();
    }
  };

  const handleOtpPaste = (event) => {
    event.preventDefault();
    const pastedValue = event.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    if (!pastedValue) return;

    const updatedOtp = Array(6).fill('');
    pastedValue.split('').forEach((digit, index) => {
      updatedOtp[index] = digit;
    });

    setOtp(updatedOtp);
    const focusIndex = Math.min(pastedValue.length, 5);
    otpInputRefs.current[focusIndex]?.focus();
  };

  const handleOtpSubmit = async (event) => {
    event.preventDefault();
    setOtpError('');
    setLoading(true);

    const code = otp.join('');
    if (code.length !== 6) {
      setOtpError('Please enter the 6-digit code.');
      setOtpShaking(true);
      window.setTimeout(() => setOtpShaking(false), 480);
      setLoading(false);
      return;
    }

    try {
      const endpoints = ['/auth/verify-2fa', '/auth/verify_2fa'];
      let verifyData = null;
      let verifyResponse = null;

      for (const endpoint of endpoints) {
        verifyResponse = await fetch(`${apiBaseUrl}${endpoint}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ otp: code, otp_code: code, temp_token: tempToken }),
        });

        verifyData = await verifyResponse.json();
        if (verifyResponse.ok) {
          onLogin(verifyData);
          return;
        }

        if (verifyResponse.status !== 404) {
          break;
        }
      }

      throw new Error(verifyData?.detail || 'Invalid code');
    } catch (err) {
      setOtpError('Invalid code. Please try again.');
      setOtpShaking(true);
      window.setTimeout(() => setOtpShaking(false), 480);
    } finally {
      setLoading(false);
    }
  };

  const renderLoginView = () => (
    <div className="auth-card__transition">
      <div className="auth-card__header">
        <p className="eyebrow">Trusted audit workspace</p>
        <h2>{mode === 'login' ? 'Welcome back' : 'Create your account'}</h2>
        <p className="helper-text">Securely submit your business details and track every audit stage from one calm workspace.</p>
      </div>

      <div className="toggle-group" role="tablist" aria-label="Authentication mode">
        <button className={`toggle-chip ${mode === 'login' ? 'is-active' : ''}`} type="button" onClick={() => setMode('login')}>Login</button>
        <button className={`toggle-chip ${mode === 'register' ? 'is-active' : ''}`} type="button" onClick={() => setMode('register')}>Register</button>
      </div>

      {error ? <p className="error-text">{error}</p> : null}

      <form onSubmit={handleSubmit}>
        <label>
          Username
          <input name="username" value={form.username} onChange={handleChange} required />
        </label>

        {mode === 'register' ? (
          <label>
            Email
            <input name="email" type="email" value={form.email} onChange={handleChange} required />
          </label>
        ) : null}

        <label>
          Password
          <input name="password" type="password" value={form.password} onChange={handleChange} required minLength={8} />
        </label>

        <button className="btn btn--primary" disabled={loading}>
          {loading ? 'Working...' : mode === 'login' ? 'Login' : 'Register'}
        </button>
      </form>
    </div>
  );

  const renderOtpView = () => (
    <div className="auth-card__transition">
      <button className="auth-card__back" type="button" onClick={() => {
        resetOtpState();
        setAuthStep('login');
        setError('');
      }}>
        ←
      </button>

      <div className="auth-card__header auth-card__header--compact">
        <p className="eyebrow">TWO-FACTOR AUTHENTICATION</p>
        <h2>Enter verification code</h2>
        <p className="helper-text">Open your authenticator app and enter the 6-digit code.</p>
      </div>

      <form onSubmit={handleOtpSubmit}>
        <div className={`otp-inputs ${otpShaking ? 'otp-inputs--error' : ''}`}>
          {otp.map((digit, index) => (
            <input
              key={index}
              ref={(node) => {
                otpInputRefs.current[index] = node;
              }}
              className="otp-input"
              type="text"
              inputMode="numeric"
              autoComplete="one-time-code"
              maxLength={1}
              value={digit}
              onChange={(event) => handleOtpChange(index, event.target.value)}
              onKeyDown={(event) => handleOtpKeyDown(index, event)}
              onPaste={index === 0 ? handleOtpPaste : undefined}
            />
          ))}
        </div>

        {otpError ? <p className="error-text otp-error">{otpError}</p> : null}

        <button className="btn btn--primary" disabled={loading}>
          {loading ? 'Verifying...' : 'Verify Code'}
        </button>

        <p className="otp-hint">Didn't receive a code? Make sure your authenticator app is synced.</p>
      </form>
    </div>
  );

  return <div className="auth-card">{authStep === 'otp' ? renderOtpView() : renderLoginView()}</div>;
}

export default AuthPage;
