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
      </Container>
    </>
  );
}
