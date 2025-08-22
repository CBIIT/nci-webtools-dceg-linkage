"use client";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { Row, Col, Form, Button, Accordion, Spinner, Alert, Card } from "react-bootstrap";
import { snpchipPlatforms, snpchip } from "@/services/queries";
import CalculateLoading from "@/components/calculateLoading";
import { FormData } from "./types";
import { parseSnps } from "@/services/utils";
import { Platform } from "./types";
import MultiSnp from "@/components/form/multiSnp";

function CheckboxList({
  options,
  selected,
  setSelected,
  type,
}: {
  options: Platform[];
  selected: Platform[];
  setSelected: (val: Platform[]) => void;
  type: "illumina" | "affymetrix";
}) {
  const toggle = (option: Platform) => {
    if (selected.some((item) => item.id === option.id)) {
      setSelected(selected.filter((item) => item.id !== option.id));
    } else {
      setSelected([...selected, option]);
    }
  };
  return (
    <>
      {options.map((option) => (
        <Form.Check
          key={option.id}
          id={`${type}-${option.id}`}
          type="checkbox"
          className={type}
          label={`${option.name} (${option.id})`}
          checked={selected.some((item) => item.id === option.id)}
          onChange={() => toggle(option)}
        />
      ))}
    </>
  );
}

export default function SNPChipForm({
  results,
  setResults,
  genome_build,
}: {
  results: any;
  setResults: (val: any) => void;
  genome_build: string;
}) {
  // All state and logic are now managed here except results and genome_build
  const [input, setInput] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [illuminaChips, setIlluminaChips] = useState<Platform[]>([]);
  const [affymetrixChips, setAffymetrixChips] = useState<Platform[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [warning, setWarning] = useState<string | null>(null);

  const defaultForm: FormData = {
    snps: "",
    pop: [],
    genome_build: genome_build || "grch37",
    varFile: "",
    platforms: [],
  };
  const {
    control,
    register,
    handleSubmit: formHandleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors },
  } = useForm<FormData>({
    defaultValues: defaultForm,
  });

  const varFile = watch("varFile") as string | FileList;
  const [availableIllumina, setAvailableIllumina] = useState<Platform[]>([]);
  const [availableAffymetrix, setAvailableAffymetrix] = useState<Platform[]>([]);
  const [platformsLoading, setPlatformsLoading] = useState(true);
  const [selectAllIllumina, setSelectAllIllumina] = useState(true);
  const [selectAllAffymetrix, setSelectAllAffymetrix] = useState(true);
  const [uploadedFileName, setUploadedFileName] = useState<string>("");
  const [accordionOpen, setAccordionOpen] = useState<string | string[] | null>(null);
  const [platformLookup, setPlatformLookup] = useState<Record<string, string>>({});

  useEffect(() => {
    async function fetchPlatforms() {
      try {
        setPlatformsLoading(true);
        const data = await snpchipPlatforms();
        
        // Create platform lookup (reverse mapping: fullName -> code)
        const lookup: Record<string, string> = {};
        for (const [code, fullName] of Object.entries(data)) {
          lookup[fullName as string] = code;
        }
        
        const illumina: Platform[] = [];
        const affymetrix: Platform[] = [];
        for (const key in data) {
          if (key.startsWith("I_")) {
            illumina.push({ id: key, name: data[key] });
          } else if (key.startsWith("A_")) {
            affymetrix.push({ id: key, name: data[key] });
          }
        }
        setAvailableIllumina(illumina);
        setAvailableAffymetrix(affymetrix);
        setIlluminaChips(illumina);
        setAffymetrixChips(affymetrix);
        setPlatformLookup(lookup);
      } catch (error) {
        console.error("Failed to fetch SNPchip platforms", error);
      } finally {
        setPlatformsLoading(false);
      }
    }
    fetchPlatforms();
  }, []);

  useEffect(() => {
    setSelectAllIllumina(availableIllumina.length > 0 && illuminaChips.length === availableIllumina.length);
    setSelectAllAffymetrix(availableAffymetrix.length > 0 && affymetrixChips.length === availableAffymetrix.length);
  }, [illuminaChips, affymetrixChips, availableIllumina, availableAffymetrix, setIlluminaChips, setAffymetrixChips]);

  useEffect(() => {
    if (varFile instanceof FileList && varFile.length > 0) {
      const file = varFile[0];
      setUploadedFileName(file.name);
      const reader = new FileReader();
      reader.onload = (e: ProgressEvent<FileReader>) => {
        const text = e.target?.result as string;
        if (text) {
          setValue("snps", parseSnps(text));
        }
      };
      reader.readAsText(file);
    } else {
      setUploadedFileName("");
    }
  }, [varFile, setValue, reset]);

  const onSubmit = async (form: FormData) => {
    setLoading(true);
    setResults(null);
    setError(null);
    setWarning(null);

    let snpsData = form.snps;
    if (varFile instanceof FileList && varFile.length > 0) {
      try {
        snpsData = await varFile[0].text();
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

    const selectedPlatforms = [...illuminaChips, ...affymetrixChips].map((p) => p.id).join("+");

    if (!selectedPlatforms) {
      setError("Please select at least one platform.");
      setLoading(false);
      return;
    }

    const payload = {
      snps: snpsData,
      platforms: selectedPlatforms,
      genome_build: genome_build,
      reference: Math.floor(Math.random() * (99999 - 10000 + 1) + 10000),
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
      if (data.error) {
        setError(data.error);
        return;
      }
      if (data.warning) {
        setWarning(data.warning);
      }
      // Transform and display results
      const db = genome_build === "grch37" ? "hg19" : "hg38";
      const snpchipRows = Object.entries(data)
        .filter(([key]) => !isNaN(Number(key)))
        .map(([_, row]) => {
          if (!Array.isArray(row)) return null;
          const rs_number_raw = String(row[0]);
          const position_raw = String(row[1]);
          const platformsStr = row[2] || "";
          const map = platformsStr
            ? platformsStr
                .split(",")
                .map((v: string) => v.trim())
                .filter(Boolean)
            : [];
          return { map, rs_number_raw, position_raw };
        })
        .filter((row) => row !== null);
      if (snpchipRows.length > 0) {
        const uniquePlatformNames = new Set<string>();
        snpchipRows.forEach((row) => {
          row.map.forEach((p: string) => p && uniquePlatformNames.add(p));
        });
        const headers = Array.from(uniquePlatformNames).map((name) => ({
          code: platformLookup[name] || name,
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
        const transformedResults = {
          snpchip: mappedSnpchip,
          headers,
          details: detailsText,
        };
        setResults(transformedResults);
        setAccordionOpen(null);
      } else if (!data.warning) {
        setWarning("No results found for the given SNPs.");
      }
    } catch (err) {
      setError("An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  function onReset(event: React.FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    // Reset form to default values
    reset(defaultForm);
    // Reset component state
    setInput("");
    setFile(null);
    setResults(null);
    setError(null);
    setWarning(null);
    setUploadedFileName("");
    // Reset platform selections to all selected
    setIlluminaChips(availableIllumina);
    setAffymetrixChips(availableAffymetrix);
    // Close the accordion
    setAccordionOpen(null);
  }

  return (
    <Form id="snpchip-form" onSubmit={formHandleSubmit(onSubmit)} onReset={onReset} noValidate>
      <Row className="mb-3 align-items-start">
        <Col sm="auto">
          <MultiSnp name="snps" register={register} errors={errors} />
        </Col>
        <Col sm={3}>
          <Form.Group controlId="varFile" className="mb-3">
            <Form.Label>Upload file with variants</Form.Label>
            {typeof varFile === "string" && varFile !== "" ? (
              <div className="form-control bg-light">{varFile}</div>
            ) : (
              <Form.Control placeholder="Upload" type="file" {...register("varFile")} />
            )}
          </Form.Group>
        </Col>
        <Col />
        <Col sm={3} className="d-flex justify-content-end">
          <Button type="reset" variant="outline-danger" className="me-1">
            Reset
          </Button>
          <Button type="submit" variant="primary" disabled={loading}>
            {loading ? <Spinner animation="border" size="sm" /> : "Calculate"}
          </Button>
        </Col>
      </Row>
      <Accordion className="mb-4 accordion-bg" activeKey={accordionOpen} onSelect={(eventKey) => setAccordionOpen(eventKey || null)}>
        <Accordion.Item eventKey="0">
          <Accordion.Header>
            <div className="d-flex justify-content-between w-100 align-items-center snpchip-accordion">
              <span>Filter by array</span>
              {!platformsLoading && (
                <small className="text-muted me-2">
                  {illuminaChips?.length || 0} Illumina array(s), and {affymetrixChips?.length || 0} Affymetrix array(s)
                  selected
                </small>
              )}
            </div>
          </Accordion.Header>
          <Accordion.Body>
            {platformsLoading ? (
              <div className="text-center">
                <Spinner animation="border" size="sm" /> Loading platforms...
              </div>
            ) : (
              <>
                {illuminaChips.length === availableIllumina.length &&
                affymetrixChips.length === availableAffymetrix.length ? (
                  <p className="instruction">
                    Limit search results to only SNPs on the selected arrays (
                    <span
                      id="selectAllChipTypes"
                      className="underlined"
                      style={{ textDecoration: "underline", cursor: "pointer", color: "blue" }}
                      onClick={() => {
                        setIlluminaChips([]);
                        setAffymetrixChips([]);
                      }}>
                      unselect all
                    </span>
                    )
                  </p>
                ) : (
                  <p className="instruction">
                    Limit search results to only SNPs on the selected arrays (
                    <span
                      id="selectAllChipTypes"
                      className="underlined"
                      style={{ textDecoration: "underline", cursor: "pointer", color: "blue" }}
                      onClick={() => {
                        setIlluminaChips(availableIllumina);
                        setAffymetrixChips(availableAffymetrix);
                      }}>
                      select all
                    </span>
                    )
                  </p>
                )}
                <Row>
                  <Col>
                    <Form.Check
                      type="checkbox"
                      id="selectAllIllumina"
                      label={<strong>Select All Illumina</strong>}
                      checked={selectAllIllumina}
                      onChange={(e) => {
                        const checked = e.target.checked;
                        setSelectAllIllumina(checked);
                        setIlluminaChips(checked ? availableIllumina : []);
                      }}
                    />
                    <CheckboxList
                      options={availableIllumina}
                      selected={illuminaChips}
                      setSelected={setIlluminaChips}
                      type="illumina"
                    />
                  </Col>
                  <Col>
                    <Form.Check
                      type="checkbox"
                      id="selectAllAffymetrix"
                      label={<strong>Select All Affymetrix</strong>}
                      checked={selectAllAffymetrix}
                      onChange={(e) => {
                        const checked = e.target.checked;
                        setSelectAllAffymetrix(checked);
                        setAffymetrixChips(checked ? availableAffymetrix : []);
                      }}
                    />
                    <CheckboxList
                      options={availableAffymetrix}
                      selected={affymetrixChips}
                      setSelected={setAffymetrixChips}
                      type="affymetrix"
                    />
                  </Col>
                </Row>
              </>
            )}
          </Accordion.Body>
        </Accordion.Item>
      </Accordion>
      {loading && <CalculateLoading />}
      <hr />
      {/* Results, warnings, and errors display */}
      {error && (
        <Alert className="mt-3" role="alert" variant="danger">
          {error}
        </Alert>
      )}
      {warning && (
        <Row className="justify-content-center my-3">
          <Col sm={8} md={7}>
            <Card border="warning" className="w-100">
              <Card.Header className="bg-warning">Warning</Card.Header>
              <Card.Body className="py-2 snpchip-card-body">
                <Card.Text style={{ marginBottom: 0 }}>{warning}</Card.Text>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}
    </Form>
  );
}
