"use client";
import { Form, Button, Accordion, Row, Col, Spinner } from "react-bootstrap";

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
            <Row>
              <Col md={6}>
                <Form.Check
                  type="checkbox"
                  id="selectAllIllumina"
                  label="Select All Illumina"
                  checked={selectAllIllumina}
                  onChange={e => setSelectAllIllumina(e.target.checked)}
                />
              </Col>
              <Col md={6}>
                <Form.Check
                  type="checkbox"
                  id="selectAllAffymetrix"
                  label="Select All Affymetrix"
                  checked={selectAllAffymetrix}
                  onChange={e => setSelectAllAffymetrix(e.target.checked)}
                />
              </Col>
            </Row>
            <p className="mt-2">
              Limit search results to only SNPs on the selected arrays (unselect all)
            </p>
          </Accordion.Body>
        </Accordion.Item>
      </Accordion>
    </>
  );
} 