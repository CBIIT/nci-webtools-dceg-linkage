// components/Navbar.tsx
export default function Navbar() {
  return (
    <nav className="navbar navbar-static-top">
      <div className="container">
        <ul id="ldlink-tabs" className="nav navbar-nav">
          <li className="nav nav-item mr-4">
            <a id="home-tab-anchor" href="#home-tab" data-toggle="tab">
              Home
            </a>
          </li>
          <li id="dropdown-tools" className="dropdown-nav">
            <div className="nav-div dropdown-toggle" data-toggle="dropdown">
              LD Tools <span className="caret" />
            </div>
            <ul className="dropdown-menu" style={{ overflow: 'hidden', backgroundColor: 'white' }}>
              {[
                'LDassoc',
                'LDexpress',
                'LDhap',
                'LDmatrix',
                'LDpair',
                'LDpop',
                'LDproxy',
                'LDtrait',
                'LDscore',
                'SNPchip',
                'SNPclip',
              ].map((tool) => (
                <li key={tool}>
                  <a
                    className="dropdown-text"
                    href={`#${tool.toLowerCase()}-tab`}
                    data-toggle="tab"
                    title={`Go to ${tool}`}
                    style={{ color: 'black' }}
                  >
                    {tool}
                  </a>
                </li>
              ))}
            </ul>
          </li>
          <li>
            <a id="apiaccess-tab-anchor" href="#apiaccess-tab" data-toggle="tab">
              API Access
            </a>
          </li>
          <li>
            <a id="citations-tab-anchor" href="#citations-tab" data-toggle="tab">
              Citations
            </a>
          </li>
          <li>
            <a id="version-tab-anchor" href="#version-tab" data-toggle="tab">
              Version History
            </a>
          </li>
          <li>
            <a id="help-tab-anchor" href="#help-tab" data-toggle="tab">
              Documentation
            </a>
          </li>
        </ul>
      </div>
    </nav>
  );
}
