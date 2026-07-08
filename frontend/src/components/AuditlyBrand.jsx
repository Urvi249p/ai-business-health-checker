function AuditlyIcon({ size = 32, className = '' }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      className={className}
      aria-hidden="true"
    >
      <rect width="32" height="32" rx="8" fill="#2563EB" />
      <rect x="8" y="7" width="13" height="17" rx="2" fill="none" stroke="white" strokeWidth="1.5" />
      <line x1="11" y1="12" x2="18" y2="12" stroke="white" strokeWidth="1.2" strokeLinecap="round" opacity="0.8" />
      <line x1="11" y1="15" x2="18" y2="15" stroke="white" strokeWidth="1.2" strokeLinecap="round" opacity="0.8" />
      <line x1="11" y1="18" x2="15" y2="18" stroke="white" strokeWidth="1.2" strokeLinecap="round" opacity="0.8" />
      <circle cx="22" cy="22" r="6" fill="#2563EB" />
      <circle cx="22" cy="22" r="5.5" fill="none" stroke="white" strokeWidth="1.5" />
      <polyline points="19,22 21.5,24.5 25.5,19.5" fill="none" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function AuditlyBrand({ size = 32, className = '', wordmarkClassName = '', wordmark = 'Auditly' }) {
  return (
    <div className={`auditly-brand ${className}`.trim()}>
      <AuditlyIcon size={size} />
      <span className={`auditly-brand__wordmark ${wordmarkClassName}`.trim()}>{wordmark}</span>
    </div>
  );
}

export default AuditlyBrand;
