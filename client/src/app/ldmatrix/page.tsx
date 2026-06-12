"use client";
import { useSearchParams } from "next/navigation";
import dynamic from "next/dynamic";
import { Suspense } from "react";
import { ErrorBoundary } from "next/dist/client/components/error-boundary";
import Alert from "react-bootstrap/Alert";
import { Container, Row, Col } from "react-bootstrap";
import LDmatrixForm from "./form";
import CalculateLoading from "@/components/calculateLoading";
import ToolBanner from "@/components/toolBanner";
import CitationBox from "@/components/citationBox";

const Results = dynamic(() => import("./results"), {
  ssr: false,
});

export default function LdAssoc() {
  const searchParams = useSearchParams();
  const ref = searchParams.get("ref");

  return (
    <>
      <ToolBanner
        name="LDmatrix Tool"
        href="/help/#LDmatrix"
        description="Create an interactive heatmap matrix of pairwise linkage disequilibrium statistics."
      />
      <Container fluid="md">
        <Row className="border rounded bg-white my-3 p-3 shadow-sm">
          <Col>
            <LDmatrixForm />
            <ErrorBoundary errorComponent={() => <Alert variant="warning">Error loading results</Alert>}>
              <Suspense fallback={<CalculateLoading />}>{ref && <Results ref={ref} />}</Suspense>
            </ErrorBoundary>
          </Col>
        </Row>
        <Row className="border rounded bg-white my-3 p-3 shadow-sm">
          <CitationBox />
          <div style={{ wordBreak: "normal", overflowWrap: "break-word", marginTop: '1rem' }}>
            Breeze, C.E., Haugen, E., Gutierrez-Arcelus, M., Yao, X., Teschendorff, A., Beck, S., Dunham, I., Stamatoyannopoulos, J., Franceschini, N., Machiela, M.J., Berndt, S.I.{" "}
            <a href="https://doi.org/10.1186/s13059-023-03126-1" target="_blank" rel="noopener noreferrer">
              FORGEdb: a tool for identifying candidate functional variants and uncovering target genes and mechanisms for complex diseases.
            </a>{" "}
            <i>Genome Biology</i>. 2024 Jan 2.
          </div>
        </Row>
      </Container>
    </>
  );
}