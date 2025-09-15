"use client";
import { useSearchParams } from "next/navigation";
import dynamic from "next/dynamic";
import { Suspense } from "react";
import { ErrorBoundary } from "next/dist/client/components/error-boundary";
import Alert from "react-bootstrap/Alert";
import { Container, Row, Col, Form } from "react-bootstrap";
import LdProxyForm from "./form";
import CalculateLoading from "@/components/calculateLoading";
import ToolBanner from "@/components/toolBanner";
import { SubmitFormData } from "./types";

const LdProxyResults = dynamic(() => import("./results"), {
  ssr: false,
});

export default function LdProxy() {
  const searchParams = useSearchParams();
  const ref = searchParams.get("ref");
  const params = Object.fromEntries(searchParams.entries()) as unknown as SubmitFormData;
     

  return (
    <>
      <ToolBanner
        name="LDproxy Tool"
        href="/help/#LDproxy"
        description="Interactively explore proxy and putatively functional variants for a query variant."
      />
      <Container fluid="md">
        <Row className="border rounded bg-white my-3 p-3 shadow-sm">
          <Col>
            <LdProxyForm params={params}/>
            <ErrorBoundary errorComponent={() => <Alert variant="warning">Error loading results</Alert>}>
              <Suspense fallback={<CalculateLoading />}>{ref && <LdProxyResults ref={ref} />}</Suspense>
            </ErrorBoundary>
          </Col>
        </Row>
      </Container>
    </>
  );
}
