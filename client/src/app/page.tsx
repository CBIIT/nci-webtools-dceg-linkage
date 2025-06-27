import Link from "next/link";
import { Container, Row, Col } from "react-bootstrap";
import Image from "next/image";
import LdToolCard from "@/components/cards/ldtool-card";
import WhatsNew from "@/components/sections/whatsnew";
import LdToolSection from "@/components/sections/ldToolCards";

export default function Home() {
 

  return (
    <>
      <div className="flex-grow-1">
        <div>
          <Row className="mt-3">
            <div className="text-center">
              <h2>
                Welcome to{" "}
                <Image
                  src="/images/LDlink_logo_small_clear.png"
                  alt="LDlink"
                  style={{ verticalAlign: "bottom" }}
                  width={91}
                  height={36}
                />
              </h2>
            </div>

            <div className="text-center" style={{ maxWidth: "1200px", margin: "auto" }}>
              <p>
                LDlink is a suite of web-based applications designed to easily and efficiently
                interrogate linkage disequilibrium in population groups. Each included application is
                specialized for querying and displaying unique aspects of linkage disequilibrium.
              </p>
            </div>
          </Row>          
          <Row>
            <LdToolSection />
          </Row>
          <Row className="ms-1 me-1">
            <WhatsNew />  
          </Row>
          <Row className="ms-1 me-1">
            <div className="container">

            
            <p style={{ fontSize: "18px" }}><b>Credits</b></p>
            <p> LDlink was developed by <a href="https://dceg.cancer.gov/about/staff-directory/biographies/K-N/machiela-mitchell"
              title="Mitchell Machiela Biography" target="_blank">Mitchell Machiela</a> in collaboration
              with NCI&apos;s Center for Biomedical Informatics and Information
              Technology (CBIIT). Support comes from the Division of Cancer
              Epidemiology and Genetics Informatics Tool Challenge.</p>
            <p>
              This work utilized the computational resources of the NIH STRIDES Initiative (<a href="https://cloud.nih.gov" target="_blank">https://cloud.nih.gov</a>) through the Other Transaction agreement [AWS&#123;*&#125;:&#123;*&#125; OT2OD027852]
            </p>
            <p>
              LDlink&apos;s <a href="https://github.com/CBIIT/nci-webtools-dceg-linkage" target="_blank" >source code</a> is available under the <a href="license.txt" target="_blank" >MIT license</a>, an <a href="https://opensource.org" target="_blank">Open Source Initiative</a> approved license.
            </p>
            <p>
              Questions or comments? Contact us via <a href="mailto:NCILDlinkWebAdmin@mail.nih.gov?subject=LDlink" target="_top" title="Support">email</a>.
            </p>
            <p id="ldlink_version"></p>
            
            

          </div>
          </Row>
        </div>
      </div>
      
    </>
  );
}
