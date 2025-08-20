"use client";
import { useSearchParams } from "next/navigation";
import dynamic from "next/dynamic";
import { Suspense } from "react";
import { ErrorBoundary } from "next/dist/client/components/error-boundary";
import Alert from "react-bootstrap/Alert";
import { Container, Row, Col } from "react-bootstrap";
import { useSuspenseQuery } from "@tanstack/react-query";
import Form from "./form";
import CalculateLoading from "@/components/calculateLoading";
import ToolBanner from "@/components/toolBanner";

const Results = dynamic(() => import("./results"), {
  ssr: false,
});

export default function LdTrait() {
  const searchParams = useSearchParams();
  const ref = searchParams.get("ref");

  // Fetch and format GWAS Catalog timestamp
  const { data: timestampData } = useSuspenseQuery({
    queryKey: ["ldtrait_timestamp"],
    queryFn: () => fetch("/LDlinkRestWeb/ldtrait_timestamp").then(res => res.json()).catch(() => null),
  });

  const formatTimestamp = () => {
    if (!timestampData?.$date) return "...";
    const datetime = new Date(timestampData.$date);
    const date = datetime.toLocaleDateString("en-US");
    const time = datetime.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
    const timezone = datetime.toString().match(/([A-Z]+[\+-][0-9]+)/)?.[1] || "";
    return `${date}, ${time} (${timezone})`;
  };

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
            <i>GWAS Catalog last updated on <span id="ldtrait-timestamp">{formatTimestamp()}</span></i>
          </Col>
        </Row>
      </Container>
    </>
  );
}
