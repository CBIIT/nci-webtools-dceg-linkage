// app/snpchip/page.tsx
"use client";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import dynamic from "next/dynamic";
import { Container, Row, Col } from "react-bootstrap";
import { ErrorBoundary } from "next/dist/client/components/error-boundary";
import Alert from "react-bootstrap/Alert";
import SnpChipForm from "./form";
import CalculateLoading from "@/components/calculateLoading";
import ToolBanner from "@/components/toolBanner";

const Results = dynamic(() => import("./results"));

export default function SNPchip() {
  const searchParams = useSearchParams();
  const ref = searchParams.get("ref");

  return (
    <>
      <ToolBanner
        name="SNPchip Tool"
        href="/help/#SNPchip"
        description="Find commercial genotyping platforms for variants."
      />
      <Container fluid="md">
        <Row className="border rounded bg-white my-3 p-3 shadow-sm">
          <Col>
            <SnpChipForm />
            <ErrorBoundary errorComponent={() => <Alert variant="warning">Error loading results</Alert>}>
              <Suspense fallback={<CalculateLoading />}>
                {ref && <Results ref={ref} />}
              </Suspense>
            </ErrorBoundary>
          </Col>
        </Row>
      </Container>
    </>
  );
}

