"use client";
import { useSearchParams } from "next/navigation";
import dynamic from "next/dynamic";
import { Suspense, useMemo } from "react";
import { ErrorBoundary } from "next/dist/client/components/error-boundary";
import Alert from "react-bootstrap/Alert";
import { Container, Row, Col } from "react-bootstrap";
import LDExpressForm from "./form";
import CalculateLoading from "@/components/calculateLoading";
import ToolBanner from "@/components/toolBanner";

const LdExpressResults = dynamic(() => import("./results"), {
  ssr: false,
});

export default function LdExpress() {
  const searchParams = useSearchParams();
  const ref = searchParams.get("ref");

  // Normalize deep-link params (similar to ldtrait)
  const params = useMemo(() => {
    const raw = Object.fromEntries(searchParams.entries());
    const safeDecode = (val?: string) => {
      if (!val) return "";
      try { return decodeURIComponent(val); } catch { return val; }
    };
    const normalizeList = (val?: string) => safeDecode(val || "")
      .replace(/,/g, "+")
      .replace(/\s+/g, "+")
      .replace(/\++/g, "+")
      .replace(/^\+|\+$/g, "");

    return {
      snps: raw.snps || raw.var || "",
      pop: normalizeList(raw.pop || ""),
      tissues: normalizeList(raw.tissues || ""),
      r2_d: raw.r2_d === "d" ? "d" : "r2",
      p_threshold: raw.p_threshold || "0.1",
      r2_d_threshold: raw.r2_d_threshold || "0.1",
      window: raw.window || "500000",
      genome_build: raw.genome_build || "grch37",
      autorun: raw.autorun === '1' ? '1' : '',
      reference: raw.reference || "",
    };
  }, [searchParams]);

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
            <LDExpressForm params={params} />
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
