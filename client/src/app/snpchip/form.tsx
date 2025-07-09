"use client";
import { Form, Button, Accordion, Row, Col, Spinner } from "react-bootstrap";
import { useState, useEffect } from "react";

interface SnpChipFormProps {
  handleSubmit: (e: React.FormEvent) => void;
  loading: boolean;
  input: string;
  setInput: (value: string) => void;
  file: File | null;
  setFile: (file: File | null) => void;
  selectAllIllumina: boolean;
  setSelectAllIllumina: (value: boolean) => void;
  selectAllAffymetrix: boolean;
  setSelectAllAffymetrix: (value: boolean) => void;
}

const availableIllumina = [
  "Illumina Cardio-MetaboChip",
  "Illumina Human1M-Duov3",
  "Illumina Human1Mv1",
  "Illumina HumanExon510Sv1",
  "Illumina HumanOmni1S-8v1",
  "Illumina HumanOmni2.5-4v1",
  "Illumina HumanOmni2.5-8v1.2",
  "Illumina HumanOmni2.5Exome-8v1",
  "Illumina HumanOmni2.5Exome-8v1.1",
  "Illumina HumanOmni2.5Exome-8v1.2",
  "Illumina HumanOmni5-4v1",
  "Illumina HumanOmni5Exome-4v1",
  "Illumina Infinium Multi-Ethnic Global-8",
];
const availableAffymetrix = [
  "Affymetrix Axiom GW AFR",
  "Affymetrix Axiom GW ASI",
  "Affymetrix Axiom GW EAS",
  "Affymetrix Axiom GW EUR",
  "Affymetrix Axiom GW Hu",
  "Affymetrix Axiom GW Hu-CHB",
  "Affymetrix Axiom GW LAT",
  "Affymetrix OncoScan",
  "Affymetrix OncoScan CNV",
  "Affymetrix SNP 6.0",
];

function CheckboxList({
  options,
  selected,
  setSelected,
  type,
}: {
  options: string[];
  selected: string[];
  setSelected: (val: string[]) => void;
  type: "illumina" | "affymetrix";
}) {
  const toggle = (option: string) => {
    if (selected.includes(option)) {
      setSelected(selected.filter((item) => item !== option));
    } else {
      setSelected([...selected, option]);
    }
  };

  return (
    <>
      {options.map((option) => (
        <Form.Check
          key={option}
          id={`${type}-${option}`}
          type="checkbox"
          className={type}
          label={option}
          checked={selected.includes(option)}
          onChange={() => toggle(option)}
        />
      ))}
    </>
  );
}

export default function SnpChipForm({
  handleSubmit,
  loading,
  input,
  setInput,
  file,
  setFile,
  selectAllIllumina,
  setSelectAllIllumina,
  selectAllAffymetrix,
  setSelectAllAffymetrix,
}: SnpChipFormProps) {
  const [illuminaChips, setIlluminaChips] = useState<string[]>(availableIllumina);
  const [affymetrixChips, setAffymetrixChips] = useState<string[]>(availableAffymetrix);

  useEffect(() => {
    setSelectAllIllumina(illuminaChips.length === availableIllumina.length);
    setSelectAllAffymetrix(affymetrixChips.length === availableAffymetrix.length);
  }, [illuminaChips, affymetrixChips]);

  return (
    <>
      <Form onSubmit={handleSubmit} className="mb-4">
        <Row className="mb-3">
          <Col md={4}>
            <Form.Group controlId="snpchip-file-snp-numbers">
              <Form.Label>RS Numbers or Genomic Coordinates</Form.Label>
              <Form.Control
                as="textarea"
                rows={5}
                placeholder="RS Numbers or Genomic Coordinates"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                required={!file}
              />
            </Form.Group>
          </Col>
          <Col md={5}>
            <Form.Group controlId="snpchip-file">
              <Form.Label>Upload file with variants</Form.Label>
              <Form.Control
                type="file"
                onChange={(e) => {
                  const target = e.target as HTMLInputElement;
                  const selectedFile = target.files?.[0] || null;
                  setFile(selectedFile);
                  if (selectedFile) setInput("");
                }}
              />
            </Form.Group>
          </Col>
          <Col md={3} className="d-flex align-items-end">
            <Button type="submit" variant="primary" disabled={loading}>
              {loading ? <Spinner animation="border" size="sm" /> : "Calculate"}
            </Button>
          </Col>
        </Row>
      </Form>

      <Accordion className="mb-4">
        <Accordion.Item eventKey="0">
          <Accordion.Header>Filter by array</Accordion.Header>
          <Accordion.Body>
            <p>
              {illuminaChips.length} Illumina array(s) and {affymetrixChips.length} Affymetrix array(s) selected (<span
                style={{ textDecoration: "underline", cursor: "pointer", color: "blue" }}
                onClick={() => {
                  const allSelected =
                    illuminaChips.length === availableIllumina.length &&
                    affymetrixChips.length === availableAffymetrix.length;
                  if (allSelected) {
                    setIlluminaChips([]);
                    setAffymetrixChips([]);
                    setSelectAllIllumina(false);
                    setSelectAllAffymetrix(false);
                  } else {
                    setIlluminaChips(availableIllumina);
                    setAffymetrixChips(availableAffymetrix);
                    setSelectAllIllumina(true);
                    setSelectAllAffymetrix(true);
                  }
                }}
              >
                unselect all
              </span>)
            </p>

            <Row>
              <Col md={6}>
                <Form.Check
                  type="checkbox"
                  id="selectAllIllumina"
                  label="Select All Illumina"
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
              <Col md={6}>
                <Form.Check
                  type="checkbox"
                  id="selectAllAffymetrix"
                  label="Select All Affymetrix"
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
          </Accordion.Body>
        </Accordion.Item>
      </Accordion>
    </>
  );
}
