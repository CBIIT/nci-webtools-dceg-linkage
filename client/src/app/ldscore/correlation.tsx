"use client";
import { useForm } from "react-hook-form";
import { Row, Col, Form, Button, Alert, ButtonGroup, ToggleButton } from "react-bootstrap";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter, usePathname } from "next/navigation";
import { fetchGeneticCorrelationResult, fetchLdScoreRuns, upload, validateSumstats, LdScoreRunSummary } from "@/services/queries";
import LdscoreSourceSelect, { LdscoreSourceValue, defaultLdscoreSourceValue } from "@/components/select/ldscore-source-select";
import CalculateLoading from "@/components/calculateLoading";
import HoverUnderlineLink from "@/components/HoverUnderlineLink";
import { useStore } from "@/store";
import { generateReference, parseLdScoreCalculationError } from "@/services/utils";
import { useEffect, useState } from "react";
import LdScoreResults from "./results";
import { useLdScoreUpload } from "./useLdScoreUpload";

interface CorrelationFormData {
  file?: FileList;
  file2?: FileList;
  sumstatsFormat1: SumstatsFormat;
  sumstatsFormat2: SumstatsFormat;
  scale: "observed" | "liability";
  samplePrev1?: string;
  popPrev1?: string;
  samplePrev2?: string;
  popPrev2?: string;
}

type SumstatsFormat = "" | "plink_raw" | "regenie_raw" | "saige_raw" | "pre_munged";

const sumstatsFormatOptions: Array<{ value: Exclude<SumstatsFormat, "">; label: string }> = [
  { value: "plink_raw", label: "PLINK raw" },
  { value: "regenie_raw", label: "REGENIE raw" },
  { value: "saige_raw", label: "SAIGE raw" },
  { value: "pre_munged", label: "Pre-munged" },
];

const sumstatsFormatLabels = sumstatsFormatOptions.reduce<Record<string, string>>((labels, option) => {
  labels[option.value] = option.label;
  return labels;
}, {});

const defaultGeneticForm: CorrelationFormData = {
  file: undefined,
  file2: undefined,
  sumstatsFormat1: "",
  sumstatsFormat2: "",
  scale: "observed",
  samplePrev1: "0.5",
  popPrev1: "0.01",
  samplePrev2: "0.5",
  popPrev2: "0.01",
};

const supportedSumstatsExtensions = [".txt", ".tsv", ".csv", ".gz", ".sumstats", ".glm", ".assoc", ".regenie", ".saige"];
const sumstatsAccept = supportedSumstatsExtensions.join(",");

function hasSupportedSumstatsExtension(filename: string): boolean {
  const lowerFilename = filename.toLowerCase();
  return supportedSumstatsExtensions.some((extension) => lowerFilename.endsWith(extension));
}

