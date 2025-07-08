"use client";
import { useSearchParams } from "next/navigation";
import dynamic from "next/dynamic";
import { Suspense } from "react";
import { ErrorBoundary } from "next/dist/client/components/error-boundary";
import Alert from "react-bootstrap/Alert";
import { Container, Row, Col, Form } from "react-bootstrap";
import SNPChipForm from "./form";
import CalculateLoading from "@/components/calculateLoading";
import { useStore } from "@/store";

// const SNPChipResults = dynamic(() => import("./results"), {
//   ssr: false,
// });

export default function SNPchip() {
  const searchParams = useSearchParams();
  const ref = searchParams.get("ref");
  const genome_build = useStore((state) => state.genome_build);
  const setGenomeBuild = useStore((state) => state.setGenomeBuild);

  return (
    <Container fluid="md">
      <Row className="border rounded bg-white my-3 p-3 shadow-sm">
        <Col sm="2">
          <Form.Group controlId="genome_build" className="mb-3">
            <Form.Label>Genome Build (1000G)</Form.Label>
            <Form.Select value={genome_build} onChange={(e) => setGenomeBuild(e.target.value)}>
              <option value="grch37">GRCh37</option>
              <option value="grch38">GRCh38</option>
              <option value="grch38_high_coverage">GRCh38 High Coverage</option>
            </Form.Select>
          </Form.Group>
        </Col>
        <Col>
          <h2 className="text-center ">
            SNPchip Tool
            <sup>
              <a
                href="/docs/#LDassoc"
                target="_blank"
                style={{ fontSize: 20, textDecoration: "none", marginLeft: 5 }}
                title="Click here for documentation">
                <i className="bi bi-info-circle-fill text-primary"></i>
              </a>
            </sup>
          </h2>
          <p className="text-center">
            Find commercial genotyping platforms for variants.
          </p>
        </Col>
        <Col sm="2" />
      </Row>
      <Row className="border rounded bg-white my-3 p-3 shadow-sm">
        <Col><SNPChipForm />
          <ErrorBoundary errorComponent={() => <Alert variant="warning">Error loading results</Alert>}>
            <Suspense fallback={<CalculateLoading />}>
             
            </Suspense>
          </ErrorBoundary>
        
        </Col>
      </Row>
    </Container>
  );
}
