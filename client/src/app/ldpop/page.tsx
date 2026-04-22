"use client";
import { useSearchParams } from "next/navigation";
import dynamic from "next/dynamic";
import { Suspense } from "react";
import { ErrorBoundary } from "next/dist/client/components/error-boundary";
import Alert from "react-bootstrap/Alert";
import { Container, Row, Col } from "react-bootstrap";
import Form from "./form";
import CalculateLoading from "@/components/calculateLoading";
import ToolBanner from "@/components/toolBanner";
import CitationBox from "../../components/citationBox";
import { submitFormData } from "./types";

const Results = dynamic(() => import("./results"), {
  ssr: false,
});

export default function LdPop() {
  const searchParams = useSearchParams();
  const params = Object.fromEntries(searchParams.entries()) as unknown as submitFormData;

  return (
    <>
      <ToolBanner
        name="LDpop Tool"
        href="/help/#LDpop"
        description="Investigate allele frequencies and linkage disequilibrium patterns across 1000G populations."
      />
      <Container fluid="md">
        <Row className="border rounded bg-white my-3 p-3 shadow-sm">
          <Col>
            <Form params={params} />
            <ErrorBoundary errorComponent={() => <Alert variant="warning">Error loading results</Alert>}>
              <Suspense fallback={<CalculateLoading />}>{params?.reference && <Results {...params} />}</Suspense>
            </ErrorBoundary>
          </Col>
        </Row>
        <Row className="border rounded bg-white my-3 p-3 shadow-sm">
          <CitationBox />
          <div style={{ wordBreak: "normal", overflowWrap: "break-word", marginTop: '1rem' }}>
              Alexander TA, Machiela MJ. <a href="https://www.ncbi.nlm.nih.gov/pubmed/?term=31924160" target="_blank" rel="noopener noreferrer">LDpop: an interactive online tool to calculate and visualize geographic LD patterns.</a> BMC Bioinformatics. 2020 Jan 10.
          </div>
        </Row>
      </Container>
    </>
  );
}
