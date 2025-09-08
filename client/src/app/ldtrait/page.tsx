"use client";
import { useSearchParams } from "next/navigation";
import dynamic from "next/dynamic";
import { Suspense, useMemo } from "react";
import { ErrorBoundary } from "next/dist/client/components/error-boundary";
import Alert from "react-bootstrap/Alert";
import { Container, Row, Col } from "react-bootstrap";
import { useQuery } from "@tanstack/react-query";
import Form from "./form";
import CalculateLoading from "@/components/calculateLoading";
import ToolBanner from "@/components/toolBanner";
import { submitFormData } from "./types";

const Results = dynamic(() => import("./results"), {
  ssr: false,
});

export default function LdTrait() {
  const searchParams = useSearchParams();

  // Build normalized params object supporting deep links (var -> snps, pop separators, defaults)
  const params = useMemo(() => {
    const raw = Object.fromEntries(searchParams.entries());
    const safeDecode = (val?: string) => {
      if (!val) return "";
      try {
        return decodeURIComponent(val);
      } catch {
        return val;
      }
    };
    const normalizePop = (val?: string) =>
      safeDecode(val || "")
        .replace(/,/g, "+")
        .replace(/\s+/g, "+")
        .replace(/\++/g, "+")
        .replace(/^\+|\+$/g, "");

    const snps = raw.snps || raw.var || "";
    const pop = normalizePop(raw.pop || "");
    const r2_d = raw.r2_d === "d" ? "d" : "r2";

    const normalized: submitFormData = {
      snps,
      pop,
      r2_d,
      r2_d_threshold: raw.r2_d_threshold || "0.1",
      window: raw.window || "500000",
      genome_build: raw.genome_build || "grch37",
      reference: raw.reference || "",
      ifContinue: (raw.ifContinue === "False" ? "False" : "Continue") as "Continue" | "False",
    };
    return normalized;
  }, [searchParams]);

  // Fetch and format GWAS Catalog timestamp
  const { data: timestampData, isLoading: timestampLoading } = useQuery({
    queryKey: ["ldtrait_timestamp"],
    queryFn: () =>
      fetch("/LDlinkRestWeb/ldtrait_timestamp")
        .then((res) => res.json())
        .catch(() => null),
  });

  const formatTimestamp = () => {
    if (timestampLoading) return "Loading...";
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
            <Form params={params} />
            <ErrorBoundary errorComponent={() => <Alert variant="warning">Error loading results</Alert>}>
              <Suspense fallback={<CalculateLoading />}>{params.reference && <Results {...params} />}</Suspense>
            </ErrorBoundary>
            <i>
              GWAS Catalog last updated on <span id="ldtrait-timestamp">{formatTimestamp()}</span>
            </i>
          </Col>
        </Row>
      </Container>
    </>
  );
}
