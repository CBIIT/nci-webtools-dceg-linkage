"use client";

function parseVersion(versionString: string | undefined): string {
  if (!versionString) return "dev";
  
  // Match version pattern like X.Y.Z where X, Y, Z are numbers
  const versionMatch = versionString.match(/(\d+\.\d+\.\d+)/);
  
  return versionMatch ? versionMatch[1] : "dev";
}

export default function Footer() {
  return (
    <>
     <footer id="footer" className="flex-grow-0">
      <div className="bg-primary text-light py-4">
        <div className="container">
          <div className="mb-4">
            <a target="_blank" href="https://www.cancer.gov/" className="text-light h4 mb-1">
              Division of Cancer Epidemiology and Genetics
            </a>
            
            <div className="h6">at the National Cancer Institute</div>
          </div>
          <div className="row">
            <div className="col-lg-4 mb-4">
              <div className="h5 mb-1 font-weight-light">CONTACT INFORMATION</div>
              <ul className="list-unstyled mb-0">
                <li>
                   <a className=" text-light" target="_top" href="mailto:NCILDlinkWebAdmin@mail.nih.gov?subject=LDlink">
                    Contact Us
                  </a>
                </li>
                 
              </ul>
              <ul className="list-unstyled mb-0 mt-3">
                  <li>Version 6.0.0</li>
              </ul>
            </div>
            <div className="col-lg-4 mb-4">
              <div>
                <a className=" h5 mb-1 font-weight-light" target="_blank" href="https://www.cancer.gov/global/web/policies">
                    POLICIES
                  </a>
              </div>
              <ul className="list-unstyled mb-0">
                <li>
                  <a className="text-light" target="_blank" href="https://www.cancer.gov/policies/accessibility">
                    Accessibility
                  </a>
                </li>
                <li>
                  <a className="text-light" target="_blank" href="https://www.cancer.gov/policies/disclaimer">
                    Disclaimer
                  </a>
                </li>
                <li>
                  <a className="text-light" target="_blank" href="https://www.cancer.gov/policies/foia">
                    FOIA
                  </a>
                </li>
                <li>
                  <a
                    className="text-light"
                    target="_blank"
                    href="https://www.hhs.gov/vulnerability-disclosure-policy/index.html">
                    HHS Vulnerability Disclosure
                  </a>
                </li>
              </ul>
            </div>
            <div className="col-lg-4 mb-4">
              <div className="h5 mb-1 font-weight-light">MORE INFORMATION</div>
              <ul className="list-unstyled mb-0">
                <li>
                  <a className="text-light" target="_blank" href="http://www.hhs.gov/">
                    U.S. Department of Health and Human Services
                  </a>
                </li>
                <li>
                  <a className="text-light" target="_blank" href="http://www.nih.gov/">
                    National Institutes of Health
                  </a>
                </li>
                <li>
                  <a className="text-light" target="_blank" href="https://www.cancer.gov/">
                    National Cancer Institute
                  </a>
                </li>
                <li>
                  <a className="text-light" target="_blank" href="http://usa.gov/">
                    USA.gov
                  </a>
                </li>
             
              </ul>
            </div>
          </div>
        </div>
        <div className="text-center">NIH ... Turning Discovery Into Health ®</div>
      </div>
    </footer>
    </>
  );
}
