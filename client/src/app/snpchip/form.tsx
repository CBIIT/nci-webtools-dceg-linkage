"use client";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { Row, Col, Form, Button, Accordion, Spinner } from "react-bootstrap";
import { useRouter, usePathname } from "next/navigation";
import { snpchipPlatforms } from "@/services/queries";
import CalculateLoading from "@/components/calculateLoading";
import { useStore } from "@/store";
import { FormData } from "./types";
import { parseSnps } from "@/services/utils";

interface Platform {
  id: string;
  name: string;
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

interface SNPChipFormProps {
  input: string;
  setInput: (val: string) => void;
  file: File | null;
  setFile: (val: File | null) => void;
  illuminaChips: Platform[];
  setIlluminaChips: (chips: Platform[]) => void;
  affymetrixChips: Platform[];
  setAffymetrixChips: (chips: Platform[]) => void;
  loading: boolean;
  handleSubmit: (e: React.FormEvent) => Promise<void>;
}

export default function SNPChipForm({
  input,
  setInput,
  file,
  setFile,
  illuminaChips,
  setIlluminaChips,
  affymetrixChips,
  setAffymetrixChips,
  loading,
  handleSubmit,
}: SNPChipFormProps) {
  console.log("SNPChipForm mounted");
  const router = useRouter();
  const pathname = usePathname();
  const { genome_build } = useStore((state: { genome_build: string }) => state);

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

  useEffect(() => {
    async function fetchPlatforms() {
      try {
        setPlatformsLoading(true);
        console.log("Fetching platforms...");
        const data = await snpchipPlatforms();
        console.log("Fetched data: ", data);
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
        console.log("Finished fetchPlatforms");
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
  }, [varFile, setValue]);

  return (
    <Form id="snpchip-form" onSubmit={handleSubmit} noValidate>
      <Row className="mb-3 align-items-start">
        <Col md={4}>
          <Form.Group controlId="snps">
            <Form.Label>RS Numbers or Genomic Coordinates</Form.Label>
            <Form.Control
              as="textarea"
              rows={5}
              placeholder="RS Numbers or Genomic Coordinates"
              value={input}
              onChange={e => setInput(e.target.value)}
              title="Enter list of RS numbers or Genomic Coordinates (one per line)"
            />
          </Form.Group>
        </Col>
        <Col md={5}>
          <Form.Group controlId="varFile">
            <Form.Label>Upload file with variants</Form.Label>
            <Form.Control
              type="file"
              onChange={e => {
                const target = e.target as HTMLInputElement;
                setFile(target.files ? target.files[0] : null);
              }}
            />
          </Form.Group>
        </Col>
        <Col md={3} className="d-flex justify-content-end">
          <Button type="reset" variant="outline-danger" className="me-1">
            Reset
          </Button>
          <Button type="submit" variant="primary" disabled={loading}>
            {loading ? <Spinner animation="border" size="sm" /> : "Calculate"}
          </Button>
        </Col>
      </Row>
      <Accordion className="mb-4">
        <Accordion.Item eventKey="0">
          <Accordion.Header>
            <div className="d-flex justify-content-between w-100 align-items-center snpchip-accordion">
              <span>Filter by array</span>
              {!platformsLoading && (
                <small className="text-muted me-2">
                  {illuminaChips?.length || 0} Illumina array(s), and {affymetrixChips?.length || 0} Affymetrix array(s) selected
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
                {illuminaChips.length === availableIllumina.length && affymetrixChips.length === availableAffymetrix.length ? (
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
    </Form>
  );
}
