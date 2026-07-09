import { useEffect, useState } from 'react';

function SettingsPage({ apiBaseUrl, token }) {
  const [profile, setProfile] = useState(null);
  const [settingsLoading, setSettingsLoading] = useState(false);
  const [settingsError, setSettingsError] = useState('');
  const [settingsMessage, setSettingsMessage] = useState('');
  const [settingsActionLoading, setSettingsActionLoading] = useState(false);
  const [qrModalOpen, setQrModalOpen] = useState(false);
  const [qrData, setQrData] = useState({ qr_code_url: '', totp_secret: '' });
  const [confirmDisableOpen, setConfirmDisableOpen] = useState(false);
  const [disableError, setDisableError] = useState('');

  const loadProfile = async () => {
    setSettingsError('');
    setSettingsLoading(true);
    try {
      const response = await fetch(`${apiBaseUrl}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Unable to load profile');
      setProfile(data);
    } catch (err) {
      setSettingsError(err.message || 'Unable to load profile. Please try again.');
      setProfile(null);
    } finally {
      setSettingsLoading(false);
    }
  };

  useEffect(() => {
    loadProfile();
  }, [apiBaseUrl, token]);

  const formatMemberSince = (createdAt) => {
    if (!createdAt) return '';
    try {
      return new Date(createdAt).toLocaleString('en-US', {
        month: 'long',
        year: 'numeric',
      });
    } catch {
      return '';
    }
  };

  const handleCloseQrModal = async () => {
    setQrModalOpen(false);
    await loadProfile();
    setSettingsMessage('Two-factor authentication is now enabled on your account.');
  };

  const handleEnable2FA = async () => {
    setSettingsError('');
    setSettingsActionLoading(true);
    try {
      const response = await fetch(`${apiBaseUrl}/auth/enable-2fa`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({}),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Unable to enable two-factor authentication');
      setQrData({ qr_code_url: data.qr_code_url || '', totp_secret: data.totp_secret || '' });
      setQrModalOpen(true);
    } catch (err) {
      setSettingsError(err.message || 'Unable to enable two-factor authentication');
    } finally {
      setSettingsActionLoading(false);
    }
  };

  const handleDisable2FA = async () => {
    setDisableError('');
    setSettingsActionLoading(true);
    try {
      const response = await fetch(`${apiBaseUrl}/auth/disable-2fa`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({}),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Unable to disable two-factor authentication');
      setConfirmDisableOpen(false);
      await loadProfile();
      setSettingsMessage('Two-factor authentication has been disabled.');
    } catch (err) {
      setDisableError(err.message || 'Unable to disable two-factor authentication');
    } finally {
      setSettingsActionLoading(false);
    }
  };

  useEffect(() => {
    if (!settingsMessage) return;
    const timeout = window.setTimeout(() => setSettingsMessage(''), 4000);
    return () => window.clearTimeout(timeout);
  }, [settingsMessage]);

  const isEnabled = profile?.is_2fa_enabled;

  return (
    <div className="dashboard-grid">
      <section className="card settings-card">
        <div className="card__header">
          <div>
            <p className="eyebrow">YOUR ACCOUNT</p>
            <h2>Profile</h2>
          </div>
        </div>

        {settingsMessage ? <p className="success-text">{settingsMessage}</p> : null}
        {settingsError ? <p className="error-text">{settingsError}</p> : null}

        {settingsLoading ? (
          <div className="settings-placeholder">
            <div className="settings-placeholder-row" />
            <div className="settings-placeholder-row" />
            <div className="settings-placeholder-row" />
          </div>
        ) : (
          <div>
            <div className="settings-info-row">
              <span className="settings-info-label">Username</span>
              <span className="settings-info-value">{profile?.username || '—'}</span>
            </div>
            <div className="settings-info-row">
              <span className="settings-info-label">Email</span>
              <span className="settings-info-value">{profile?.email || '—'}</span>
            </div>
            <div className="settings-info-row settings-info-row--last">
              <span className="settings-info-label">Member Since</span>
              <span className="settings-info-value">{formatMemberSince(profile?.created_at) || '—'}</span>
            </div>
          </div>
        )}
      </section>

      <section className="card settings-card">
        <div className="card__header">
          <div>
            <p className="eyebrow">SECURITY</p>
            <h2>Two-Factor Authentication</h2>
          </div>
        </div>

        <p className="helper-text">Add an extra layer of security to your account. Once enabled, you'll need your authenticator app every time you log in.</p>

        <div className="settings-info-row">
          <span className="settings-info-label">2FA Status</span>
          <span
            className={`status-pill ${isEnabled ? 'status-pill--enabled' : 'status-pill--disabled'}`}>
            {isEnabled ? '● Enabled' : '○ Disabled'}
          </span>
        </div>

        {disableError ? <p className="error-text">{disableError}</p> : null}

        {isEnabled ? (
          <button
            className="btn btn--danger-outline"
            type="button"
            onClick={() => setConfirmDisableOpen(true)}
            disabled={settingsActionLoading || settingsLoading}
          >
            Disable Two-Factor Authentication
          </button>
        ) : (
          <button
            className="btn btn--primary"
            type="button"
            onClick={handleEnable2FA}
            disabled={settingsActionLoading || settingsLoading}
          >
            Enable Two-Factor Authentication
          </button>
        )}

        {qrModalOpen ? (
          <div className="settings-modal-overlay">
            <div className="settings-modal">
              <div className="settings-modal__header">
                <h3>Scan QR Code</h3>
                <p className="helper-text">Open Google Authenticator or Authy and scan this code to set up two-factor authentication</p>
              </div>
              <div className="settings-modal__body">
                <img
                  src={qrData.qr_code_url}
                  width="200"
                  height="200"
                  alt="2FA QR code"
                  className="settings-modal__qr"
                />
                <p className="helper-text">Can't scan? Enter this code manually:</p>
                <div className="settings-secret">{qrData.totp_secret || '—'}</div>
                <div className="settings-modal-divider" />
                <p className="helper-text">2FA is now active — use this code to log in next time.</p>
              </div>
              <div className="settings-modal__footer">
                <button
                  className="btn btn--secondary"
                  type="button"
                  onClick={handleCloseQrModal}
                >
                  Close
                </button>
                <button
                  className="btn btn--primary"
                  type="button"
                  onClick={handleCloseQrModal}
                >
                  Got it
                </button>
              </div>
            </div>
          </div>
        ) : null}

        {confirmDisableOpen ? (
          <div className="settings-modal-overlay">
            <div className="settings-modal settings-modal--small">
              <div className="settings-modal__header">
                <h3>Disable Two-Factor Authentication</h3>
              </div>
              <div className="settings-modal__body">
                <p className="helper-text">This will remove the extra security from your account. You'll only need your password to log in.</p>
                <div className="settings-warning-strip">
                  <span>⚠ This action will take effect immediately</span>
                </div>
              </div>
              <div className="settings-modal__footer">
                <button
                  className="btn btn--secondary"
                  type="button"
                  onClick={() => setConfirmDisableOpen(false)}
                >
                  Cancel
                </button>
                <button
                  className="btn btn--danger"
                  type="button"
                  onClick={handleDisable2FA}
                  disabled={settingsActionLoading}
                >
                  Yes, Disable 2FA
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
