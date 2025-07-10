"use client";
import { Form, Button, Accordion, Row, Col, Spinner } from "react-bootstrap";
import { useState, useEffect } from "react";
import { snpchipPlatforms } from "../../services/queries";

export interface Platform {
  id: string;
  name: string;
}

interface SnpChipFormProps {
  handleSubmit: (e: React.FormEvent) => void;
  loading: boolean;
  input: string;
  setInput: (value: string) => void;
  file: File | null;
  setFile: (file: File | null) => void;
  illuminaChips: Platform[];
  setIlluminaChips: (chips: Platform[]) => void;
  affymetrixChips: Platform[];
  setAffymetrixChips: (chips: Platform[]) => void;
}

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

export default function SnpChipForm({
  handleSubmit,
  loading,
  input,
  setInput,
  file,
  setFile,
  illuminaChips,
  setIlluminaChips,
  affymetrixChips,
  setAffymetrixChips,
}: SnpChipFormProps) {
  const [availableIllumina, setAvailableIllumina] = useState<Platform[]>([]);
  const [availableAffymetrix, setAvailableAffymetrix] = useState<Platform[]>(
    [],
  );
  const [platformsLoading, setPlatformsLoading] = useState(true);
  const [selectAllIllumina, setSelectAllIllumina] = useState(true);
  const [selectAllAffymetrix, setSelectAllAffymetrix] = useState(true);

  useEffect(() => {
    async function fetchPlatforms() {
      try {
        setPlatformsLoading(true);
        const data = await snpchipPlatforms();
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
      } catch (error) {
        console.error("Failed to fetch SNPchip platforms", error);
      } finally {
        setPlatformsLoading(false);
      }
    }
    fetchPlatforms();
  }, [setIlluminaChips, setAffymetrixChips]);

  useEffect(() => {
    setSelectAllIllumina(
      availableIllumina.length > 0 &&
        illuminaChips.length === availableIllumina.length,
    );
    setSelectAllAffymetrix(
      availableAffymetrix.length > 0 &&
        affymetrixChips.length === availableAffymetrix.length,
    );
  }, [illuminaChips, affymetrixChips, availableIllumina, availableAffymetrix]);

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
            {platformsLoading ? (
              <div className="text-center">
                <Spinner animation="border" size="sm" /> Loading platforms...
              </div>
            ) : (
              <>
                <p>
                  {illuminaChips?.length || 0} Illumina array(s) and{" "}
                  {affymetrixChips?.length || 0} Affymetrix array(s) selected
                </p>
                <Button
                  variant="link"
                  className="p-0 mb-3"
                  onClick={() => {
                    const allSelected =
                      illuminaChips.length === availableIllumina.length &&
                      affymetrixChips.length === availableAffymetrix.length;
                    if (allSelected) {
                      setIlluminaChips([]);
                      setAffymetrixChips([]);
                    } else {
                      setIlluminaChips(availableIllumina);
                      setAffymetrixChips(availableAffymetrix);
                    }
                  }}
                >
                  {illuminaChips.length === availableIllumina.length &&
                  affymetrixChips.length === availableAffymetrix.length
                    ? "Deselect All"
                    : "Select All"}
                </Button>
                <Row>
                  <Col>
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
                  <Col>
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
              </>
            )}
          </Accordion.Body>
        </Accordion.Item>
      </Accordion>
    </>
  );
}
