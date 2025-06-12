// components/Header.tsx
export default function Header() {
  return (
    <div className="header" style={{ backgroundColor: '#F8F9FA' }}>
      <div className="container">
        <header className="usa-banner__header">
          <div className="usa-banner__inner">
            <div className="container">
              <div className="usa-banner__header-text">
                An official website of the United States government
              </div>
            </div>
          </div>
        </header>
        <a href="https://dceg.cancer.gov/" target="_blank" rel="noopener noreferrer">
          <img
            className="mw-100"
            height="90"
            src="/images/NIH-LDlink-Logo.png"
            alt="NIH National Institutes of Health"
          />
          <span className="sr-only">NIH National Institutes of Health</span>
        </a>
      </div>
    </div>
  );
}
