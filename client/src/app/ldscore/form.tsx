"use client";
import { useForm } from "react-hook-form";
import { Row, Col, Form, Button, ButtonGroup, ToggleButton, Alert, Nav, Tab } from "react-bootstrap";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter, usePathname } from "next/navigation";
import { ldscore } from "@/services/queries";
import LdscorePopSelect, { LdscorePopOption } from "@/components/select/ldscore-pop-select";
import CalculateLoading from "@/components/calculateLoading";
import { useStore } from "@/store";
import { useState } from "react";
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
  const onHeritabilitySubmit = async (data: FormData) => {
    setHeritabilityResult("");
   // setUploadedFilename("");
    //console.log("Submitting heritability form with data:", data.pop.value); 
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
      console.log("Fetching heritability result with params:", params.toString());
      const response = await fetch(`/LDlinkRestWeb/ldherit?${params.toString()}`);
      if (response.ok) {
        const result = await response.json();
        setHeritabilityResult(result.result || JSON.stringify(result));
      } else {
        setHeritabilityResult("Failed to fetch heritability result.");
      }
    } catch (error) {
      setHeritabilityResult("Error fetching heritability result.");
    } finally {
      setHeritabilityLoading(false);
    }
  };
  const onHeritabilityReset = () => {
    heritabilityForm.reset();
  };

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
    console.log(filename2)
    console.log(params.toString())
    try {
      const response = await fetch(`/LDlinkRestWeb/ldcorrelation?${params.toString()}`);
      
      if (response.ok) {
        const result = await response.json();
        setGeneticResult(result.result || JSON.stringify(result));
 
      } else {
               console.log(response)
        setGeneticResult("Failed to fetch genetic correlation result.");
      }
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
  const onLdSubmit = async (data: FormData) => {
    const formData = new FormData();
    if (data.file) formData.append("file", data.file);
    formData.append("analysis_type", "ld_calculation");
    formData.append("pop", data.pop.value || "");
    formData.append("window", String(data.window));
    formData.append("windowUnit", data.windowUnit);
    ldMutation.mutate(formData);
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
          <Form id="ldscore-form-heritability" onSubmit={heritabilityForm.handleSubmit(onHeritabilitySubmit)} onReset={onHeritabilityReset} noValidate>
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
          {heritabilityResult && (
            <>
              <Row>
                <Col>
                  <div id="herit-table-download-raw-container" style={{ maxWidth: 600, margin: '0 auto' }}>
                    <table className="table table-bordered table-sm mb-0" style={{ width: "100%", margin: "0 auto" }}>
                      <caption style={{ captionSide: 'top', fontWeight: 600, fontSize: '1.1em', color: '#084298', textAlign: 'center', marginBottom: 0 }}>
                        Heritability Result
                      </caption>
                      <thead>
                        <tr>
                          <th style={{ border: '1px solid black', padding: '4px 8px', textAlign: 'left', backgroundColor: 'rgb(242, 242, 242)', fontWeight: 600 }}></th>
                          <th style={{ border: '1px solid black', padding: '4px 8px', textAlign: 'left', backgroundColor: 'rgb(242, 242, 242)', fontWeight: 600 }}>Value</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(() => {
                          const parsed = parseHeritabilityResult(heritabilityResult);
                          const ratioDisplay = parsed.ratio.trim().startsWith('< 0')
                            ? '< 0 (usually indicates GC correction)'
                            : parsed.ratio;
                          return [
                            ['Total Observed scale h²', parsed.h2],
                            ['Lambda GC', parsed.lambdaGC],
                            ['Mean Chi²', parsed.meanChi2],
                            ['Intercept', parsed.intercept],
                            ['Ratio', ratioDisplay],
                          ].map(([label, value]) => (
                            <tr key={label}>
                              <td style={{ border: '1px solid black', padding: '4px 8px', textAlign: 'left', fontSize: '0.97em' }}>{label}</td>
                              <td style={{ border: '1px solid black', padding: '4px 8px', textAlign: 'left', fontSize: '0.97em' }}>{value}</td>
                            </tr>
                          ));
                        })()}
                      </tbody>
                    </table>
                    <div className="panel panel-default mt-3" style={{ maxWidth: 600, margin: '20px auto 0 auto', border: '1px solid #bdbdbd', borderRadius: 6, boxShadow: '0 1px 2px rgba(0,0,0,0.03)' }}>
                      <div className="panel-heading" style={{ fontWeight: 600, background: '#f5f5f5', padding: '8px 12px', borderBottom: '1px solid #ddd', borderTopLeftRadius: 6, borderTopRightRadius: 6 }}>
                        Download Options
                      </div>
                      <div className="panel-body" style={{ padding: '12px', display: 'flex', gap: '10px', justifyContent: 'center' }}>
                        <button id="download-herit-input-btn" type="button" className="btn btn-default" style={{ border: '1px solid #bdbdbd', borderRadius: 4, background: '#fff' }} onClick={() => handleDownloadInput(heritabilityResult, exampleFilename||uploadedFilename)}>Download Input</button>
                        <button id="download-herit-tables-btn" type="button" className="btn btn-default" style={{ border: '1px solid #bdbdbd', borderRadius: 4, background: '#fff' }} onClick={() => handleDownloadTable(heritabilityResult, "heritability_result.txt")}>Download Table</button>
                      </div>
                    </div>
                    <RawHeritabilityPanel result={heritabilityResult} title="Heritability Analysis Output" />
                  </div>
                </Col>
              </Row>
            </>
          )}

          {heritabilityMutation.isError && (
            <Row>
              <Col>
                <Alert variant="danger" className="mt-3">
                  <Alert.Heading>Error</Alert.Heading>
                  <p>Failed to process Heritability calculation. Please check your input and try again.</p>
                </Alert>
              </Col>
            </Row>
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
        {geneticResult && (
          <div className="mt-3">
            <div className="panel panel-default">
              <div className="panel-body" style={{ padding: '12px', background: '#ffffff' }}>
                {(() => {
          const parsed = parseGeneticCorrelationResult(geneticResult);
          return (
            <>
              <h5>Heritability of phenotype 1</h5>
              {renderKeyValueTable(parsed.herit1 || '')}
              <h5>Heritability of phenotype 2</h5>
              {renderKeyValueTable(parsed.herit2 || '')}
              <h5>Genetic Covariance</h5>
              {renderKeyValueTable(parsed.gencov || '')}
              <h5>Genetic Correlation</h5>
              {renderKeyValueTable(parsed.gencorr || '')}
              <h5>Summary of Genetic Correlation Results</h5>
              {renderSummaryTable(parsed.summary || '')}
                 <div className="panel panel-default mt-3" style={{ maxWidth: 600, margin: '20px auto 0 auto', border: '1px solid #bdbdbd', borderRadius: 6, boxShadow: '0 1px 2px rgba(0,0,0,0.03)' }}>
                      <div className="panel-heading" style={{ fontWeight: 600, background: '#f5f5f5', padding: '8px 12px', borderBottom: '1px solid #ddd', borderTopLeftRadius: 6, borderTopRightRadius: 6 }}>
                        Download Options
                      </div>
                      <div className="panel-body" style={{ padding: '12px', display: 'flex', gap: '10px', justifyContent: 'center' }}>
                        <button
                          id="download-correlation-input1-btn"
                          type="button"
                          className="btn btn-default"
                          style={{ border: '1px solid #bdbdbd', borderRadius: 4, background: '#fff' }}
                          onClick={() => handleDownloadInput(geneticResult, exampleFile1 || uploadedFile1)}
                        >
                          Download Input 1
                        </button>
                        <button
                          id="download-correlation-input2-btn"
                          type="button"
                          className="btn btn-default"
                          style={{ border: '1px solid #bdbdbd', borderRadius: 4, background: '#fff' }}
                          onClick={() => handleDownloadInput(geneticResult, exampleFile2 || uploadedFile2)}
                        >
                          Download Input 2
                        </button>
                        <button
                          id="download-correlation-tables-btn"
                          type="button"
                          className="btn btn-default"
                          style={{ border: '1px solid #bdbdbd', borderRadius: 4, background: '#fff' }}
                          onClick={() => handleDownloadTable(geneticResult, "correlation_result.txt")}
                        >
                          Download Table
                        </button>
                      </div>
                    </div>
                    <RawHeritabilityPanel result={geneticResult} title="Correlation Analysis Output" />
            </>
          );
        })()}
              </div>
            </div>
          </div>
        )}
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
  if (filename.includes('correlation')) {
    const parsed = parseGeneticCorrelationResult(result);
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
       // lines.push("-".repeat(section.title.length));
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
function parseHeritabilityResult(result: string) {
  // Extract values using regex
  const h2Match = result.match(/Total Observed scale h2:\s*([\d.eA-Z+-]+) \(([^)]+)\)/);
  const lambdaMatch = result.match(/Lambda GC:\s*([\d.eA-Z+-]+)/);
  const meanChi2Match = result.match(/Mean Chi\^2:\s*([\d.eA-Z+-]+)/);
  const interceptMatch = result.match(/Intercept:\s*([\d.eA-Z+-]+) \(([^)]+)\)/);
  const ratioMatch = result.match(/Ratio\s*([<>=-]*)\s*([\d.eA-Z+-]+)/);
  return {
    h2: h2Match ? `${h2Match[1]} (${h2Match[2]})` : "",
    lambdaGC: lambdaMatch ? lambdaMatch[1] : "",
    meanChi2: meanChi2Match ? meanChi2Match[1] : "",
    intercept: interceptMatch ? `${interceptMatch[1]} (${interceptMatch[2]})` : "",
    ratio: ratioMatch ? `${ratioMatch[1]} ${ratioMatch[2]}` : "",
  };
}

// Helper to parse genetic correlation result string into sections
function parseGeneticCorrelationResult(resultStr: string) {
  // Only parse from the first result section onward
  const startIdx = resultStr.search(/Heritability of phenotype 1/i);
  if (startIdx === -1) return {};
  const trimmed = resultStr.slice(startIdx);
  // Section headers in order
  const headers = [
    'Heritability of phenotype 1',
    'Heritability of phenotype 2',
    'Genetic Covariance',
    'Genetic Correlation',
    'Summary of Genetic Correlation Results',
  ];
  // Find section indices
  const indices = headers.map(h => {
    const re = new RegExp(`^${h}`, 'im');
    const m = trimmed.match(re);
    return m ? trimmed.indexOf(m[0]) : -1;
  });
  // Extract sections
  const sections: Record<string, string> = {};
  for (let i = 0; i < headers.length; ++i) {
    if (indices[i] === -1) continue;
    const start = indices[i] + headers[i].length;
    const end = indices.slice(i + 1).find(idx => idx > indices[i]) ?? trimmed.length;
    sections[headers[i]] = trimmed.slice(start, end).trim();
  }
  return {
    herit1: sections['Heritability of phenotype 1'] || '',
    herit2: sections['Heritability of phenotype 2'] || '',
    gencov: sections['Genetic Covariance'] || '',
    gencorr: sections['Genetic Correlation'] || '',
    summary: sections['Summary of Genetic Correlation Results'] || '',
  };
}

function TableContainer({ children }: { children: React.ReactNode }) {
  return (
    <div className="table-responsive" style={{ maxWidth: 600, margin: '0 auto', overflowX: 'auto' }}>
      {children}
    </div>
  );
}

function renderKeyValueTable(section: string) {
  if (!section) return null;
  // Split by newlines, but also handle multiple key-value pairs on a single line
  const lines = section.split(/\r?\n/).filter(l => l.trim() && !/^[-]+$/.test(l));
  const kvPairs: [string, string][] = [];
  lines.forEach(line => {
    // Try to match all key-value pairs in the line (colon or angle brackets)
    let found = false;
    // Colon-separated pairs
    const colonPairs = line.matchAll(/([\w\s²\*\-]+?):\s*([^:<>]+?)(?=(?:[A-Z][^:]*:|$))/g);
    for (const pair of colonPairs) {
      kvPairs.push([pair[1].trim(), pair[2].trim()]);
      found = true;
    }
    // Angle bracket pairs (e.g., Key < Value)
    if (!found) {
      const angleMatch = line.match(/([\w\s²\*\-]+?)([<>])\s*([^<>=]+)/);
      if (angleMatch) {
        kvPairs.push([angleMatch[1].trim(), angleMatch[2] + ' ' + angleMatch[3].trim()]);
        found = true;
      }
    }
    // Fallback: treat the whole line as a value with an empty key
    if (!found) {
      kvPairs.push(['', line.trim()]);
      // { border: '1px solid black', padding: '4px 8px', textAlign: 'left', backgroundColor: 'rgb(242, 242, 242)', fontWeight: 600 }
    }
  });
  return (
    <TableContainer>
      <table className="table table-bordered table-sm mb-3" style={{ margin: 0, minWidth: 0 }}>
        <thead>
          <tr>
            <th style={{ border: '1px solid black', padding: '4px 8px', textAlign: 'left', backgroundColor: 'rgb(242, 242, 242)', fontWeight: 600 }}></th>
            <th style={{ border: '1px solid black', padding: '4px 8px', textAlign: 'left', backgroundColor: 'rgb(242, 242, 242)', fontWeight: 600 }}>Value</th>
          </tr>
        </thead>
        <tbody>
          {kvPairs.map(([k, v], i) => (
            <tr key={i}>
              <td style={{ border: '1px solid black', padding: '4px 8px', textAlign: 'left', fontSize: '0.97em' }}>{k}</td>
              <td style={{ border: '1px solid black', padding: '4px 8px', textAlign: 'left', fontSize: '0.97em' }}>{v}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </TableContainer>
  );
}

function renderSummaryTable(section: string) {
  if (!section) return null;
  // Exclude 'Analysis finished at' and all following lines
  const lines = section.split(/\r?\n/).filter(l => l.trim());
  const endIdx = lines.findIndex(l => /^Analysis\s+finished\s+at/i.test(l));
  const filteredLines = endIdx === -1 ? lines : lines.slice(0, endIdx);
  // Find the first line with at least two columns (header)
  let headerIdx = 0;
  while (headerIdx < filteredLines.length && filteredLines[headerIdx].split(/\s+/).length < 2) headerIdx++;
  if (headerIdx >= filteredLines.length - 1) return <pre>{section}</pre>;
  const header = filteredLines[headerIdx].split(/\s+/).filter(Boolean);
  const rows = filteredLines.slice(headerIdx + 1).map(l => l.split(/\s+/).filter(Boolean));
  return (
    <TableContainer>
      <table className="table table-bordered table-sm mb-3" style={{ margin: 0, minWidth: 0 }}>
        <thead >
          <tr>{header.map((h, i) => <th key={i} style={{ border: '1px solid black', padding: '4px 8px', textAlign: 'left', backgroundColor: 'rgb(242, 242, 242)', fontWeight: 600 }}>{h}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((cols, i) => <tr key={i}>{cols.map((c, j) => <td key={j} style={{ border: '1px solid black', padding: '4px 8px', textAlign: 'left', fontSize: '0.97em' }}>{c}</td>)}</tr>)}
        </tbody>
      </table>
    </TableContainer>
  );
}
