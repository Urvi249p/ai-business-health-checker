function HomePage() {
  return (
    <div className="home-page">
      <section className="home-hero">
        <div className="home-hero__content">
          <p className="eyebrow">AI-POWERED BUSINESS INTELLIGENCE</p>
          <h2 className="home-hero__title">
            Get a professional business audit in minutes
          </h2>
          <p className="home-hero__subtitle">
            Auditly uses a team of 5 specialized AI agents to analyze 
            your business, identify opportunities, and deliver a complete 
            strategy report — covering SWOT analysis, pricing strategy, 
            and a 90-day growth plan.
          </p>
          <button
            className="btn btn--primary btn--large"
            type="button"
            onClick={() => window.location.assign('/audit')}
          >
            Start My Audit →
          </button>
          <p className="home-hero__note">
            Takes 3–5 minutes · Free to use · PDF report included
          </p>
        </div>
      </section>

      <section className="home-why">
        <div className="home-why__grid">
          <div className="home-why__item">
            <div className="home-why__icon">🎯</div>
            <h4>Personalized to your business</h4>
            <p>Every report is tailored to your specific industry, 
            team size, revenue, and goals — not a generic template.</p>
          </div>
          <div className="home-why__item">
            <div className="home-why__icon">⚡</div>
            <h4>5 AI agents working together</h4>
            <p>A Business Analyst, SWOT Analyst, Pricing Consultant, 
            Growth Strategist, and Report Writer collaborate on your audit.</p>
          </div>
          <div className="home-why__item">
            <div className="home-why__icon">📄</div>
            <h4>Professional PDF report</h4>
            <p>Receive a formatted, consultant-quality report ready to 
            share with your team, partners, or investors.</p>
          </div>
          <div className="home-why__item">
            <div className="home-why__icon">🔒</div>
            <h4>Private and secure</h4>
            <p>Your business data is only used to generate your report 
            and is never shared or stored beyond your session.</p>
          </div>
        </div>
      </section>

      <section className="home-expect card card--wide">
        <div className="card__header">
          <div>
            <p className="eyebrow">WHAT TO EXPECT</p>
            <h3>What your audit covers</h3>
          </div>
        </div>
        <p className="home-expect__subtitle">
          Our AI analyses your business across 4 dimensions and 
          delivers a professional PDF report.
        </p>
        <div className="expectation-list">
          <div className="expectation-item">
            <div className="expectation-item__icon">◻</div>
            <div className="expectation-item__content">
              <h4>SWOT Analysis</h4>
              <p>Strengths, weaknesses, opportunities and threats 
              specific to your business — grounded in facts, 
              not generic templates.</p>
            </div>
          </div>
          <div className="expectation-item">
            <div className="expectation-item__icon">🏷</div>
            <div className="expectation-item__content">
              <h4>Pricing Strategy</h4>
              <p>The optimal pricing model and specific price points 
              for your market, customer type, and goals.</p>
            </div>
          </div>
          <div className="expectation-item">
            <div className="expectation-item__icon">↗</div>
            <div className="expectation-item__content">
              <h4>90-Day Growth Plan</h4>
              <p>A phase-by-phase action plan with clear owners, 
              success metrics and expected outcomes for each phase.</p>
            </div>
          </div>
          <div className="expectation-item">
            <div className="expectation-item__icon">📄</div>
            <div className="expectation-item__content">
              <h4>PDF Report</h4>
              <p>A professionally formatted report ready to present 
              to partners, investors or your team.</p>
            </div>
          </div>
        </div>
        <div className="expectation-strip">
          <span className="expectation-strip__item">
            ⏱ Estimated time: 3–5 minutes
          </span>
          <span className="expectation-strip__item">
            ⚠ Report auto-deleted after 30 minutes — download promptly
          </span>
        </div>
        <div className="home-expect__cta">
          <button
            className="btn btn--primary"
            type="button"
            onClick={() => window.location.assign('/audit')}
          >
            Start My Audit →
          </button>
        </div>
      </section>
    </div>
  );
}

export default HomePage;
