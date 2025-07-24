// app/snpchip/page.tsx
"use client";
import { useSearchParams } from "next/navigation";
import { useState, Suspense } from "react";
import { Container, Row, Col, Form, Alert, Card } from "react-bootstrap";
import SnpChipForm, { Platform } from "./form";
import CalculateLoading from "@/components/calculateLoading";
import SNPChipResults, { SnpchipResult } from "./results";
import { useStore } from "@/store";
import { snpchip } from "@/services/queries";
import { PLATFORM_LOOKUP } from "./constants";

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

      // console.log("SNPchip results:", data);
      if (data.error) {
        setError(data.error);
        return;
      }

      if (data.warning) {
        setWarning(data.warning);
      }

      const db = genome_build === 'grch37' ? 'hg19' : 'hg38';

      const snpchipRows = Object.entries(data)
        .filter(([key]) => !isNaN(Number(key)))
        .map(([_, row]) => {
          if (!Array.isArray(row)) return null;
          const rs_number_raw = String(row[0]);
          const position_raw = String(row[1]);

          const platformsStr = row[2] || "";
          const map = platformsStr
            ? platformsStr.split(",").map((v: string) => v.trim()).filter(Boolean)
            : [];
          return { map, rs_number_raw, position_raw };
        })
        .filter((row): row is { map: string[]; rs_number_raw: string; position_raw: string; } => row !== null);

      

      if (snpchipRows.length > 0) {
        const uniquePlatformNames = new Set<string>();
        snpchipRows.forEach((row) => {
          row.map.forEach((p: string) => p && uniquePlatformNames.add(p))
        });

        const headers = Array.from(uniquePlatformNames).map((name) => ({
          code: PLATFORM_LOOKUP[name] || name,
          platform: name,
        }));

        // Sort headers alphabetically by full platform name
        headers.sort((a, b) => a.platform.localeCompare(b.platform));

        const mappedSnpchip = snpchipRows.map((row) => {
          return {
            ...row,
            map: headers.map((h) => (row.map.includes(h.platform) ? "\u2714" : "")),
          };
        });

        const detailsText = [
          ["RS Number", "Position", ...headers.map((h) => h.platform)].join("\t"),
          ...mappedSnpchip.map((row) => {
            return [
              row.rs_number_raw,
              "chr" + row.position_raw,
              ...row.map.map((v) => (v === "\u2714" ? "\u2714" : "")),
            ].join("\t");
          }),
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
          <h1 className="text-center h2">
            SNPchip Tool
            <sup>
              <a
                href="/help/#SNPchip"
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
          </h1>
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
          {warning && (
            <Row className="justify-content-center my-3">
              <Col sm={8} md={7}>
                <Card border="warning">
                  <Card.Header className="bg-warning">Warning</Card.Header>
                  <Card.Body>
                    <Card.Text>{warning}</Card.Text>
                  </Card.Body>
                </Card>
              </Col>
            </Row>
          )}
          <Suspense fallback={<CalculateLoading />}>
            {results && <SNPChipResults results={results} genome_build={genome_build} />}
          </Suspense>
        </Col>
      </Row>
    </Container>
  );
}
            
