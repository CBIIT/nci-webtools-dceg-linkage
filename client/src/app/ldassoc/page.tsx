"use client";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { ErrorBoundary } from "next/dist/client/components/error-boundary";
import Alert from "react-bootstrap/Alert";
import Loading from "@/components/loading";
import { Container, Row, Col } from "react-bootstrap";
import LDAssocForm from "./form";
import LdAssocResults from "./results";
export default function LdAssoc() {
  const searchParams = useSearchParams();
  const ref = searchParams.get("ref");

  return (
    <Container fluid="md">
      <Row className="border rounded bg-white my-3 p-3 shadow-sm">
        <Col>
          <h2 className="text-center ">
            LDassoc Tool
            <sup>
              <a
                id="module-help"
                href="/docs/#LDassoc"
                style={{ fontSize: 20, textDecoration: "none", marginLeft: 5 }}
                title="Click here for documentation">
                <i className="bi bi-info-circle-fill text-primary"></i>
              </a>
            </sup>
          </h2>
          <p id="module-description" className="text-center">
            Interactively visualize association p-value results and linkage disequilibrium patterns for a genomic region
            of interest.
          </p>
        </Col>
      </Row>
      <Row className="border rounded bg-white my-3 p-3 shadow-sm">
        <Col>
          <LDAssocForm />
          <ErrorBoundary errorComponent={() => <Alert variant="warning">Error loading results</Alert>}>
            <Suspense fallback={<Loading message="Loading..." />}>{ref && <LdAssocResults ref={ref} />}</Suspense>
          </ErrorBoundary>
        </Col>
      </Row>
    </Container>
  );
}
