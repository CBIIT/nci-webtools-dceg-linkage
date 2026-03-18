"use client";
import { useSearchParams } from "next/navigation";
import dynamic from "next/dynamic";
import { Suspense } from "react";
import { ErrorBoundary } from "next/dist/client/components/error-boundary";
import Alert from "react-bootstrap/Alert";
import { Container, Row, Col, Form } from "react-bootstrap";
import LDAssocForm from "./form";
import CalculateLoading from "@/components/calculateLoading";
import ToolBanner from "@/components/toolBanner";
import CitationBox from "../../components/citationBox";

const LdAssocResults = dynamic(() => import("./results"), {
  ssr: false,
});

export default function LdAssoc() {
  const searchParams = useSearchParams();
  const ref = searchParams.get("ref");

  return (
    <>
      <ToolBanner
        name="LDassoc Tool"
        href="/help/#LDassoc"
        description="Interactively visualize association p-value results and linkage disequilibrium patterns for a genomic
              region of interest."
      />
      <Container fluid="md">
        <Row className="border rounded bg-white my-3 p-3 shadow-sm">
          <Col>
            <LDAssocForm />
            <ErrorBoundary errorComponent={() => <Alert variant="warning">Error loading results</Alert>}>
              <Suspense fallback={<CalculateLoading />}>{ref && <LdAssocResults ref={ref} />}</Suspense>
            </ErrorBoundary>
          </Col>
        </Row>
        <Row className="border rounded bg-white my-3 p-3 shadow-sm">
        <CitationBox />
          <div style={{ wordBreak: "normal", overflowWrap: "break-word", marginTop: '1rem' }}>
            Machiela MJ, Chanock SJ. <a href="http://www.ncbi.nlm.nih.gov/pubmed/?term=28968746" target="_blank" rel="noopener noreferrer" >LDassoc: an online tool for interactively exploring genome-wide association study results and prioritizing variants for functional investigation.</a> Bioinformatics. 2017 Sept 12.
          </div>
        </Row>
      </Container>
    </>
  );
}
