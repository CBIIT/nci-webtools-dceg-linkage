"use client";
import { useForm } from "react-hook-form";
import { Row, Col, Form, Button, ButtonGroup, ToggleButton, Alert, Nav, Tab } from "react-bootstrap";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter, usePathname } from "next/navigation";
import { ldscore, fetchHeritabilityResult, fetchGeneticCorrelationResult, fetchLdScoreCalculationResult } from "@/services/queries";
import LdscorePopSelect, { LdscorePopOption } from "@/components/select/ldscore-pop-select";
import CalculateLoading from "@/components/calculateLoading";
import { useStore } from "@/store";
import { useState } from "react";
import LdScoreResults from "./results";
import "./style.css";

export interface FormData {
  file?: File;
  file2?: File; // Second file for genetic correlation
  analysis_type: "heritability" | "genetic_correlation" | "ld_calculation";
  pop: LdscorePopOption;
  window: number;
  windowUnit: "kb" | "cM";
}

export default function LdScoreForm() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const pathname = usePathname();
  const { genome_build } = useStore((state) => state);
  const [exampleFilename, setExampleFilename] = useState<string>("");
  const [exampleFilepath, setExampleFilepath] = useState<string>("");
  const [heritabilityResult, setHeritabilityResult] = useState<string>("");
  const [heritabilityLoading, setHeritabilityLoading] = useState(false);
  const [heritPanelOpen, setHeritPanelOpen] = useState(false);
  const [uploadedFilename, setUploadedFilename] = useState<string>("");
  const [uploading, setUploading] = useState(false);
  const [exampleFile1, setExampleFile1] = useState<string>("");
  const [exampleFile2, setExampleFile2] = useState<string>("");
  const [uploadedFile1, setUploadedFile1] = useState<string>("");
  const [uploadedFile2, setUploadedFile2] = useState<string>("");

  // Add state for LD calculation example and uploaded files
  const [exampleBed, setExampleBed] = useState<string>("");
  const [exampleBim, setExampleBim] = useState<string>("");
  const [exampleFam, setExampleFam] = useState<string>("");
  const [uploadedBed, setUploadedBed] = useState<string>("");
  const [uploadedBim, setUploadedBim] = useState<string>("");
  const [uploadedFam, setUploadedFam] = useState<string>("");

  const handleFileUpload = async (file: File) => {
    setUploading(true);
    const formData = new FormData();
    formData.append("ldscoreFile", file);
   
    try {
      const response = await fetch("/LDlinkRestWeb/upload", {
        method: "POST",
        body: formData,
      });
      if (response.ok) {
        setUploadedFilename(file.name);
      } else {
        setUploadedFilename("");
      }
    } catch (e) {
      setUploadedFilename("");
    } finally {
      setUploading(false);
    }
  };

  // Update file upload handlers for genetic correlation
  const handleGeneticFileUpload = async (file: File, fileNum: 1 | 2) => {
    setUploading(true);
    const formData = new FormData();
    formData.append("ldscoreFile", file);
    try {
      const response = await fetch("/LDlinkRestWeb/upload", {
        method: "POST",
        body: formData,
      });
      if (response.ok) {
        if (fileNum === 1) setUploadedFile1(file.name);
        else setUploadedFile2(file.name);
      } else {
        if (fileNum === 1) setUploadedFile1("");
        else setUploadedFile2("");
      }
    } catch (e) {
      if (fileNum === 1) setUploadedFile1("");
      else setUploadedFile2("");
    } finally {
      setUploading(false);
    }
  };

  // Upload handler for LD calculation multiple files (.bed, .bim, .fam)
  const handleLdFilesUpload = async (files: FileList) => {
    setUploading(true);
    setUploadedBed(""); setUploadedBim(""); setUploadedFam("");
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const ext = file.name.split('.').pop()?.toLowerCase();
      const formData = new FormData();
      formData.append("ldscoreFile", file);
      try {
        const response = await fetch("/LDlinkRestWeb/upload", {
          method: "POST",
          body: formData,
        });
        if (response.ok) {
          if (ext === 'bed') setUploadedBed(file.name);
          if (ext === 'bim') setUploadedBim(file.name);
          if (ext === 'fam') setUploadedFam(file.name);
        }
      } catch (e) {
        // ignore
      }
    }
    setUploading(false);
  };

  // Heritability form state
  const heritabilityForm = useForm<FormData>({
    defaultValues: {
      analysis_type: "heritability",
      pop: undefined,
      window: 0,
      windowUnit: "cM"
    }
  });
  const heritabilityMutation = useMutation({
    mutationFn: ldscore,
    onSuccess: (data: any) => {
      if (data?.error) {
        console.error("LDscore calculation failed:", data.error);
        return;
      }
      queryClient.setQueryData(["ldscore", data.id], data);
      router.push(`${pathname}?ref=${data.id}`);
    },
    onError: (error) => {
      console.error("LDscore mutation error:", error);
    },
  });
  // Remove all result parsing, rendering, and download helpers from here.
  // Only keep form logic, file upload, and state management.

  // Add state to track the reference and type for result display
  const [resultRef, setResultRef] = useState<string | null>(null);
  const [resultType, setResultType] = useState<"heritability" | "genetic_correlation" | "ldscore" | null>(null);

  // Add a mapping so form uses the correct type for LdScoreResults
  // 'heritability' -> 'heritability', 'genetic_correlation' -> 'correlation', 'ldscore' -> 'ldscore'
  const resultTypeMap = {
    heritability: 'heritability',
    genetic_correlation: 'correlation',
    ldscore: 'ldscore',
  } as const;

  // Update submit handlers to set resultRef and resultType
  const onHeritabilitySubmit = async (data: FormData) => {
    setHeritabilityLoading(true);
    const pop =  data.pop.value ;
    const genomeBuild = genome_build || "grch37";
    const reference = Math.floor(Math.random() * (99999 - 10000 + 1)).toString();
    const isExample = !!exampleFilename;
    const filename = exampleFilename || uploadedFilename;
    const params = new URLSearchParams({
      filename,
      pop,
      genome_build: genomeBuild,
      isExample: isExample ? "true" : "false",
      reference,
    });
    try {
      await fetchHeritabilityResult(params); // still trigger backend
      setResultRef(reference);
      setResultType("heritability");
    } catch (error) {
      // handle error UI if needed
    } finally {
      setHeritabilityLoading(false);
    }
  };

  // Removed duplicate onGeneticSubmit definition to resolve redeclaration error.


  // Genetic correlation form state
  const geneticForm = useForm<FormData>({
    defaultValues: {
      analysis_type: "genetic_correlation",
      pop: undefined,
      window: 0,
      windowUnit: "cM"
    }
  });
  const geneticMutation = useMutation({
    mutationFn: ldscore,
    onSuccess: (data: any) => {
      if (data?.error) {
        console.error("LDscore calculation failed:", data.error);
        return;
      }
      queryClient.setQueryData(["ldscore", data.id], data);
      router.push(`${pathname}?ref=${data.id}`);
    },
    onError: (error) => {
      console.error("LDscore mutation error:", error);
    },
  });
  const [geneticLoading, setGeneticLoading] = useState(false);
  const [geneticResult, setGeneticResult] = useState("");
  const onGeneticSubmit = async (data: FormData) => {
    setGeneticResult("");
    setGeneticLoading(true);
    const pop = data.pop.value;
    const genomeBuild = genome_build || "grch37";
    const reference = Math.floor(Math.random() * (99999 - 10000 + 1)).toString();
    const isExample = !!exampleFile1;
    const filename = exampleFile1 || uploadedFile1;
    const filename2 = exampleFile2 || uploadedFile2;
    const params = new URLSearchParams({
      filename,
      filename2,
      pop,
      genome_build: genomeBuild,
      isExample: isExample ? "true" : "false",
      reference,
    });
    try {
      const result = await fetchGeneticCorrelationResult(params);
      setGeneticResult(result.result || JSON.stringify(result));
    } catch (error) {
      setGeneticResult("Error fetching genetic correlation result.");
    } finally {
      setGeneticLoading(false);
    }
  };
  const onGeneticReset = () => {
    geneticForm.reset();
  };

  // LD calculation form state
  const ldForm = useForm<FormData>({
    defaultValues: {
      analysis_type: "ld_calculation",
      pop: undefined,
      window: 0,
      windowUnit: "cM"
    }
  });
  const ldMutation = useMutation({
    mutationFn: ldscore,
    onSuccess: (data: any) => {
      if (data?.error) {
        console.error("LDscore calculation failed:", data.error);
        return;
      }
      queryClient.setQueryData(["ldscore", data.id], data);
      router.push(`${pathname}?ref=${data.id}`);
    },
    onError: (error) => {
      console.error("LDscore mutation error:", error);
    },
  });
  const [ldResult, setLdResult] = useState<string>("");

  const onLdSubmit = async () => {
    const bed = exampleBed || uploadedBed;
    const bim = exampleBim || uploadedBim;
    const fam = exampleFam || uploadedFam;
    const window = ldForm.getValues("window");
    const windowUnit = ldForm.getValues("windowUnit");
    if (!bed || !bim || !fam) {
      alert("Please provide all three files: .bed, .bim, .fam");
      return;
    }
    const isExample = !!exampleBed;
    const filename = `${bed};${bim};${fam}`;
    const reference = Math.floor(Math.random() * (99999 - 10000 + 1)).toString();
    const params = new URLSearchParams({
      filename,
      window: String(window),
      windowUnit,
      isExample: isExample ? "true" : "false",
      reference,
    });
    try {
      setUploading(true);
      await fetchLdScoreCalculationResult(params);
      setResultRef(reference);
      setResultType("ldscore");
    } catch (error) {
      // handle error UI if needed
    } finally {
      setUploading(false);
    }
  };
  const onLdReset = () => {
    ldForm.reset();
  };

  const analysisType = heritabilityForm.watch("analysis_type");

  if (heritabilityMutation.isPending || geneticMutation.isPending || ldMutation.isPending) {
    return <CalculateLoading />;
  }

  return (
    <Tab.Container activeKey={analysisType} onSelect={(key) => heritabilityForm.setValue("analysis_type", key as any)}>
      <Row>
        <Col sm={12}>
          <Nav variant="tabs" className="mb-3">
            <Nav.Item>
              <Nav.Link eventKey="heritability">Heritability Analysis</Nav.Link>
            </Nav.Item>
            <Nav.Item>
              <Nav.Link eventKey="genetic_correlation">Genetic Correlation</Nav.Link>
            </Nav.Item>
            <Nav.Item>
              <Nav.Link eventKey="ld_calculation">LD Score Calculation</Nav.Link>
            </Nav.Item>
          </Nav>
        </Col>
      </Row>

      <Tab.Content>
        <Tab.Pane eventKey="heritability">
          <Form id="ldscore-form-heritability" onSubmit={heritabilityForm.handleSubmit(onHeritabilitySubmit)} onReset={() => heritabilityForm.reset()} noValidate>
            <Row>
              <Col sm={4}>
                <Form.Group controlId="file" className="mb-3">
                  <Form.Label>Upload pre-munged GWAS sumstats file</Form.Label>
                  {typeof exampleFilename === "string" && exampleFilename !== "" ? (
              <div className="form-control bg-light">{exampleFilename}</div>
            ) : (
                    <Form.Control 
                      type="file" 
                      {...heritabilityForm.register("file", { required: "File is required" })}
                      accept=".txt,.tsv,.csv"
                      title="Upload pre-munged GWAS sumstats"
                      onChange={async (e) => {
                        //e.target.value = "";
                        const input = e.target as HTMLInputElement;
                        const file = input.files && input.files[0];
                        setHeritabilityResult("")
                        if (file) {
                          setUploading(true);
                          await handleFileUpload(file);
                          setUploading(false);
                          setUploadedFilename(file.name);
                          heritabilityForm.clearErrors("file");
                        }
                      }}
                    />
                  )}
                  <div className="mt-2">
                    <a href="/help#LDscore" className="text-decoration-none" target="_blank" rel="noopener noreferrer">
                      Click here for sample format
                    </a>
                  </div>
             <Form.Text className="text-danger">{heritabilityForm.formState.errors?.file?.message}</Form.Text>
             </Form.Group>
             <Form.Group controlId="useEx" className="mb-3">
                  <div className="mt-2">
                    <Form.Check 
                      type="switch"
                      id="use-example-heritability"
                      label="Use Example Data"
                      onChange={async (e) => {
                        if (e.target.checked) {
                          heritabilityForm.setValue("analysis_type", "heritability");
                          setUploadedFilename("")
                          setHeritabilityResult("")
                          heritabilityForm.clearErrors("file");
                          try {
                            const response = await fetch("/LDlinkRestWeb/ldherit_example");
                            if (response.ok) {
                              const data = await response.json();
                              setExampleFilename(data.filenames || "");
                              setExampleFilepath(data.filepaths || "");
                            } else {
                              setExampleFilename("");
                              setExampleFilepath("");
                              console.error("Failed to fetch example data");
                            }
                          } catch (error) {
                            setExampleFilename("");
                            setExampleFilepath("");
                            console.error("Error fetching example data:", error);
                          }
                        } else {
                          setExampleFilename("");
                          setExampleFilepath("");
                          heritabilityForm.setValue("pop", { label: "", value: "" });
                        }
                      }}
                    />
                  {(exampleFilename || uploadedFilename) && (
                    <div className="mt-1" style={{ fontSize: "0.95em" }}>
                      <span style={{ fontWeight: 600 }}>Input files uploaded:</span><br />
                     <a
                        href={exampleFilename
                          ? `/LDlinkRestWeb/copy_and_download/${encodeURIComponent(exampleFilename)}`
                          : `/LDlinkRestWeb/tmp/uploads/${encodeURIComponent(uploadedFilename)}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        download
                        style={{ textDecoration: 'none', color: 'inherit' }}
                      >
                        {exampleFilename || uploadedFilename}
                      </a>
                    </div>
                  )}
                  </div>
               
                </Form.Group>
              </Col>

              <Col sm={4}>
                <Form.Group controlId="pop" className="mb-3">
                  <Form.Label>Population</Form.Label>
                  <LdscorePopSelect name="pop" control={heritabilityForm.control} rules={{ required: "Population is required" }} />
                  <Form.Text className="text-danger">{heritabilityForm.formState.errors?.pop?.message}</Form.Text>
                </Form.Group>
              </Col>

              <Col />
              <Col sm={2}>
                <div className="text-end">
                  <Button type="reset" variant="outline-danger" className="me-1">
                    Reset
                  </Button>
                  <Button type="submit" variant="primary" disabled={heritabilityMutation.isPending}>
                    Calculate
                  </Button>
                </div>
              </Col>
            </Row>
          </Form>
          {heritabilityLoading && (
            <div className="d-flex flex-column align-items-center my-3">
              <span
                className="px-3 py-2 mb-2"
                style={{
                  background: '#e3f0ff',
                  color: '#084298',
                  borderRadius: '6px',
                  fontWeight: 500,
                  textAlign: 'center',
                  maxWidth: 800,
                }}
              >
                Computational time may vary based on the number of samples and genetic markers provided in the data
              </span>
              <div>
                <CalculateLoading />
              </div>
            </div>
          )}
          {uploading && (
            <div style={{ position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh', background: 'rgba(255,255,255,0.7)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <div className="d-flex flex-column align-items-center">
                <span
                  className="px-3 py-2 mb-2"
                  style={{
                    background: '#e3f0ff',
                    color: '#084298',
                    borderRadius: '6px',
                    fontWeight: 500,
                    textAlign: 'center',
                    maxWidth: 800,
                  }}
                >
                  Uploading file, please wait...
                </span>
                <CalculateLoading />
              </div>
            </div>
          )}
          {/* Only show results via LdScoreResults for heritability tab */}
          {resultRef && resultType === 'heritability' && (
            <LdScoreResults reference={resultRef} type="heritability" />
          )}
        </Tab.Pane>

        <Tab.Pane eventKey="genetic_correlation">
          <Form id="ldscore-form-genetic-correlation" onSubmit={geneticForm.handleSubmit(onGeneticSubmit)} onReset={onGeneticReset} noValidate>
            <Row>
              <Col sm={3}>
                <Form.Group controlId="file" className="mb-3">
                  <Form.Label>Upload pre-munged GWAS sumstats file</Form.Label>
                  {typeof exampleFile1 === "string" && exampleFile1 !== "" ? (
                    <div className="form-control bg-light">{exampleFile1}</div>
                  ) : (
                    <Form.Control 
                      type="file" 
                      {...geneticForm.register("file", { required: "Trait 1 file is required" })}
                      accept=".txt,.tsv,.csv"
                      title="Upload pre-munged GWAS sumstats"
                      onChange={async (e) => {
                        const input = e.target as HTMLInputElement;
                        const file = input.files && input.files[0];
                        if (file) {
                          await handleFileUpload(file);
                          setUploadedFile1(file.name);
                          geneticForm.clearErrors("file");
                        }
                      }}
                    />
                  )}
                  <Form.Text className="text-danger">{geneticForm.formState.errors?.file?.message}</Form.Text>
                </Form.Group>
                <Form.Group controlId="file2" className="mb-3">
                  <Form.Label>Upload pre-munged GWAS sumstats file</Form.Label>
                  {typeof exampleFile2 === "string" && exampleFile2 !== "" ? (
                    <div className="form-control bg-light">{exampleFile2}</div>
                  ) : (
                    <Form.Control 
                      type="file" 
                      {...geneticForm.register("file2", { required: "Trait 2 file is required" })}
                      accept=".txt,.tsv,.csv"
                      title="Upload pre-munged GWAS sumstats"
                      onChange={async (e) => {
                        const input = e.target as HTMLInputElement;
                        const file = input.files && input.files[0];
                        if (file) {
   
                          await handleFileUpload(file);
                          setUploadedFile2(file.name);
                          geneticForm.clearErrors("file2");
                        }
                      }}
                    />
                  )}
                  <div className="mt-2">
                    <a href="/help#LDscore" className="text-decoration-none" target="_blank" rel="noopener noreferrer">
                      Click here for sample format
                    </a>
                  </div>
                  <Form.Text className="text-danger">{geneticForm.formState.errors?.file2?.message}</Form.Text>
                </Form.Group>
              
              </Col>
              <Col sm={1}></Col>
              <Col sm={3}>
                <Form.Group controlId="pop" className="mb-3">
                  <Form.Label>Population</Form.Label>
                  <LdscorePopSelect name="pop" control={geneticForm.control} rules={{ required: "Population is required" }} />
                  <Form.Text className="text-danger">{geneticForm.formState.errors?.pop?.message}</Form.Text>
                </Form.Group>
              </Col>
              <Col />
              <Col sm={3}>
                <div className="text-end">
                  <Button type="reset" variant="outline-danger" className="me-1">
                    Reset
                  </Button>
                  <Button type="submit" variant="primary" disabled={geneticMutation.isPending}>
                    Calculate
                  </Button>
                </div>
              </Col>
            </Row>
            <Row>
              <Col sm={12}>
                <div className="mb-3">
                  <Form.Check 
                    type="switch"
                    id="use-example-correlation"
                    label="Use Example Data"
                    onChange={(e) => {
                      if (e.target.checked) {
                        setExampleFile1("BBJ_HDLC22.txt");
                        setExampleFile2("BBJ_LDLC22.txt");
                        setUploadedFile1("");
                        setUploadedFile2("");
                        geneticForm.setValue("analysis_type", "genetic_correlation");
                      } else {
                        setExampleFile1("");
                        setExampleFile2("");
                        geneticForm.setValue("pop", { label: "", value: "" });
                      }
                    }}
                  />
                   {(exampleFile1 || uploadedFile1) && (exampleFile2 || uploadedFile2) && (
                    <>
                      <span style={{ fontWeight: 600 }}>Input files uploaded:</span><br />
                      <a
                        href={exampleFile1 ? `/LDlinkRestWeb/copy_and_download/${encodeURIComponent(exampleFile1)}` : `/LDlinkRestWeb/tmp/uploads/${encodeURIComponent(uploadedFile1)}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        download
                        style={{ textDecoration: 'none', color: 'inherit' }}
                      >
                        {exampleFile1 || uploadedFile1}
                      </a>
                     <br></br>
                      <a
                        href={exampleFile2 ? `/LDlinkRestWeb/copy_and_download/${encodeURIComponent(exampleFile2)}` : `/LDlinkRestWeb/tmp/uploads/${encodeURIComponent(uploadedFile2)}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        download
                        style={{ textDecoration: 'none', color: 'inherit' }}
                      >
                        {exampleFile2 || uploadedFile2}
                      </a>
                    </>
                  )}
                </div>
              </Col>
            </Row>
            
            {geneticMutation.isError && (
              <Row>
                <Col>
                  <Alert variant="danger" className="mt-3">
                    <Alert.Heading>Error</Alert.Heading>
                    <p>Failed to process Genetic Correlation calculation. Please check your input and try again.</p>
                  </Alert>
                </Col>
              </Row>
            )}
          </Form>
        {geneticLoading && (
            <div className="d-flex flex-column align-items-center my-3">
              <span
                className="px-3 py-2 mb-2"
                style={{
                  background: '#e3f0ff',
                  color: '#084298',
                  borderRadius: '6px',
                  fontWeight: 500,
                  textAlign: 'center',
                  maxWidth: 800,
                }}
              >
                Computational time may vary based on the number of samples and genetic markers provided in the data
              </span>
              <div>
                <CalculateLoading />
              </div>
            </div>
          )}
        {geneticResult }
        </Tab.Pane>

        <Tab.Pane eventKey="ld_calculation">
          <Form id="ldscore-form-ld-calculation" onSubmit={ldForm.handleSubmit(onLdSubmit)} onReset={onLdReset} noValidate>
            <Row>
              <Col sm={4}>
                <Form.Group controlId="ldfiles" className="mb-3">
                  <Form.Label>Upload .bed, .bim, .fam files (all three required)</Form.Label>
                  {(exampleBed || exampleBim || exampleFam) ? (
                    <div className="form-control bg-light">
                      {exampleBed && <div>{exampleBed}</div>}
                      {exampleBim && <div>{exampleBim}</div>}
                      {exampleFam && <div>{exampleFam}</div>}
                    </div>
                  ) : (
                    <Form.Control
                      type="file"
                      accept=".bed,.bim,.fam"
                      multiple
                      title="Upload .bed, .bim, .fam files"
                      onChange={async (e) => {
                        const input = e.target as HTMLInputElement;
                        if (input.files) {
                          handleLdFilesUpload(input.files);
                        }
                      }}
                    />
                  )}
                </Form.Group>
                <Form.Group controlId="useExLd" className="mb-3">
                  <div className="mt-2">
                    <Form.Check
                      type="switch"
                      id="use-example-ld"
                      label="Use Example Data"
                      onChange={async (e) => {
                        if (e.target.checked) {
                          setExampleBed("22.bed");
                          setExampleBim("22.bim");
                          setExampleFam("22.fam");
                          setUploadedBed("");
                          setUploadedBim("");
                          setUploadedFam("");
                        } else {
                          setExampleBed("");
                          setExampleBim("");
                          setExampleFam("");
                        }
                      }}
                    />
                    {(uploadedBed || uploadedBim || uploadedFam || exampleBed || exampleBim || exampleFam) && (
                      <div className="mt-1" style={{ fontSize: "0.95em" }}>
                        <span style={{ fontWeight: 600 }}>Input files:</span><br />
                        <div>{exampleBed || uploadedBed}</div>
                        <div>{exampleBim || uploadedBim}</div>
                        <div>{exampleFam || uploadedFam}</div>
                      </div>
                    )}
                  </div>
                </Form.Group>
              </Col>
              <Col sm={3}>
                {/* Keep window option as before */}
                <Form.Group controlId="window" className="mb-3">
                  <Form.Label>Window</Form.Label>
                  <div className="d-flex">
                    <Form.Control
                      type="number"
                      {...ldForm.register("window", { required: "Window is required",  min: { value: 1, message: "Window must be greater than 0" } })}
                      style={{ maxWidth: "120px", marginRight: "8px" }}
                      title="Please enter an integer greater than 0"
                    />
                    <Form.Select
                      {...ldForm.register("windowUnit")}
                      style={{ maxWidth: "80px" }}
                      defaultValue="cM"
                      title="Select unit for the window size"
                    >
                      <option value="kb">kb</option>
                      <option value="cM">cM</option>
                    </Form.Select>
                  </div>
                  <Form.Text className="text-danger">{ldForm.formState.errors?.window?.message}</Form.Text>
                </Form.Group>
              </Col>
              <Col />
              <Col sm={2}>
                <div className="text-end">
                  <Button type="reset" variant="outline-danger" className="me-1">
                    Reset
                  </Button>
                  <Button type="submit" variant="primary" disabled={ldMutation.isPending}>
                    Calculate
                  </Button>
                </div>
              </Col>
            </Row>
          </Form>

          {ldResult && (
            <div className="mt-3" style={{ maxWidth: 600, margin: '0 auto', background: '#f9f9f9', border: '1px solid #bdbdbd', borderRadius: 6, padding: 16 }}>
              <div style={{ fontWeight: 600, marginBottom: 8, color: '#084298' }}>LD Score Calculation Result</div>
              <pre style={{ whiteSpace: 'pre-wrap', fontSize: '0.97em', margin: 0 }}>{ldResult}</pre>
            </div>
          )}

          {ldMutation.isError && (
            <Row>
              <Col>
                <Alert variant="danger" className="mt-3">
                  <Alert.Heading>Error</Alert.Heading>
                  <p>Failed to process LD Score calculation. Please check your input and try again.</p>
                </Alert>
              </Col>
            </Row>
          )}
        </Tab.Pane>
      </Tab.Content>

      {/* Show results component if reference and type are available */}
      {resultRef && resultType && (
        <LdScoreResults reference={resultRef} type={resultTypeMap[resultType]} />
      )}
    </Tab.Container>
  );
}

// Helper functions and components
function handleDownloadInput(result: string, exampleFilename?: string) {
  // Try to get the input file from the DOM or state
  const fileInput = document.getElementById("ldscore-form-heritability-file-input") as HTMLInputElement | null;
  if (fileInput && fileInput.files && fileInput.files[0]) {
    const file = fileInput.files[0];
    const url = URL.createObjectURL(file);
    const a = document.createElement("a");
    a.href = url;
    a.download = file.name;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }, 0);
  } else if (exampleFilename) {
    // Download from backend API
    const a = document.createElement("a");
    a.href = `/LDlinkRestWeb/copy_and_download/${encodeURIComponent(exampleFilename)}`;
    a.download = exampleFilename || "example_input.txt";
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      document.body.removeChild(a);
    }, 0);
  } else {
    alert("No input file available to download.");
  }
}
function handleDownloadTable(result: string, filename: string) {
  // Helper to parse genetic correlation result into sections
  function parseCorrelationResult(result: string) {
    // This is a simple parser based on expected section headers
    const sections = {
      herit1: "",
      herit2: "",
      gencov: "",
      gencorr: "",
      summary: "",
    };
    let current: keyof typeof sections | null = null;
    const lines = result.split(/\r?\n/);
    for (const line of lines) {
      if (/Heritability of phenotype 1/i.test(line)) {
        current = "herit1";
        continue;
      }
      if (/Heritability of phenotype 2/i.test(line)) {
        current = "herit2";
        continue;
      }
      if (/Genetic Covariance/i.test(line)) {
        current = "gencov";
        continue;
      }
      if (/Genetic Correlation/i.test(line)) {
        current = "gencorr";
        continue;
      }
      if (/Summary of Genetic Correlation Results/i.test(line)) {
        current = "summary";
        continue;
      }
      if (current) {
        sections[current] += (sections[current] ? "\n" : "") + line;
      }
    }
    // Remove leading/trailing whitespace
    Object.keys(sections).forEach((k) => {
      sections[k as keyof typeof sections] = sections[k as keyof typeof sections].trim();
    });
    return sections;
  }

  // Helper to parse heritability result into fields
  function parseHeritabilityResult(result: string) {
    // Try to extract values from the result string
    const h2Match = result.match(/Total Observed scale h2:\s*([^\n]+)/i);
    const lambdaGCMatch = result.match(/Lambda GC:\s*([^\n]+)/i);
    const meanChi2Match = result.match(/Mean Chi\^?2:\s*([^\n]+)/i);
    const interceptMatch = result.match(/Intercept:\s*([^\n]+)/i);
    const ratioMatch = result.match(/Ratio:\s*([^\n]+)/i);
    return {
      h2: h2Match ? h2Match[1].trim() : "",
      lambdaGC: lambdaGCMatch ? lambdaGCMatch[1].trim() : "",
      meanChi2: meanChi2Match ? meanChi2Match[1].trim() : "",
      intercept: interceptMatch ? interceptMatch[1].trim() : "",
      ratio: ratioMatch ? ratioMatch[1].trim() : "",
    };
  }

  if (filename.includes('correlation')) {
    const parsed = parseCorrelationResult(result);
    const sections = [
      { title: "Heritability of phenotype 1", content: parsed.herit1 },
      { title: "Heritability of phenotype 2", content: parsed.herit2 },
      { title: "Genetic Covariance", content: parsed.gencov },
      { title: "Genetic Correlation", content: parsed.gencorr },
      { title: "Summary of Genetic Correlation Results", content: parsed.summary },
    ];
    const lines: string[] = [];
    for (const section of sections) {
      if (section.content && section.content.trim()) {
        lines.push(section.title);
        // For summary, keep as is; for others, format as key-value
        if (section.title === "Summary of Genetic Correlation Results") {
          lines.push(section.content);
        } else {
          section.content.split(/\r?\n/).forEach(line => lines.push(line));
        }
        lines.push(""); // blank line between sections
      }
    }
    const blob = new Blob([lines.join("\n")], { type: "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      document.body.removeChild(a);
    }, 0);
  } else {
    // Heritability mode (default)
    const parsed = parseHeritabilityResult(result);
    const lines = [
      "Heritability Result",
      "-------------------",
      `Total Observed scale h2:\t${parsed.h2}`,
      `Lambda GC:\t${parsed.lambdaGC}`,
      `Mean Chi^2:\t${parsed.meanChi2}`,
      `Intercept:\t${parsed.intercept}`,
      `Ratio:\t${parsed.ratio}`,
    ];
    const blob = new Blob([lines.join("\n")], { type: "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      document.body.removeChild(a);
    }, 0);
  }
}
function RawHeritabilityPanel({ result, title }: { result: string; title: string }) {
  const [showRaw, setShowRaw] = useState(false);
  return (
    <div className="panel panel-default mt-3" style={{ maxWidth: 600, margin: '20px auto 0 auto', border: '1px solid #bdbdbd', borderRadius: 6, boxShadow: '0 1px 2px rgba(0,0,0,0.03)' }}>
      <div className="panel-heading" style={{ fontWeight: 600, background: '#f5f5f5', padding: '8px 12px', borderBottom: '1px solid #ddd', borderTopLeftRadius: 6, borderTopRightRadius: 6, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span>{title}</span>
        <button
          type="button"
          className="btn btn-sm btn-outline-primary"
          onClick={() => setShowRaw((open) => !open)}
          aria-expanded={showRaw}
          aria-controls="heritRawPanelBody"
        >
          {showRaw ? "Collapse" : "Expand"}
        </button>
      </div>
      <div
        id="heritRawPanelBody"
        className={showRaw ? "panel-body" : "panel-body collapse"}
        style={{ padding: showRaw ? '12px' : 0, display: showRaw ? 'block' : 'none', background: '#f9f9f9' }}
      >
        <pre style={{ fontSize: '0.97em', whiteSpace: 'pre-wrap', margin: 0 }}>{result}</pre>
      </div>
    </div>
  );
}
