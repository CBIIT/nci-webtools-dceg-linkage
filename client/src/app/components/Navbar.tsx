"use client";
import Link from "next/link";

export default function Navbar() {
  const tools = [
    { id: "ldassoc", title: "LDassoc", description: "Calculate LDassoc" },
    { id: "ldexpress", title: "LDexpress" },
    { id: "ldhap", title: "LDhap" },
    { id: "ldmatrix", title: "LDmatrix" },
    { id: "ldpair", title: "LDpair" },
    { id: "ldpop", title: "LDpop" },
    { id: "ldproxy", title: "LDproxy" },
    { id: "ldtrait", title: "LDtrait" },
    { id: "ldscore", title: "LDscore" },
    { id: "snpchip", title: "SNPchip" },
    { id: "snpclip", title: "SNPclip" },
  ];

  return (
    <nav className="navbar navbar-expand-lg navbar-light border-bottom">
      <div className="container">
        

        <button
          className="navbar-toggler"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#ldlinkNavbar"
          aria-controls="ldlinkNavbar"
          aria-expanded="false"
          aria-label="Toggle navigation"
        >
          <span className="navbar-toggler-icon" />
        </button>

        <div className="collapse navbar-collapse" id="ldlinkNavbar">
          <ul id="ldlink-tabs" className="navbar-nav me-auto mb-2 mb-lg-0">

            {/* Home */}
            <li className="nav-item mr-4">
              <Link id="home-tab-anchor" className="nav-link" href="/" >
                Home
              </Link>
            </li>

            {/* LD Tools Dropdown */}
            <li id="dropdown-tools" className="nav-item dropdown">
              <a
                className="nav-link dropdown-toggle"
                href="#"
                id="ldtoolsDropdown"
                role="button"
                data-bs-toggle="dropdown"
                aria-expanded="false"
              >
                LD Tools
              </a>
              <ul className="dropdown-menu" aria-labelledby="ldtoolsDropdown">
                {tools.map((tool) => (
                  <li key={tool.id}>
                    <a
                      id={`${tool.id}-tab-anchor`}
                      className="dropdown-item"
                      href={`#${tool.id}-tab`}
                      data-bs-toggle="tab"
                      title={tool.description || tool.title}
                      style={{ color: "black" }}
                    >
                      {tool.title}
                    </a>
                  </li>
                ))}
              </ul>
            </li>

            {/* Other Tabs */}
            <li className="nav-item">
              <a id="apiaccess-tab-anchor" className="nav-link" href="#apiaccess-tab" data-bs-toggle="tab">
                API Access
              </a>
            </li>
            <li className="nav-item">
              <Link id="citations-tab-anchor" className="nav-link" href="/citations">
                Citations
              </Link>
            </li>
            <li className="nav-item">
                <Link href="/version-history" className="nav-link">Version History</Link>

            </li>

            <li className="nav-item">
              <Link href="/documentation" className="nav-link">Documentation</Link>
            </li>
          </ul>
        </div>
      </div>
    </nav>
  );
}
