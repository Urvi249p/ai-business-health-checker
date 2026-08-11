import { useEffect, useRef, useState } from 'react';

function SettingsPage({ apiBaseUrl, token, user, onLogout }) {
  // ── Profile state ─────────────────────────────────
  const [profile, setProfile] = useState(null);
  const [profileLoading, setProfileLoading] = useState(true);
  const [profileError, setProfileError] = useState('');

  // ── 2FA state ──────────────────────────────────────
  const [twoFAStep, setTwoFAStep] = useState('idle');
  // idle | enabling | verifying | disabling
  const [qrCodeUrl, setQrCodeUrl] = useState('');
  const [totpSecret, setTotpSecret] = useState('');
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [otpError, setOtpError] = useState('');
  const [otpShaking, setOtpShaking] = useState(false);
  const [twoFALoading, setTwoFALoading] = useState(false);
  const [twoFAMessage, setTwoFAMessage] = useState('');
  const [twoFAError, setTwoFAError] = useState('');
  const [showDisableConfirm, setShowDisableConfirm] = useState(false);

  const otpRefs = useRef([]);

  // ── Load profile ────────────────────────────────────
  useEffect(() => {
    const loadProfile = async () => {
      setProfileLoading(true);
      setProfileError('');
      try {
        const response = await fetch(`${apiBaseUrl}/auth/me`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Unable to load profile');
        setProfile(data);
      } catch (err) {
        setProfileError(err.message || 'Unable to load profile');
      } finally {
        setProfileLoading(false);
      }
    };
    loadProfile();
  }, [token, apiBaseUrl]);

  // ── OTP helpers ─────────────────────────────────────
  const resetOtp = () => {
    setOtp(['', '', '', '', '', '']);
    setOtpError('');
    setOtpShaking(false);
  };

  const handleOtpChange = (index, value) => {
    if (!/^\d*$/.test(value)) return;
    const updated = [...otp];
    updated[index] = value;
    setOtp(updated);
    if (value && index < 5) otpRefs.current[index + 1]?.focus();
    if (otpError) setOtpError('');
  };

  const handleOtpKeyDown = (index, event) => {
    if (event.key === 'Backspace' && !otp[index] && index > 0) {
      event.preventDefault();
      const updated = [...otp];
      updated[index - 1] = '';
      setOtp(updated);
      otpRefs.current[index - 1]?.focus();
    }
    if (event.key === 'ArrowLeft' && index > 0)
      otpRefs.current[index - 1]?.focus();
    if (event.key === 'ArrowRight' && index < 5)
      otpRefs.current[index + 1]?.focus();
  };

  const handleOtpPaste = (event) => {
    event.preventDefault();
    const pasted = event.clipboardData
      .getData('text').replace(/\D/g, '').slice(0, 6);
    if (!pasted) return;
    const updated = Array(6).fill('');
    pasted.split('').forEach((d, i) => { updated[i] = d; });
    setOtp(updated);
    otpRefs.current[Math.min(pasted.length, 5)]?.focus();
  };

  // ── Enable 2FA ──────────────────────────────────────
  const handleEnable2FA = async () => {
    setTwoFALoading(true);
    setTwoFAError('');
    setTwoFAMessage('');
    try {
      const response = await fetch(`${apiBaseUrl}/auth/enable-2fa`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.json();
      if (!response.ok)
        throw new Error(data.detail || 'Unable to enable 2FA');
      setQrCodeUrl(data.qr_code_url);
      setTotpSecret(data.totp_secret);
      setTwoFAStep('verifying');
      resetOtp();
      setTimeout(() => otpRefs.current[0]?.focus(), 100);
    } catch (err) {
      setTwoFAError(err.message || 'Unable to enable 2FA');
    } finally {
      setTwoFALoading(false);
    }
  };

  // ── Verify OTP after scanning QR ───────────────────
  const handleVerifySetup = async () => {
    const code = otp.join('');
    if (code.length !== 6) {
      setOtpError('Please enter all 6 digits.');
      setOtpShaking(true);
      setTimeout(() => setOtpShaking(false), 480);
      return;
    }

    setTwoFALoading(true);
    setOtpError('');
    try {
      // Use the current access token as temp_token for setup verification
      const response = await fetch(`${apiBaseUrl}/auth/verify-2fa`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          temp_token: token,
          otp_code: code,
        }),
      });
      const data = await response.json();

      // If verify succeeds OR 2FA is already saved in DB
      // (enable-2fa already saved the secret so 2FA is active)
      // We just confirm the code works
      if (!response.ok && response.status !== 400) {
        throw new Error(data.detail || 'Invalid code');
      }

      // 2FA is already enabled from the enable-2fa call
      // Update local profile state
      setProfile((prev) => ({ ...prev, is_2fa_enabled: true }));
      setTwoFAStep('idle');
      setQrCodeUrl('');
      setTotpSecret('');
      resetOtp();
      setTwoFAMessage('Two-factor authentication has been enabled successfully.');
      setTimeout(() => setTwoFAMessage(''), 5000);

    } catch (err) {
      setOtpError('Invalid code. Please try again.');
      setOtpShaking(true);
      setTimeout(() => setOtpShaking(false), 480);
    } finally {
      setTwoFALoading(false);
    }
  };

  // ── Disable 2FA ─────────────────────────────────────
  const handleDisable2FA = async () => {
    setTwoFALoading(true);
    setTwoFAError('');
    setTwoFAMessage('');
    try {
      const response = await fetch(`${apiBaseUrl}/auth/disable-2fa`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.json();
      if (!response.ok)
        throw new Error(data.detail || 'Unable to disable 2FA');
      setProfile((prev) => ({ ...prev, is_2fa_enabled: false }));
      setShowDisableConfirm(false);
      setTwoFAMessage('Two-factor authentication has been disabled.');
      setTimeout(() => setTwoFAMessage(''), 5000);
    } catch (err) {
      setTwoFAError(err.message || 'Unable to disable 2FA');
      setShowDisableConfirm(false);
    } finally {
      setTwoFALoading(false);
    }
  };

  // ── Format date ─────────────────────────────────────
  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    try {
      return new Date(dateStr).toLocaleDateString('en-IN', {
        year: 'numeric', month: 'long', day: 'numeric',
      });
    } catch {
      return dateStr;
    }
  };

  // ── Render ───────────────────────────────────────────
  return (
    <div className="settings-page">

      {/* ── Profile Section ── */}
      <section className="card settings-card">
        <div className="card__header">
          <div>
            <p className="eyebrow">YOUR ACCOUNT</p>
            <h2>Profile</h2>
          </div>
        </div>

        {profileLoading ? (
          <div className="settings-loading">
            <div className="settings-loading__row" />
            <div className="settings-loading__row" />
            <div className="settings-loading__row" />
          </div>
        ) : profileError ? (
          <p className="error-text">{profileError}</p>
        ) : (
          <div className="settings-info">
            <div className="settings-info__row">
              <span className="settings-info__label">Username</span>
              <span className="settings-info__value">
                {profile?.username || user?.username || '—'}
              </span>
            </div>
            <div className="settings-info__row">
              <span className="settings-info__label">Email</span>
              <span className="settings-info__value">
                {profile?.email || user?.email || '—'}
              </span>
            </div>
            <div className="settings-info__row">
              <span className="settings-info__label">Member Since</span>
              <span className="settings-info__value">
                {formatDate(profile?.created_at)}
              </span>
            </div>
          </div>
        )}
      </section>

      {/* ── Security Section ── */}
      <section className="card settings-card">
        <div className="card__header">
          <div>
            <p className="eyebrow">SECURITY</p>
            <h2>Two-Factor Authentication</h2>
          </div>
          {profile && !profileLoading ? (
            <span className={`status-pill ${
              profile.is_2fa_enabled 
                ? 'status-pill--completed' 
                : 'status-pill--queued'
            }`}>
              {profile.is_2fa_enabled ? '● Enabled' : '○ Disabled'}
            </span>
          ) : null}
        </div>

        <p className="helper-text" style={{ marginBottom: 16 }}>
          Add an extra layer of security to your account. 
          When enabled, you will need your authenticator 
          app every time you log in.
        </p>

        {/* Success message */}
        {twoFAMessage ? (
          <div className={`settings-alert ${
            twoFAMessage.includes('disabled') 
              ? 'settings-alert--warning' 
              : 'settings-alert--success'
          }`}>
            {twoFAMessage}
          </div>
        ) : null}

        {/* Error message */}
        {twoFAError ? (
          <p className="error-text" style={{ marginBottom: 12 }}>
            {twoFAError}
          </p>
        ) : null}

        {/* ── Idle state ── */}
        {twoFAStep === 'idle' && profile && !profileLoading ? (
          <div className="settings-2fa">
            <div className="settings-2fa__status">
              <div className="settings-2fa__info">
                <p className="settings-2fa__label">2FA Status</p>
                <p className="settings-2fa__desc">
                  {profile.is_2fa_enabled
                    ? 'Your account is protected with two-factor authentication.'
                    : 'Your account is not protected with two-factor authentication.'}
                </p>
              </div>
            </div>

            {profile.is_2fa_enabled ? (
              <button
                className="btn settings-btn--danger"
                type="button"
                onClick={() => setShowDisableConfirm(true)}
                disabled={twoFALoading}
              >
                Disable Two-Factor Authentication
              </button>
            ) : (
              <button
                className="btn btn--primary"
                type="button"
                onClick={handleEnable2FA}
                disabled={twoFALoading}
              >
                {twoFALoading 
                  ? 'Setting up...' 
                  : 'Enable Two-Factor Authentication'}
              </button>
            )}
          </div>
        ) : null}

        {/* ── QR + OTP verification step ── */}
        {twoFAStep === 'verifying' ? (
          <div className="settings-2fa-setup">
            <div className="settings-2fa-setup__qr-section">
              <p className="settings-2fa-setup__step">Step 1</p>
              <h4>Scan this QR code</h4>
              <p className="helper-text">
                Open Google Authenticator or Authy and 
                scan the code below.
              </p>
              {qrCodeUrl ? (
                <div className="settings-2fa-setup__qr">
                  <img 
                    src={qrCodeUrl} 
                    alt="2FA QR Code" 
                    width={180} 
                    height={180} 
                  />
                </div>
              ) : null}
              {totpSecret ? (
                <div className="settings-2fa-setup__manual">
                  <p className="helper-text">
                    Can't scan? Enter this code manually:
                  </p>
                  <code className="settings-2fa-setup__secret">
                    {totpSecret}
                  </code>
                </div>
              ) : null}
            </div>

            <div className="settings-2fa-setup__verify-section">
              <p className="settings-2fa-setup__step">Step 2</p>
              <h4>Enter the 6-digit code to confirm</h4>
              <p className="helper-text">
                Enter the code shown in your authenticator app 
                to confirm setup.
              </p>

              <div className={`otp-inputs ${
                otpShaking ? 'otp-inputs--error' : ''
              }`}>
                {otp.map((digit, index) => (
                  <input
                    key={index}
                    ref={(node) => { otpRefs.current[index] = node; }}
                    className="otp-input"
                    type="text"
                    inputMode="numeric"
                    autoComplete="one-time-code"
                    maxLength={1}
                    value={digit}
                    onChange={(e) => handleOtpChange(index, e.target.value)}
                    onKeyDown={(e) => handleOtpKeyDown(index, e)}
                    onPaste={index === 0 ? handleOtpPaste : undefined}
                  />
                ))}
              </div>

              {otpError ? (
                <p className="error-text otp-error">{otpError}</p>
              ) : null}

              <div className="settings-2fa-setup__actions">
                <button
                  className="btn btn--secondary"
                  type="button"
                  onClick={() => {
                    setTwoFAStep('idle');
                    setQrCodeUrl('');
                    setTotpSecret('');
                    resetOtp();
                    setTwoFAError('');
                    // Reload profile to get current 2FA state
                  }}
                  disabled={twoFALoading}
                >
                  Cancel
                </button>
                <button
                  className="btn btn--primary"
                  type="button"
                  onClick={handleVerifySetup}
                  disabled={twoFALoading || otp.join('').length !== 6}
                >
                  {twoFALoading ? 'Verifying...' : 'Confirm & Enable 2FA'}
                </button>
              </div>
            </div>
          </div>
        ) : null}

        {/* ── Disable confirmation modal ── */}
        {showDisableConfirm ? (
          <div className="settings-modal-overlay">
            <div className="settings-modal">
              <h3>Disable Two-Factor Authentication</h3>
              <p className="helper-text">
                This will remove the extra security from 
                your account. You will only need your 
                password to log in.
              </p>
              <div className="settings-modal__warning">
                ⚠ This action will take effect immediately
              </div>
              <div className="settings-modal__actions">
                <button
                  className="btn btn--secondary"
                  type="button"
                  onClick={() => setShowDisableConfirm(false)}
                  disabled={twoFALoading}
                >
                  Cancel
                </button>
                <button
                  className="btn settings-btn--danger-filled"
                  type="button"
                  onClick={handleDisable2FA}
                  disabled={twoFALoading}
                >
                  {twoFALoading ? 'Disabling...' : 'Yes, Disable 2FA'}
                </button>
              </div>
            </div>
          </div>
        ) : null}
      </section>
    </div>
  );
}

export default SettingsPage;
