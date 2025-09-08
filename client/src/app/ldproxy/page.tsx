"use client";
import { useSearchParams } from "next/navigation";
import dynamic from "next/dynamic";
import { Suspense, useMemo } from "react";
import { ErrorBoundary } from "next/dist/client/components/error-boundary";
import Alert from "react-bootstrap/Alert";
import { Container, Row, Col, Form } from "react-bootstrap";
import LdProxyForm from "./form";
import CalculateLoading from "@/components/calculateLoading";
import ToolBanner from "@/components/toolBanner";
import { getInitialState } from "@/components/LDproxy/LDproxy.utils";

const LdProxyResults = dynamic(() => import("./results"), {
  ssr: false,
});

export default function LdProxy() {
  const searchParams = useSearchParams();
  const query = useMemo(() => {
    // Attempt to build object from Next.js ReadonlyURLSearchParams
    const spObj: Record<string, string> = {};
    try {
      for (const [k, v] of (searchParams as any).entries()) {
        spObj[k] = v;
      }
    } catch {
      // ignore
    }
    // Fallback to raw window.location.search if no keys found
    if (typeof window !== "undefined" && Object.keys(spObj).length === 0) {
      const manual = new URLSearchParams(window.location.search);
      for (const [k, v] of manual.entries()) {
        spObj[k] = v;
      }
      // eslint-disable-next-line no-console
      console.log("[LDproxy/page] Fallback parsed search params via window.location:", spObj);
    }
    return spObj;
  }, [searchParams]);

  // Debug logging to verify presence of 'pop' in URL query params.
  if (typeof window !== "undefined") {
    // eslint-disable-next-line no-console
    console.log("[LDproxy/page] Current URL:", window.location.href);
    // eslint-disable-next-line no-console
    console.log("[LDproxy/page] Next useSearchParams toString():", searchParams.toString());
    // eslint-disable-next-line no-console
    console.log("[LDproxy/page] Derived query object:", query);
  }
  const initialState = getInitialState(query);
  const ref = searchParams.get("ref");

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
            <LdProxyForm initialState={initialState} />
            <ErrorBoundary errorComponent={() => <Alert variant="warning">Error loading results</Alert>}>
              <Suspense fallback={<CalculateLoading />}>
                {(ref || initialState.submitted) && <LdProxyResults ref={ref || ""} />}
              </Suspense>
            </ErrorBoundary>
          </Col>
        </Row>
      </Container>
    </>
  );
}
