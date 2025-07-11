// app/snpchip/page.tsx
"use client";
import { useSearchParams } from "next/navigation";
import { useState, Suspense } from "react";
import { Container, Row, Col, Form, Alert } from "react-bootstrap";
import SnpChipForm, { Platform } from "./form";
import CalculateLoading from "@/components/calculateLoading";
import SNPChipResults, { SnpchipResult } from "./results";
import { useStore } from "@/store";
import { snpchip } from "@/services/queries";

interface SnpChipPayload {
  snps: string;
  platforms: string;
  genome_build: string;
  reference: number;
}

export default function SNPchip() {
  const searchParams = useSearchParams();
  const ref = searchParams.get("ref");

  const genome_build = useStore((state) => state.genome_build);
  const setGenomeBuild = useStore((state) => state.setGenomeBuild);

  const [input, setInput] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [illuminaChips, setIlluminaChips] = useState<Platform[]>([]);
  const [affymetrixChips, setAffymetrixChips] = useState<Platform[]>([]);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [warning, setWarning] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResults(null);
    setError(null);
    setWarning(null);

    let snpsData = input;
    if (file) {
      try {
        snpsData = await file.text();
      } catch (err) {
        setError("Error reading file.");
        setLoading(false);
        return;
      }
    }

    if (!snpsData) {
      setError("Please provide a list of SNPs or upload a file.");
      setLoading(false);
      return;
    }

    const selectedPlatforms = [...illuminaChips, ...affymetrixChips]
      .map((p) => p.id)
      .join("+");

    if (!selectedPlatforms) {
      setError("Please select at least one platform.");
      setLoading(false);
      return;
    }

    const payload: SnpChipPayload = {
      snps: snpsData,
      platforms: selectedPlatforms,
      genome_build: genome_build,
      reference: ref
        ? parseInt(ref, 10)
        : Math.floor(Math.random() * (99999 - 10000 + 1) + 10000),
    };

    try {
      const raw = await snpchip(payload);

      let data = raw;
      if (typeof raw === "string") {
        try {
          data = JSON.parse(raw);
        } catch (err) {
          setError("Failed to parse SNPchip response.");
          setLoading(false);
          return;
        }
      }

      console.log("SNPchip results:", data);
      if (data.error) {
        setError(data.error);
        return;
      }

      if (data.warning) {
        setWarning(data.warning);
      }

      const snpchipRows = Object.entries(data)
        .filter(([key]) => !isNaN(Number(key)))
        .map(([_, row]: [string, any[]]) => {
          const rs_number = row[0];
          const position = row[1];
          const platformsStr = row[2] || "";
          const map = platformsStr
            ? platformsStr.split(",").map((v) => v.trim()).filter(Boolean)
            : [];
          return { rs_number, position, map };
        });

      console.log("SNPchip parsed rows:", snpchipRows);

      if (snpchipRows.length > 0) {
        const uniquePlatformNames = new Set<string>();
        snpchipRows.forEach((row) =>
          row.map.forEach((p: string) => p && uniquePlatformNames.add(p))
        );

        const headers = Array.from(uniquePlatformNames).map((name) => ({
          code: name,
          platform: name,
        }));

        const mappedSnpchip = snpchipRows.map((row) => ({
          ...row,
          map: headers.map((h) => (row.map.includes(h.code) ? "X" : "")),
        }));

        const detailsText = [
          ["RS Number", "Position", ...headers.map((h) => h.platform)].join("\t"),
          ...mappedSnpchip.map((row) =>
            [
              row.rs_number,
              row.position,
              ...row.map.map((v) => (v === "X" ? "X" : "")),
            ].join("\t")
          ),
        ].join("\n");

        const transformedResults: SnpchipResult = {
          snpchip: mappedSnpchip,
          headers,
          details: detailsText,
        };
        setResults(transformedResults);
      } else if (!data.warning) {
        setWarning("No results found for the given SNPs.");
      }
    } catch (err) {
      console.error(err);
      setError("An unexpected error occurred.");
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
            <Form.Select
              value={genome_build}
              onChange={(e) => setGenomeBuild(e.target.value)}
            >
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
                style={{
                  fontSize: 20,
                  textDecoration: "none",
                  marginLeft: 5,
                }}
                title="Click here for documentation"
              >
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
        <Col>
          <Suspense fallback={<CalculateLoading />}>
            <SnpChipForm
              handleSubmit={handleSubmit}
              input={input}
              setInput={setInput}
              file={file}
              setFile={setFile}
              loading={loading}
              illuminaChips={illuminaChips}
              setIlluminaChips={setIlluminaChips}
              affymetrixChips={affymetrixChips}
              setAffymetrixChips={setAffymetrixChips}
            />
          </Suspense>
          {loading && <CalculateLoading />}
          {error && <Alert variant="danger">{error}</Alert>}
          {warning && <Alert variant="warning">{warning}</Alert>}
          <Suspense fallback={<CalculateLoading />}>
            {results && <SNPChipResults results={results} />}
          </Suspense>
        </Col>
      </Row>
    </Container>
  );
}
