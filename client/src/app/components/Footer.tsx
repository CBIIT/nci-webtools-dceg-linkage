// components/Footer.tsx
export default function Footer() {
  return (
    <div className="footer text-left text-md-center pt-4 pb-4 text-light flex-none">
      <div className="container">
        <ul className="list-inline text-light">
          {[
            { href: "https://www.cancer.gov/", label: "Home" },
            { href: "mailto:NCILDlinkWebAdmin@mail.nih.gov?subject=LDlink", label: "Support" },
            { href: "https://www.cancer.gov/global/web/policies", label: "Policies" },
            { href: "https://www.cancer.gov/global/web/policies/accessibility", label: "Accessibility" },
            { href: "https://cancer.gov/global/viewing-files", label: "Viewing Files" },
            { href: "https://www.cancer.gov/global/web/policies/foia", label: "FOIA" },
          ].map((item, idx, arr) => (
            <li key={item.label} className="pb-1 d-block d-md-inline">
              <a className="text-light m-1" href={item.href} target="_blank" rel="noopener noreferrer">
                {item.label}
              </a>
              {idx < arr.length - 1 && <span className="d-none d-md-inline">|</span>}
            </li>
          ))}
        </ul>

        <ul className="list-inline text-light">
          {[
            { href: "https://www.hhs.gov/", label: "U.S. Department of Health and Human Services" },
            { href: "https://www.nih.gov", label: "National Institutes of Health" },
            { href: "https://www.cancer.gov/", label: "National Cancer Institute" },
            { href: "https://www.hhs.gov/vulnerability-disclosure-policy/", label: "HHS Vulnerability Disclosure" },
            { href: "https://usa.gov", label: "USA.gov" },
          ].map((item, idx, arr) => (
            <li key={item.label} className="pb-1 d-block d-md-inline">
              <a className="text-light m-1" href={item.href} target="_blank" rel="noopener noreferrer">
                {item.label}
              </a>
              {idx < arr.length - 1 && <span className="d-none d-md-inline">|</span>}
            </li>
          ))}
        </ul>

        <ul className="list-inline text-light">
          <li>NIH ... Turning Discovery Into Health<sup>&reg;</sup></li>
        </ul>
      </div>
    </div>
  );
}
