"use client";
import { useSearchParams } from "next/navigation";
import dynamic from "next/dynamic";
import React, { Suspense } from "react";
import Alert from "react-bootstrap/Alert";
import { Container, Row, Col } from "react-bootstrap";
import Form from "./form";
import CalculateLoading from "@/components/calculateLoading";
import ToolBanner from "@/components/toolBanner";
import { ErrorBoundary } from "next/dist/client/components/error-boundary";

const Results = dynamic(() => import("./results"), {
  ssr: false,
});

export default function SNPclip() {
  const searchParams = useSearchParams();
  const ref = searchParams.get("ref");

  return (
    <>
      <ToolBanner
        name="SNPclip"
        href="/help/#SNPclip"
        description="Prune a list of variants by linkage disequilibrium."
      />
      <Container fluid="md">
        <Row className="border rounded bg-white my-3 p-3 shadow-sm">
          <Col>
            <Form />
            <ErrorBoundary errorComponent={() => <Alert variant="warning">Error loading results</Alert>}>
              <Suspense fallback={<CalculateLoading />}>{ref && <Results ref_id={ref} />}</Suspense>
            </ErrorBoundary>
          </Col>
        </Row>
      </Container>
    </>
  );
}