export default function Correlation() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const pathname = usePathname();
  const { genome_build } = useStore((state) => state);
  const currentSessionLdScoreRuns = useStore((state) => state.ldScoreRuns);

  const [reference, setReference] = useState<string>("");
  const [exampleFile1, setExampleFile1] = useState<string>("");
  const [exampleFile2, setExampleFile2] = useState<string>("");
  const [uploadedFile1, setUploadedFile1] = useState<string>("");
  const [uploadedFile2, setUploadedFile2] = useState<string>("");
  const [uploading, setUploading] = useState(false);
  const [useExampleCorrelation, setUseExampleCorrelation] = useState(false);
  const [geneticLoading, setGeneticLoading] = useState(false);
  const [geneticCorrelationResultRef, setGeneticCorrelationResultRef] = useState<string | null>(null);
  const [geneticError, setGeneticError] = useState<string>("");
  const [fileError, setFileError] = useState<string>("");
  const [renameWarnings, setRenameWarnings] = useState<string>("");
  const [file1Valid, setFile1Valid] = useState(false);
  const [file2Valid, setFile2Valid] = useState(false);
  const [validationError1, setValidationError1] = useState<string>("");
  const [validationError2, setValidationError2] = useState<string>("");
  const [ldscoreSourceValue, setLdscoreSourceValue] = useState<LdscoreSourceValue>(defaultLdscoreSourceValue);
  const [ldscoreSourceError, setLdscoreSourceError] = useState<string>("");
  const [priorLdScoreRuns, setPriorLdScoreRuns] = useState<LdScoreRunSummary[]>([]);
  const [priorRunsLoading, setPriorRunsLoading] = useState(false);
  const ldScoreUpload = useLdScoreUpload();

  useEffect(() => {
    let cancelled = false;
    setPriorRunsLoading(true);
    fetchLdScoreRuns()
      .then(({ runs }) => {
        if (!cancelled) setPriorLdScoreRuns(runs);
      })
      .catch(() => {
        if (!cancelled) setPriorLdScoreRuns([]);
      })
      .finally(() => {
        if (!cancelled) setPriorRunsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const handleFileUpload = async (file: File, fileNumber: 1 | 2, sumstatsFormat: SumstatsFormat) => {
    setFileError(""); // Clear any previous errors
    setUploading(true);
    
    // Generate new reference if not already set
    const newReference = reference || generateReference();
    if (!reference) {
      setReference(newReference);
    }
    
    const formData = new FormData();
    formData.append("ldscoreFile", file);
    formData.append("reference", newReference);
    formData.append("summary_stats_format", sumstatsFormat);
    formData.append("analysis_type", "genetic_correlation");
    formData.append("trait", String(fileNumber));
   
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
        const validateData = await validateSumstats(filenameToUse, newReference, sumstatsFormat, String(fileNumber));
       // console.log("File validation response:", validateData);
        
        if (validateData?.fileValid?.valid) {
          const normalizedFilename = validateData.fileValid.normalizedFilename || validateData.fileValid.normalized_filename || filenameToUse;
          if (normalizedFilename !== filenameToUse) {
            setRenameWarnings((prev) => (prev ? prev + "; " + `File was normalized to ${normalizedFilename}` : `File was normalized to ${normalizedFilename}`));
          }
          if (fileNumber === 1) {
            setFile1Valid(true);
            setValidationError1("");
            setUploadedFile1(normalizedFilename);
          } else {
            setFile2Valid(true);
            setValidationError2("");
            setUploadedFile2(normalizedFilename);
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
        return filenameToUse;
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
    defaultValues: defaultGeneticForm,
  });

  const selectedScale = geneticForm.watch("scale");
  // required is enforced inside validate (rather than via the standalone `required`
  // rule) so it can be bypassed once example/uploaded data is present; RHF evaluates
  // `required` before `validate` and would otherwise fail immediately since the file
  // input is never given a value when using example data.
  const file1Registration = geneticForm.register("file", {
    validate: (fileList: FileList | undefined) => {
      if (uploadedFile1 || exampleFile1) return true;
      if (!fileList || fileList.length === 0) return "File is required";
      const file = fileList[0];
      return hasSupportedSumstatsExtension(file.name) || 'Only .txt, .tsv, .csv, .gz, .sumstats, .glm, .assoc, .regenie, or .saige files are allowed';
    }
  });
  const file2Registration = geneticForm.register("file2", {
    validate: (fileList: FileList | undefined) => {
      if (uploadedFile2 || exampleFile2) return true;
      if (!fileList || fileList.length === 0) return "File is required";
      const file = fileList[0];
      return hasSupportedSumstatsExtension(file.name) || 'Only .txt, .tsv, .csv, .gz, .sumstats, .glm, .assoc, .regenie, or .saige files are allowed';
    }
  });

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
    if (ldscoreSourceValue.mode === "reference" && !ldscoreSourceValue.pop) {
      setLdscoreSourceError("Population is required");
      return;
    }
    if (ldscoreSourceValue.mode !== "reference" && !ldscoreSourceValue.ldscoreReference) {
      setLdscoreSourceError("Select an LD score run to reuse, or upload *.l2.ldscore.gz, *.l2.M, *.l2.M_5_50 files");
      return;
    }
    setLdscoreSourceError("");
    setGeneticCorrelationResultRef(null);
    setGeneticError("");
    setGeneticLoading(true);
    const genomeBuild = genome_build || "grch37";
    const isExample = !!exampleFile1;
    const filename = exampleFile1 || uploadedFile1;
    const filename2 = exampleFile2 || uploadedFile2;
    const params = new URLSearchParams({
      filename,
      filename2,
      genome_build: genomeBuild,
      isExample: isExample ? "true" : "false",
      reference,
      summary_stats_format: `${data.sumstatsFormat1},${data.sumstatsFormat2}`,
    });

    if (ldscoreSourceValue.mode === "reference") {
      params.append("pop", ldscoreSourceValue.pop?.value || "");
      params.append("ldscoreSource", "reference");
    } else {
      params.append("ldscoreSource", "custom");
      params.append("ldscoreReference", ldscoreSourceValue.ldscoreReference || "");
    }

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
      setGeneticError(parseLdScoreCalculationError(error, "Failed to process genetic correlation calculation. Please check your input and try again."));
    } finally {
      setGeneticLoading(false);
    }
  };

  const onGeneticReset = () => {
    geneticForm.reset(defaultGeneticForm);
    setGeneticCorrelationResultRef(null);
    setGeneticError("");
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
    setRenameWarnings("");
    setLdscoreSourceValue(defaultLdscoreSourceValue);
    setLdscoreSourceError("");
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
                    const newReference = generateReference();
                    setReference(newReference);
                    setExampleFile1("BBJ_HDLC22.txt");
                    setExampleFile2("BBJ_LDLC22.txt");
                    geneticForm.setValue("sumstatsFormat1", "pre_munged");
                    geneticForm.setValue("sumstatsFormat2", "pre_munged");
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
                    geneticForm.setValue("sumstatsFormat1", "");
                    geneticForm.setValue("sumstatsFormat2", "");
                    //geneticForm.setValue("pop", null);
                  }
                }}
              />
            </div>
          </Col>
        
           <Col s={12} sm={12} md={6} lg={3}>
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

           <Col s={12} sm={12} md={6} lg={3}>
            <Form.Group controlId="ldscoreSource" className="mb-3">
              <Form.Label>LD Score Source</Form.Label>
              <LdscoreSourceSelect
                value={ldscoreSourceValue}
                onChange={setLdscoreSourceValue}
                currentSessionRuns={currentSessionLdScoreRuns}
                priorRuns={priorLdScoreRuns}
                priorRunsLoading={priorRunsLoading}
                disabled={geneticLoading}
                onRequestUpload={() => ldScoreUpload.reset()}
                onRequestImport={() => ldScoreUpload.reset()}
              />
              {ldscoreSourceValue.mode === "customUpload" && (
                <div className="mt-2">
                  <Form.Control
                    type="file"
                    multiple
                    accept=".bed,.bim,.fam"
                    disabled={geneticLoading || ldScoreUpload.uploading || ldScoreUpload.computing}
                    onChange={async (e) => {
                      const input = e.target as HTMLInputElement;
                      if (input.files && input.files.length === 3) {
                        const uploadResult = await ldScoreUpload.uploadFiles(input.files);
                        if (uploadResult) {
                          const computedRun = await ldScoreUpload.computeLdScore(uploadResult);
                          if (computedRun) {
                            setLdscoreSourceValue((prev) => ({ ...prev, ldscoreReference: computedRun.reference }));
                          }
                        }
                      }
                    }}
                  />
                  {/* <div style={{ fontSize: "0.85rem" }}>Upload matching *.bed, *.bim, *.fam files (same base name). The LD score will be computed automatically before running this analysis.</div>
                  {(ldScoreUpload.uploading || ldScoreUpload.computing) && (
                    <div className="mt-1">{ldScoreUpload.uploading ? "Uploading files..." : "Computing LD score..."}</div>
                  )} */}
                  {ldScoreUpload.fileError && <Form.Text className="text-danger">{ldScoreUpload.fileError}</Form.Text>}
                </div>
              )}
              {ldscoreSourceValue.mode === "customImport" && (
                <div className="mt-2">
                  <Form.Control
                    type="file"
                    multiple
                    accept=".gz,.M,.M_5_50"
                    disabled={geneticLoading || ldScoreUpload.uploading || ldScoreUpload.importing}
                    onChange={async (e) => {
                      const input = e.target as HTMLInputElement;
                      // Validate on every selection change (not just when exactly 3 files are
                      // chosen) so a stale error from a prior attempt is replaced immediately --
                      // each file dialog invocation replaces the whole selection, so a fix-up
                      // pick of just the missing file would otherwise leave the old error stuck.
                      if (input.files && input.files.length > 0) {
                        const importedRun = await ldScoreUpload.importPrecomputedLdScore(input.files, genome_build || "grch37");
                        if (importedRun) {
                          setLdscoreSourceValue((prev) => ({ ...prev, ldscoreReference: importedRun.reference }));
                        }
                      }
                    }}
                  />
                  <div style={{ fontSize: "0.85rem" }}>Upload matching *.l2.ldscore.gz, *.l2.M, *.l2.M_5_50 files (same base name).</div>
                  {ldScoreUpload.importing && <div className="mt-1">Importing LD score files...</div>}
                  {ldScoreUpload.fileError && <Form.Text className="text-danger">{ldScoreUpload.fileError}</Form.Text>}
                </div>
              )}
              {ldscoreSourceError && <Form.Text className="text-danger d-block">{ldscoreSourceError}</Form.Text>}
            </Form.Group>
          </Col>
          <Col s={12} sm={12} md={6} lg={2}>
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
          {selectedScale === "liability" && ( 
              <div
                style={{
                  position: "absolute",
                  top: 0,
                  bottom: 0,
                  left: -5,
                  width: "100%",
                  border: "1px solid #dee2e6",
                  borderRadius: "0.375rem",
                  pointerEvents: "none",
                }}
              />
             )}
           <Row>
             <Form.Label className="fw-semibold mb-1">Trait 1</Form.Label>
            <Col s={12} sm={12} md={6} lg={4}>
            <Form.Group controlId="sumstatsFormat1" className="mb-3">
              <Form.Label>Summary statistics format</Form.Label>
              <Form.Select
                disabled={geneticLoading || useExampleCorrelation}
                style={{ maxWidth: "400px" }}
                {...geneticForm.register("sumstatsFormat1", { required: "Summary statistics format is required" })}
                onChange={(e) => {
                  geneticForm.setValue("sumstatsFormat1", e.target.value as SumstatsFormat, { shouldValidate: true });
                  setGeneticCorrelationResultRef(null);
                  setUploadedFile1("");
                  setFile1Valid(false);
                  setValidationError1("");
                  geneticForm.setValue("file", undefined);
                }}
              >
                <option value="">Select format</option>
                {sumstatsFormatOptions.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </Form.Select>
              <Form.Text className="text-danger">{geneticForm.formState.errors?.sumstatsFormat1?.message}</Form.Text>
            </Form.Group>
            <Form.Group controlId="file" className="mb-3">
              <Form.Label>Upload GWAS summary statistics file</Form.Label>
              {typeof exampleFile1 === "string" && exampleFile1 !== "" ? (
                <div className="form-control bg-light">{exampleFile1}</div>
              ) : (
                <Form.Control 
                  type="file" 
                  {...file1Registration}
                  accept={sumstatsAccept}
                  title="Upload PLINK, REGENIE, SAIGE, or LDSC-ready GWAS sumstats"
                  disabled={geneticLoading}
                  style={{ maxWidth: "400px" }}
                  onChange={async (e) => {
                    await file1Registration.onChange(e);
                    const input = e.target as HTMLInputElement;
                    const file = input.files && input.files[0];
                    setGeneticCorrelationResultRef(null);
                    if (file) {
                      const validFormat = await geneticForm.trigger("sumstatsFormat1");
                      if (!validFormat) {
                        input.value = "";
                        geneticForm.setValue("file", undefined, { shouldValidate: true });
                        return;
                      }
                      await handleFileUpload(file, 1, geneticForm.getValues("sumstatsFormat1"));
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
                      <Form.Label>
                       Sample prevalence
                      </Form.Label>
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
                          title="Percentage (enter as 0–1)"
                      />
                      <Form.Text className="text-danger">{geneticForm.formState.errors?.samplePrev1?.message}</Form.Text>
                    </Form.Group>
                  </Col>
                  <Col xs={6}>
                    <Form.Group controlId="popPrev1">
                      <Form.Label>
                        Population prevalence
                       </Form.Label>
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
                          title="Percentage (enter as 0–1)"
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
          {selectedScale === "liability" && (
            <div
              style={{
                position: "absolute",
                top: 0,
                bottom: 0,
                left: -5,
                width: "100%",
                border: "1px solid #dee2e6",
                borderRadius: "0.375rem",
                pointerEvents: "none",
              }}
            />
          )}
        <Row>  
           <Form.Label className="fw-semibold mb-1">Trait 2</Form.Label>
          <Col s={12} sm={12} md={6} lg={4}>
            <Form.Group controlId="sumstatsFormat2" className="mb-3">
              <Form.Label>Summary statistics format</Form.Label>
              <Form.Select
                disabled={geneticLoading || useExampleCorrelation}
                style={{ maxWidth: "400px" }}
                {...geneticForm.register("sumstatsFormat2", { required: "Summary statistics format is required" })}
                onChange={(e) => {
                  geneticForm.setValue("sumstatsFormat2", e.target.value as SumstatsFormat, { shouldValidate: true });
                  setGeneticCorrelationResultRef(null);
                  setUploadedFile2("");
                  setFile2Valid(false);
                  setValidationError2("");
                  geneticForm.setValue("file2", undefined);
                }}
              >
                <option value="">Select format</option>
                {sumstatsFormatOptions.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </Form.Select>
              <Form.Text className="text-danger">{geneticForm.formState.errors?.sumstatsFormat2?.message}</Form.Text>
            </Form.Group>
            <Form.Group controlId="file2" className="mb-3">
              <Form.Label>Upload GWAS summary statistics file</Form.Label>
              {typeof exampleFile2 === "string" && exampleFile2 !== "" ? (
                <div className="form-control bg-light">{exampleFile2}</div>
              ) : (
                <Form.Control 
                  type="file" 
                  {...file2Registration}
                  accept={sumstatsAccept}
                  title="Upload PLINK, REGENIE, SAIGE, or LDSC-ready GWAS sumstats"
                  disabled={geneticLoading}
                  style={{ maxWidth: "400px" }}
                  onChange={async (e) => {
                    await file2Registration.onChange(e);
                    const input = e.target as HTMLInputElement;
                    const file = input.files && input.files[0];
                    setGeneticCorrelationResultRef(null);
                    if (file) {
                      const validFormat = await geneticForm.trigger("sumstatsFormat2");
                      if (!validFormat) {
                        input.value = "";
                        geneticForm.setValue("file2", undefined, { shouldValidate: true });
                        return;
                      }
                      await handleFileUpload(file, 2, geneticForm.getValues("sumstatsFormat2"));
                      geneticForm.clearErrors("file2");
                    }
                  }}
                />
              )}
                <Form.Text className="text-danger">{geneticForm.formState.errors?.file2?.message}</Form.Text>
              </Form.Group>
              </Col>
              {selectedScale === "liability" && (
                <>
                <Col s={12} sm={12} md={6} lg={5}>
                    <Row>
                      <Col xs={6}>
                        <Form.Group controlId="samplePrev2">
                          <Form.Label>Sample prevalence
                           </Form.Label>
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
                             title="Percentage (enter as 0–1)"
                          />
                          <Form.Text className="text-danger">{geneticForm.formState.errors?.samplePrev2?.message}</Form.Text>
                        </Form.Group>
                      </Col>
                      <Col xs={6}>
                        <Form.Group controlId="popPrev2">
                          <Form.Label>Population prevalence
                           </Form.Label>
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
                               title="Percentage (enter as 0–1)"
                          />
                          <Form.Text className="text-danger">{geneticForm.formState.errors?.popPrev2?.message}</Form.Text>
                        </Form.Group>
                      </Col>
                    </Row>
                  </Col>
                  </>)}
                </Row>
                </div>
                 <Row>
                  <Col s={12} sm={12} md={6} lg={4}>
                   <div style={{ fontSize: '0.875rem', fontWeight: 'normal', maxWidth: 400 }}>Upload PLINK, REGENIE, SAIGE, or LDSC-ready summary statistics. Special characters will be removed automatically from the file name. Use only A-Z, 0-9, dots, hyphens, and underscores.</div>
                  </Col>
                </Row>  

                 {((exampleFile1 || uploadedFile1) || (exampleFile2 || uploadedFile2)) && (
                <>
                  <span style={{ fontWeight: 600 }}>Input files uploaded:</span><br />
                  <div>
                    <span style={{ fontWeight: 600 }}>Trait 1 format:</span> {sumstatsFormatLabels[geneticForm.getValues("sumstatsFormat1")] || "Not selected"}
                  </div>
                  <div>
                    <span style={{ fontWeight: 600 }}>Trait 2 format:</span> {sumstatsFormatLabels[geneticForm.getValues("sumstatsFormat2")] || "Not selected"}
                  </div>
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
      {geneticError && (
        <Alert variant="danger" className="mt-2">
          {geneticError}
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
