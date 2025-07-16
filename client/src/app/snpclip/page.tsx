"use client";
import { useSearchParams } from "next/navigation";
import dynamic from "next/dynamic";
import React, { Suspense } from "react";
import Alert from "react-bootstrap/Alert";
import { Container, Row, Col } from "react-bootstrap";
import Form from "./form";
import CalculateLoading from "@/components/calculateLoading";
import ToolBanner from "@/components/toolBanner";

const Results = dynamic(() => import("./results"), {
  ssr: false,
});

class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return <Alert variant="warning">Error loading results</Alert>;
    }

    return this.props.children;
  }
}

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
            <ErrorBoundary>
              <Suspense fallback={<CalculateLoading />}>{ref && <Results ref_id={ref} />}</Suspense>
            </ErrorBoundary>
          </Col>
        </Row>
      </Container>
    </>
  );
}
