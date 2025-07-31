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

const Results = dynamic(() => import("./results"), {
  ssr: false,
});

export default function LdTrait() {
  const searchParams = useSearchParams();
  const ref = searchParams.get("ref");

  return (
    <>
      <ToolBanner
        name="LDtrait Tool"
        href="/help/#LDtrait"
        description="Search if a list of variants (or variants in LD with those variants) have previously been associated with a trait or disease."
      />
      <Container fluid="md">
        <Row className="border rounded bg-white my-3 p-3 shadow-sm">
          <Col>
            <Form />
            <ErrorBoundary errorComponent={() => <Alert variant="warning">Error loading results</Alert>}>
              <Suspense fallback={<CalculateLoading />}>{ref && <Results ref={ref} />}</Suspense>
            </ErrorBoundary>
          </Col>
        </Row>
      </Container>
    </>
  );
}
