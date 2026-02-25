"use client";
import { useForm } from "react-hook-form";
import { Row, Col, Form, Button, Alert, ButtonGroup, ToggleButton } from "react-bootstrap";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter, usePathname } from "next/navigation";
import { fetchGeneticCorrelationResult, upload, validateSumstats } from "@/services/queries";
import LdscorePopSelect, { LdscorePopOption } from "@/components/select/ldscore-pop-select";
import CalculateLoading from "@/components/calculateLoading";
import HoverUnderlineLink from "@/components/HoverUnderlineLink";
import { useStore } from "@/store";
import { useState } from "react";
import LdScoreResults from "./results";

interface CorrelationFormData {
  file?: FileList;
  file2?: FileList;
  pop: LdscorePopOption | null;
  scale: "observed" | "liability";
  samplePrev1?: string;
  popPrev1?: string;
  samplePrev2?: string;
  popPrev2?: string;
}

export default function Correlation() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const pathname = usePathname();
  const { genome_build } = useStore((state) => state);
  
  const [reference, setReference] = useState<string>("");
  const [exampleFile1, setExampleFile1] = useState<string>("");
  const [exampleFile2, setExampleFile2] = useState<string>("");
  const [uploadedFile1, setUploadedFile1] = useState<string>("");
  const [uploadedFile2, setUploadedFile2] = useState<string>("");
  const [uploading, setUploading] = useState(false);
  const [useExampleCorrelation, setUseExampleCorrelation] = useState(false);
  const [geneticLoading, setGeneticLoading] = useState(false);
  const [geneticCorrelationResultRef, setGeneticCorrelationResultRef] = useState<string | null>(null);
  const [fileError, setFileError] = useState<string>("");
  const [renameWarnings, setRenameWarnings] = useState<string>("");
  const [file1Valid, setFile1Valid] = useState(false);
  const [file2Valid, setFile2Valid] = useState(false);
  const [validationError1, setValidationError1] = useState<string>("");
  const [validationError2, setValidationError2] = useState<string>("");

  const handleFileUpload = async (file: File, fileNumber: 1 | 2) => {
    setFileError(""); // Clear any previous errors
    setUploading(true);
    
    // Generate new reference if not already set
    const newReference = reference || Math.floor(Math.random() * (99999 - 10000 + 1)).toString();
    if (!reference) {
      setReference(newReference);
    }
    
    const formData = new FormData();
    formData.append("ldscoreFile", file);
    formData.append("reference", newReference);
   
    try {
      const response = await upload(formData);
      if (response.status === 200) {
        // Determine filename to use; handle server rename mapping if present
        let filenameToUse = file.name;
        if (response.data && response.data.renamed) {
          if (Array.isArray(response.data.renamed) && response.data.renamed.length > 0) {
            const mapping = response.data.renamed[0];
            if (mapping.original !== mapping.sanitized) {
              // append warning message (multiple uploads will concatenate)
              setRenameWarnings((prev) => (prev ? prev + "; " + `File was renamed to ${mapping.sanitized}` : `File was renamed to ${mapping.sanitized}`));
            }
            filenameToUse = mapping.sanitized;
          }
        }
        // After successful upload, validate the file (use server-provided name)
        const validateData = await validateSumstats(filenameToUse, newReference);
       // console.log("File validation response:", validateData);
        
        if (validateData?.fileValid?.valid) {
          if (fileNumber === 1) {
            setFile1Valid(true);
            setValidationError1("");
            setUploadedFile1(filenameToUse);
          } else {
            setFile2Valid(true);
            setValidationError2("");
            setUploadedFile2(filenameToUse);
          }
        } else {
          if (fileNumber === 1) {
            setFile1Valid(false);
            const errors = validateData?.fileValid?.errors || [];
            const warnings = validateData?.fileValid?.warnings || [];
            const errorMessages = [...errors, ...warnings].join(". ");
            setValidationError1(errorMessages || "File validation failed. Please check the file format.");
            setUploadedFile1(filenameToUse);
          } else {
            setFile2Valid(false);
            const errors = validateData?.fileValid?.errors || [];
            const warnings = validateData?.fileValid?.warnings || [];
            const errorMessages = [...errors, ...warnings].join(". ");
            setValidationError2(errorMessages || "File validation failed. Please check the file format.");
            setUploadedFile2(filenameToUse);
          }
        }
        return file.name;
      } else {
        setFileError('Error: File upload failed');
        return "";
      }
    } catch (e) {
      setFileError('Error: File upload failed');
      return "";
    } finally {
      setUploading(false);
    }
  };

  const geneticForm = useForm<CorrelationFormData>({
    defaultValues: {
      file: undefined,
      file2: undefined,
      pop: null,
      scale: "observed",
      samplePrev1: "0.5",
      popPrev1: "0.01",
      samplePrev2: "0.5",
      popPrev2: "0.01",
    }
  });

  const selectedScale = geneticForm.watch("scale");

  const geneticMutation = useMutation({
    mutationFn: fetchGeneticCorrelationResult,
    onSuccess: (data: any) => {
      if (data?.error) {
        console.error("Genetic correlation calculation failed:", data.error);
        return;
      }
      queryClient.setQueryData(["ldscore", data.id], data);
      router.push(`${pathname}?ref=${data.id}`);
    },
    onError: (error) => {
      console.error("Genetic correlation mutation error:", error);
    },
  });

  const onGeneticSubmit = async (data: CorrelationFormData) => {
    setGeneticCorrelationResultRef(null);
    setGeneticLoading(true);
    const pop = data.pop?.value || '';
    const genomeBuild = genome_build || "grch37";
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

    if (data.scale === "liability") {
      params.append("scale", "liability");
      params.append("samp_prev", `${data.samplePrev1 || ""},${data.samplePrev2 || ""}`);
      params.append("pop_prev", `${data.popPrev1 || ""},${data.popPrev2 || ""}`);
    } else {
      params.append("scale", "observed");
    }
    try {
      await fetchGeneticCorrelationResult(params);
      setGeneticCorrelationResultRef(reference);
    } catch (error) {
      console.error("Genetic correlation calculation error:", error);
    } finally {
      setGeneticLoading(false);
    }
  };

  const onGeneticReset = () => {
    geneticForm.reset();
    setGeneticCorrelationResultRef(null);
    setReference("");
    setExampleFile1("");
    setExampleFile2("");
    setUploadedFile1("");
    setUploadedFile2("");
    setUseExampleCorrelation(false);
    setFileError("");
    setFile1Valid(false);
    setFile2Valid(false);
    setValidationError1("");
    setValidationError2("");
    geneticForm.setValue("pop", null);
    geneticForm.setValue("scale", "observed");
    geneticForm.setValue("samplePrev1", "0.5");
    geneticForm.setValue("popPrev1", "0.01");
    geneticForm.setValue("samplePrev2", "0.5");
    geneticForm.setValue("popPrev2", "0.01");
    setRenameWarnings("");
  };

  return (
    <>
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
            <div className="spinner-border text-primary" role="status">
              <span className="visually-hidden">Loading...</span>
            </div>
          </div>
        </div>
      )}

      <Form id="correlation-form" onSubmit={geneticForm.handleSubmit(onGeneticSubmit)} onReset={onGeneticReset} noValidate>
        <Row>
          <Col s={12} sm={12} md={6} lg={4}>
            <Form.Group>
              <div className="mt-2">
                <HoverUnderlineLink href="/help#LDscore">
                  Click here for sample format
                </HoverUnderlineLink>
              </div>
              <Form.Text className="text-danger">{geneticForm.formState.errors?.file2?.message}</Form.Text>
         
            </Form.Group>
              <div className="mb-3">
              <Form.Check
                type="switch"
                id="use-example-correlation"
                label="Use example data"
                checked={useExampleCorrelation}
                disabled={geneticLoading}
                onChange={(e) => {
                  setUseExampleCorrelation(e.target.checked);
                   setGeneticCorrelationResultRef(null);
                  if (e.target.checked) {
                    // Generate new reference for example data
                    const newReference = Math.floor(Math.random() * (99999 - 10000 + 1)).toString();
                    setReference(newReference);
                    setExampleFile1("BBJ_HDLC22.txt");
                    setExampleFile2("BBJ_LDLC22.txt");
                    setUploadedFile1("");
                    setUploadedFile2("");
                    setValidationError1("");
                    setValidationError2("");
                    setFile1Valid(false);
                    setFile2Valid(false);
                    geneticForm.clearErrors("file");
                    geneticForm.clearErrors("file2");
                  } else {
                    setReference("");
                    setExampleFile1("");
                    setExampleFile2("");
                    //geneticForm.setValue("pop", null);
                  }
                }}
              />
            </div>
          </Col>
        
           <Col s={12} sm={12} md={6} lg={4}>
            <Form.Group controlId="scale" className="mb-3">
              <Form.Label className="d-block">Scale</Form.Label>
              <ButtonGroup>
                <ToggleButton
                  id="radio-correlation-scale-observed"
                  title="Observed scale"
                  type="radio"
                  variant="outline-primary"
                  disabled={geneticLoading}
                  {...geneticForm.register("scale")}
                  value="observed"
                  checked={selectedScale === "observed"}
                  onChange={() => {
                    geneticForm.setValue("scale", "observed");
                    geneticForm.setValue("samplePrev1", "0.5");
                    geneticForm.setValue("popPrev1", "0.01");
                    geneticForm.setValue("samplePrev2", "0.5");
                    geneticForm.setValue("popPrev2", "0.01");
                    geneticForm.clearErrors(["samplePrev1", "popPrev1", "samplePrev2", "popPrev2"]);
                  }}>
                  Observed
                </ToggleButton>
                <ToggleButton
                  id="radio-correlation-scale-liability"
                  title="Liability scale"
                  type="radio"
                  variant="outline-primary"
                  disabled={geneticLoading}
                  {...geneticForm.register("scale")}
                  value="liability"
                  checked={selectedScale === "liability"}
                  onChange={() => {
                    geneticForm.setValue("scale", "liability");
                  }}>
                  Liability
                </ToggleButton>
              </ButtonGroup>
            </Form.Group>
          </Col>

           <Col s={12} sm={12} md={6} lg={2}>
            <Form.Group controlId="pop" className="mb-3">
              <Form.Label>Population</Form.Label>
              <LdscorePopSelect name="pop" control={geneticForm.control} isLoading={geneticLoading} rules={{ required: "Population is required" }} />
              <Form.Text className="text-danger">{geneticForm.formState.errors?.pop?.message}</Form.Text>
            </Form.Group>
          </Col>
          <Col s={12} sm={12} md={12} lg={2}>
            <div className="text-end">
              <Button type="reset" variant="outline-danger" className="me-1" disabled={geneticLoading}>
                Reset
              </Button>
              <Button type="submit" variant="primary" disabled={geneticMutation.isPending || geneticLoading}>
               {geneticLoading ? "Loading..." : "Calculate"}
              </Button>
            </div>
          </Col>
        </Row>

           <div className="mb-1 position-relative">
            <div
              style={{
                position: "absolute",
                top: 0,
                bottom: 10,
                left: -5,
                width: selectedScale === "liability" ? "71%" : "33%",
                border: "1px solid #dee2e6",
                borderRadius: "0.375rem",
                pointerEvents: "none",
              }}
            />
           <Row>
             <Form.Label className="fw-semibold mb-1">Trait 1</Form.Label>
            <Col s={12} sm={12} md={6} lg={4}>
            <Form.Group controlId="file" className="mb-3">
              <Form.Label>Upload pre-munged GWAS sumstats file</Form.Label>
              {typeof exampleFile1 === "string" && exampleFile1 !== "" ? (
                <div className="form-control bg-light">{exampleFile1}</div>
              ) : (
                <Form.Control 
                  type="file" 
                  {...geneticForm.register("file", { 
                    required: "File is required",
                    validate: (fileList: FileList | undefined) => {
                      if (!fileList || fileList.length === 0) return true;
                      const file = fileList[0];
                      const ext = file.name.split('.').pop()?.toLowerCase();
                      return ext === 'txt' || 'Only .txt files are allowed';
                    }
                  })}
                  accept=".txt"
                  title="Upload pre-munged GWAS sumstats"
                  disabled={geneticLoading}
                  onChange={async (e) => {
                    const input = e.target as HTMLInputElement;
                    const file = input.files && input.files[0];
                    setGeneticCorrelationResultRef(null);
                    if (file) {
                      const filename = await handleFileUpload(file, 1);
                      setUploadedFile1(filename);
                      geneticForm.clearErrors("file");
                    }
                  }}
                />
              )}
              <Form.Text className="text-danger">{geneticForm.formState.errors?.file?.message}</Form.Text>
           
            </Form.Group>

            </Col>
              {selectedScale === "liability" && (
              <>
              <Col s={12} sm={12} md={6} lg={5}>
                <Row>
                  <Col xs={6}>
                    <Form.Group controlId="samplePrev1">
                      <Form.Label>Sample prevalence</Form.Label>
                      <Form.Control
                        type="number"
                        step="0.01"
                        min={0}
                        max={1}
                        disabled={geneticLoading}
                        placeholder="0.5"
                        style={{ maxWidth: "160px" }}
                        {...geneticForm.register("samplePrev1", {
                          validate: (value) => {
                            if (selectedScale !== "liability") return true;
                            if (!value || value.trim() === "") return "Sample prevalence is required";
                            const num = Number(value);
                            if (Number.isNaN(num)) return "Sample prevalence must be numeric";
                            return (num > 0 && num < 1) || "Sample prevalence must be between 0 and 1";
                          },
                        })}
                      />
                      <Form.Text className="text-danger">{geneticForm.formState.errors?.samplePrev1?.message}</Form.Text>
                    </Form.Group>
                  </Col>
                  <Col xs={6}>
                    <Form.Group controlId="popPrev1">
                      <Form.Label>Population prevalence</Form.Label>
                      <Form.Control
                        type="number"
                        step="0.01"
                        min={0}
                        max={1}
                        disabled={geneticLoading}
                        placeholder="0.01"
                        style={{ maxWidth: "160px" }}
                        {...geneticForm.register("popPrev1", {
                          validate: (value) => {
                            if (selectedScale !== "liability") return true;
                            if (!value || value.trim() === "") return "Population prevalence is required";
                            const num = Number(value);
                            if (Number.isNaN(num)) return "Population prevalence must be numeric";
                            return (num > 0 && num < 1) || "Population prevalence must be between 0 and 1";
                          },
                        })}
                      />
                      <Form.Text className="text-danger">{geneticForm.formState.errors?.popPrev1?.message}</Form.Text>
                    </Form.Group>
                  </Col>
                </Row>
                  </Col>       
              </>
            )}
        </Row>
        </div>
        <div className="mb-1 position-relative">
          <div
            style={{
              position: "absolute",
              top: 0,
              bottom: 50,
              left: -5,
              width: selectedScale === "liability" ? "71%" : "33%",
              border: "1px solid #dee2e6",
              borderRadius: "0.375rem",
              pointerEvents: "none",
            }}
          />
        <Row>  
           <Form.Label className="fw-semibold mb-1">Trait 2</Form.Label>
          <Col s={12} sm={12} md={6} lg={4}>
            <Form.Group controlId="file2" className="mb-3">
              <Form.Label>Upload pre-munged GWAS sumstats file</Form.Label>
              {typeof exampleFile2 === "string" && exampleFile2 !== "" ? (
                <div className="form-control bg-light">{exampleFile2}</div>
              ) : (
                <Form.Control 
                  type="file" 
                  {...geneticForm.register("file2", { 
                    required: "File is required",
                    validate: (fileList: FileList | undefined) => {
                      if (!fileList || fileList.length === 0) return true;
                      const file = fileList[0];
                      const ext = file.name.split('.').pop()?.toLowerCase();
                      return ext === 'txt' || 'Only .txt files are allowed';
                    }
                  })}
                  accept=".txt"
                  title="Upload pre-munged GWAS sumstats"
                  disabled={geneticLoading}
                  onChange={async (e) => {
                    const input = e.target as HTMLInputElement;
                    const file = input.files && input.files[0];
                    setGeneticCorrelationResultRef(null);
                    if (file) {
                      const filename = await handleFileUpload(file, 2);
                      setUploadedFile2(filename);
                      geneticForm.clearErrors("file2");
                    }
                  }}
                />
              )}
              </Form.Group>
              </Col>
              {selectedScale === "liability" && (
                <>
                <Col s={12} sm={12} md={6} lg={5}>
                    <Row>
                      <Col xs={6}>
                        <Form.Group controlId="samplePrev2">
                          <Form.Label>Sample prevalence</Form.Label>
                          <Form.Control
                            type="number"
                            step="0.01"
                            min={0}
                            max={1}
                            disabled={geneticLoading}
                            placeholder="0.5"
                            style={{ maxWidth: "160px" }}
                            {...geneticForm.register("samplePrev2", {
                              validate: (value) => {
                                if (selectedScale !== "liability") return true;
                                if (!value || value.trim() === "") return "Sample prevalence is required";
                                const num = Number(value);
                                if (Number.isNaN(num)) return "Sample prevalence must be numeric";
                                return (num > 0 && num < 1) || "Sample prevalence must be between 0 and 1";
                              },
                            })}
                          />
                          <Form.Text className="text-danger">{geneticForm.formState.errors?.samplePrev2?.message}</Form.Text>
                        </Form.Group>
                      </Col>
                      <Col xs={6}>
                        <Form.Group controlId="popPrev2">
                          <Form.Label>Population prevalence</Form.Label>
                          <Form.Control
                            type="number"
                            step="0.01"
                            min={0}
                            max={1}
                            disabled={geneticLoading}
                            placeholder="0.01"
                            style={{ maxWidth: "160px" }}
                            {...geneticForm.register("popPrev2", {
                              validate: (value) => {
                                if (selectedScale !== "liability") return true;
                                if (!value || value.trim() === "") return "Population prevalence is required";
                                const num = Number(value);
                                if (Number.isNaN(num)) return "Population prevalence must be numeric";
                                return (num > 0 && num < 1) || "Population prevalence must be between 0 and 1";
                              },
                            })}
                          />
                          <Form.Text className="text-danger">{geneticForm.formState.errors?.popPrev2?.message}</Form.Text>
                        </Form.Group>
                      </Col>
                    </Row>
                  </Col>
                  </>)}
                </Row>
                <Row>
                  <Col s={12} sm={12} md={6} lg={4}>
                   <div style={{ fontSize: '0.875rem', fontWeight: 'normal' }}>Special characters will be removed automatically, Use: A-Z, 0-9, dots, hyphens, and underscores only</div>
                  </Col>
                </Row>  
                </div>

                 {((exampleFile1 || uploadedFile1) || (exampleFile2 || uploadedFile2)) && (
                <>
                  <span style={{ fontWeight: 600 }}>Input files uploaded:</span><br />
                  {(exampleFile1 || uploadedFile1) && (
                    <>
                          <a
                        href={exampleFile1 ? `/LDlinkRestWeb/copy_and_download/${encodeURIComponent(exampleFile1)}` : `/LDlinkRestWeb/tmp/uploads/${reference}/${encodeURIComponent(uploadedFile1)}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        download
                        style={{ textDecoration: 'underline', color: '#2a71a5' }}
                      >
                        {exampleFile1 || uploadedFile1}
                      </a>
                      <br />
                    </>
                  )}
                  {(exampleFile2 || uploadedFile2) && (
                    <>
                      <a
                        href={exampleFile2 ? `/LDlinkRestWeb/copy_and_download/${encodeURIComponent(exampleFile2)}` : `/LDlinkRestWeb/tmp/uploads/${reference}/${encodeURIComponent(uploadedFile2)}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        download
                        style={{ textDecoration: 'underline', color: '#2a71a5' }}
                      >
                        {exampleFile2 || uploadedFile2}
                      </a>
                      <br />
                    </>
                  )}
                  {!useExampleCorrelation && renameWarnings.length > 0 && (
                    <Alert variant="warning" className="mt-2">
                      {renameWarnings}
                    </Alert>
                  )}
                </>
              )}
        </Form>

      {fileError && (
        <Row>
          <Col>
            <Alert variant="warning" className="mt-3">
              {fileError}
            </Alert>
          </Col>
        </Row>
      )}

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

   {!file1Valid && validationError1 && (
                <Alert variant="danger" className="mt-2">
                  The first uploaded file has the following issues:<br />
                  {validationError1}
                </Alert>
              )}

     {!file2Valid && validationError2 && (
                <Alert variant="danger" className="mt-2">
                  The second uploaded file has the following issues:<br />
                  {validationError2}
                </Alert>
              )}
      {geneticCorrelationResultRef && (
           <>
         <hr />
        <LdScoreResults
          reference={geneticCorrelationResultRef}
          type="correlation"
          uploads={
            [exampleFile1 || uploadedFile1, exampleFile2 || uploadedFile2].filter(Boolean).join(',')
          }
        />
        </>
      )}
    </>
  );
}
