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
          <Row>
            <WhatsNew />  
          </Row>
          <Row>
            <div className="container">

            <br/>
            <p style={{ fontSize: "18px" }}><b>Credits</b></p>
            <p> LDlink was developed by <a href="https://dceg.cancer.gov/about/staff-directory/biographies/K-N/machiela-mitchell"
              title="Mitchell Machiela Biography" target="_blank">Mitchell Machiela</a> in collaboration
              with NCI&apos;s Center for Biomedical Informatics and Information
              Technology (CBIIT). Support comes from the Division of Cancer
              Epidemiology and Genetics Informatics Tool Challenge.</p>

            
            

          </div>
          </Row>
        </div>
      </div>
      <div className="bg-light py-5 flex-grow-1">
        <div>
          <Row>
            <Col>
              <p>
                Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aliquam id dictum sapien. Nam suscipit erat vel
                facilisis sagittis. Fusce a ante sed magna malesuada tincidunt. Ut pretium, ante eget suscipit egestas,
                augue ligula vestibulum justo, id interdum nunc odio et odio. Sed sed egestas nisl, aliquam imperdiet
                quam. Duis pellentesque purus cursus, molestie felis eget, facilisis nisl. Phasellus convallis lectus
                vitae nibh imperdiet commodo. Integer rhoncus imperdiet mauris. Suspendisse at dolor felis. Vestibulum
                ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia curae; Nam imperdiet elit orci,
                nec condimentum lectus sollicitudin eu. Aenean felis nunc, accumsan a arcu ut, sagittis ornare lorem.
                Sed ac lorem et dui faucibus pharetra vel sed ipsum. Quisque varius erat euismod dolor lacinia commodo.
                Phasellus sed ultrices neque, sit amet consectetur nisl.
              </p>
              <div>
                <p className="h6">Reference</p>
                <ol>
                  <li>
                    Sed fringilla elementum convallis. Morbi vehicula sapien sit amet quam facilisis, id gravida massa
                    volutpat. Nulla venenatis aliquam mi eu finibus. Proin at congue magna, in tempor dui. Suspendisse
                    potenti. Quisque pharetra sagittis volutpat. Suspendisse laoreet risus et tempor sollicitudin.
                  </li>
                </ol>
              </div>
            </Col>
          </Row>
        </div>
      </div>
    </>
  );
}
