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
import { submitFormData } from "./types";

const Results = dynamic(() => import("./results"), {
  ssr: false,
});

export default function LdPair() {
  const searchParams = useSearchParams();
  const params = Object.fromEntries(searchParams.entries()) as unknown as submitFormData;

  return (
    <>
      <ToolBanner
        name="LDpair Tool"
        href="/help/#LDpair"
        description="Investigate correlated alleles for a pair of variants in high LD."
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
      </Container>
    </>
  );
}
