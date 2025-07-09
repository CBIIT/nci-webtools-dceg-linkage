"use client";
import { useSearchParams } from "next/navigation";
import { useState, Suspense } from "react";
import { Container, Row, Col, Form, Alert } from "react-bootstrap";
import SnpChipForm from "./form";
import CalculateLoading from "@/components/calculateLoading";
import SNPChipResults from "./results"; // New component for results
import { useStore } from "@/store";

export default function SNPchip() {
  const searchParams = useSearchParams();
  const ref = searchParams.get("ref");

  const genome_build = useStore((state) => state.genome_build);
  const setGenomeBuild = useStore((state) => state.setGenomeBuild);

  const [input, setInput] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectAllIllumina, setSelectAllIllumina] = useState(true);
  const [selectAllAffymetrix, setSelectAllAffymetrix] = useState(true);
  const [results, setResults] = useState<any>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    const formData = new FormData();

    if (file) formData.append("file", file);
    else formData.append("input", input);

    formData.append("illumina", selectAllIllumina.toString());
    formData.append("affymetrix", selectAllAffymetrix.toString());

    try {
      const res = await fetch("/snpchip", {
        method: "POST",
        body: formData,
      });
      if (!res.ok) throw new Error("Failed to fetch results");
      const data = await res.json();
      setResults(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

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
          <h2 className="text-center">
            SNPchip Tool
            <sup>
              <a
                href="/docs/#LDassoc"
                target="_blank"
                style={{ fontSize: 20, textDecoration: "none", marginLeft: 5 }}
                title="Click here for documentation"
              >
                <i className="bi bi-info-circle-fill text-primary"></i>
              </a>
            </sup>
          </h2>
          <p className="text-center">Find commercial genotyping platforms for variants.</p>
        </Col>
        <Col sm="2" />
      </Row>
      <Row className="border rounded bg-white my-3 p-3 shadow-sm">
        <Col>
          <SnpChipForm
            handleSubmit={handleSubmit}
            input={input}
            setInput={setInput}
            file={file}
            setFile={setFile}
            loading={loading}
            selectAllIllumina={selectAllIllumina}
            setSelectAllIllumina={setSelectAllIllumina}
            selectAllAffymetrix={selectAllAffymetrix}
            setSelectAllAffymetrix={setSelectAllAffymetrix}
          />
          <Suspense fallback={<CalculateLoading />}>
            {results && <SNPChipResults results={results} />}
          </Suspense>
        </Col>
      </Row>
    </Container>
  );
} 