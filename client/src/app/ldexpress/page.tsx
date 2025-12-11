"use client";
import { useSearchParams } from "next/navigation";
import dynamic from "next/dynamic";
import { Suspense } from "react";
import { ErrorBoundary } from "next/dist/client/components/error-boundary";
import Alert from "react-bootstrap/Alert";
import { Container, Row, Col } from "react-bootstrap";
import LDExpressForm from "./form";
import CalculateLoading from "@/components/calculateLoading";
import ToolBanner from "@/components/toolBanner";
import { SubmitFormData } from "./types";

const LdExpressResults = dynamic(() => import("./results"), {
  ssr: false,
});

export default function LdExpress() {
  const searchParams = useSearchParams();
  const ref = searchParams.get("ref");
  const params = Object.fromEntries(searchParams.entries()) as unknown as SubmitFormData;
  return (
    <>
      <ToolBanner
        name="LDexpress Tool"
        href="/help/#LDexpress"
        description="Search if a list of variants (or variants in LD with those variants) is associated with gene expression in multiple tissue types."
      />
      <Container fluid="md">
        <Row className="border rounded bg-white my-3 p-3 shadow-sm">
          <Col>
            <LDExpressForm  params={params}/>
            <ErrorBoundary errorComponent={() => <Alert variant="warning">Error loading results</Alert>}>
              <Suspense fallback={<CalculateLoading />}>{ref && <LdExpressResults ref={ref} />}</Suspense>
            </ErrorBoundary>
            <i>GTEx v8</i>
          </Col>
        </Row>
      </Container>
    </>
  );
}
