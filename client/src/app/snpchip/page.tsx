// app/snpchip/page.tsx
"use client";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { Container, Row, Col } from "react-bootstrap";
import SnpChipForm from "./form";
import CalculateLoading from "@/components/calculateLoading";
import ToolBanner from "@/components/toolBanner";

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
            <Suspense fallback={<CalculateLoading />}>
              <SnpChipForm />
            </Suspense>
          </Col>
        </Row>
      </Container>
    </>
  );
}

