import AuditlyBrand from './AuditlyBrand';

function Sidebar({ currentView, onNavigate, username, onLogout }) {
  const navItems = [
    { view: 'overview', icon: '⌂', label: 'Overview' },
    { view: 'reports', icon: '▣', label: 'Reports' },
    { view: 'history', icon: '◌', label: 'History' },
    { view: 'settings', icon: '⚙', label: 'Settings' },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar__brand">
        <AuditlyBrand size={32} className="sidebar__brand-logo" wordmarkClassName="sidebar__brand-wordmark" />
      </div>

      <nav className="sidebar__nav" aria-label="Primary navigation">
        {navItems.map((item) => (
          <button
            key={item.view}
            type="button"
            className={`sidebar__link ${currentView === item.view ? 'is-active' : ''}`}
            onClick={() => onNavigate(item.view)}
          >
            <span className="sidebar__icon">{item.icon}</span>
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="sidebar__footer">
        <div className="sidebar__profile">
          <div className="profile-avatar">
            {username?.slice(0, 1).toUpperCase() || 'U'}
          </div>
          <div>
            <p className="profile-name">{username || 'Signed in'}</p>
          </div>
        </div>
        <button className="sidebar__logout" onClick={onLogout}>Log out</button>
      </div>
    </aside>
  );
}

export default Sidebar;
