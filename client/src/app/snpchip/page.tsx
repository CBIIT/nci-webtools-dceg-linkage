// app/snpchip/page.tsx
"use client";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import dynamic from "next/dynamic";
import { Container, Row, Col } from "react-bootstrap";
import { ErrorBoundary } from "next/dist/client/components/error-boundary";
import Alert from "react-bootstrap/Alert";
import SnpChipForm from "./form";
import CalculateLoading from "@/components/calculateLoading";
import ToolBanner from "@/components/toolBanner";
import { useStore } from "@/store";

const Results = dynamic(() => import("./results"), {
  ssr: false,
});

export default function SNPchip() {
  const [results, setResults] = useState(null);
  const searchParams = useSearchParams();
  const ref = searchParams.get("ref");
  const genomeBuild = useStore((state) => state.genome_build);

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
            <SnpChipForm
              results={results}
              setResults={setResults}
              genome_build={genomeBuild}
            />
            <ErrorBoundary errorComponent={() => <Alert variant="danger">Error loading results</Alert>}>
              <Suspense fallback={<CalculateLoading />}>
                {results && <Results results={results} genome_build={genomeBuild} />}
              </Suspense>
            </ErrorBoundary>
          </Col>
        </Row>
      </Container>
    </>
  );
}

