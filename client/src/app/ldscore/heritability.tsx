"use client";
import { useForm } from "react-hook-form";
import { Row, Col, Form, Button, Alert, ButtonGroup, ToggleButton } from "react-bootstrap";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter, usePathname } from "next/navigation";
import { fetchHeritabilityResult, upload, validateSumstats } from "@/services/queries";
import LdscorePopSelect, { LdscorePopOption } from "@/components/select/ldscore-pop-select";
import CalculateLoading from "@/components/calculateLoading";
import HoverUnderlineLink from "@/components/HoverUnderlineLink";
import { useStore } from "@/store";
import { generateReference } from "@/services/utils";
import { useState } from "react";
import LdScoreResults from "./results";

interface HeritabilityFormData {
  file?: File;
  sumstatsFormat: SumstatsFormat;
  pop: LdscorePopOption | null;
  scale: "observed" | "liability";
  samplePrev?: string;
  popPrev?: string;
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

const defaultHeritabilityForm: HeritabilityFormData = {
  file: undefined,
  sumstatsFormat: "",
  pop: null,
  scale: "observed",
  samplePrev: "0.5",
  popPrev: "0.01",
};

const supportedSumstatsExtensions = [".txt", ".tsv", ".csv", ".gz", ".sumstats", ".glm", ".assoc", ".regenie", ".saige"];
const sumstatsAccept = supportedSumstatsExtensions.join(",");

function hasSupportedSumstatsExtension(filename: string): boolean {
  const lowerFilename = filename.toLowerCase();
  return supportedSumstatsExtensions.some((extension) => lowerFilename.endsWith(extension));
}

export default function Heritability() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const pathname = usePathname();
  const { genome_build } = useStore((state) => state);
  
  const [exampleFilename, setExampleFilename] = useState<string>("");
  const [uploadedFilename, setUploadedFilename] = useState<string>("");
  const [renameWarnings, setRenameWarnings] = useState<string>("");
  const [uploading, setUploading] = useState(false);
  const [useExample, setUseExample] = useState(false);
  const [heritabilityLoading, setHeritabilityLoading] = useState(false);
  const [heritabilityResultRef, setHeritabilityResultRef] = useState<string | null>(null);
  const [reference, setReference] = useState<string>("");

  const heritabilityForm = useForm<HeritabilityFormData>({
    defaultValues: defaultHeritabilityForm,
  });


  const handleFileUpload = async (file: File, sumstatsFormat: SumstatsFormat) => {
    setUploading(true);
    setRenameWarnings("");
    
    // Generate a new reference for this upload session
    const newReference = generateReference();
    setReference(newReference);
    
    const formData = new FormData();
    formData.append("ldscoreFile", file);
    formData.append("reference", newReference);
    formData.append("summary_stats_format", sumstatsFormat);
    formData.append("analysis_type", "heritability");
   
    try {
      const response = await upload(formData);
      if (response.status === 200) {
        // If server returned a renamed mapping, surface it as a user warning
        let filenameToUse = file.name;
        if (response.data && response.data.renamed) {
          if (Array.isArray(response.data.renamed) && response.data.renamed.length > 0) {
            const mapping = response.data.renamed[0];
            if (mapping.original !== mapping.sanitized) {
              setRenameWarnings(`File was renamed to ${mapping.sanitized}`);
            }
            filenameToUse = mapping.sanitized;
          }
        }
        setUploadedFilename(filenameToUse);
        // After successful upload, validate the file (use server-provided name)
        const validateData = await validateSumstats(filenameToUse, newReference, sumstatsFormat);
       
        if (validateData?.fileValid?.valid) {
          const normalizedFilename = validateData.fileValid.normalizedFilename || validateData.fileValid.normalized_filename || filenameToUse;
          setUploadedFilename(normalizedFilename);
          if (normalizedFilename !== filenameToUse) {
            setRenameWarnings((previous) => (
              previous ? `${previous}; File was normalized to ${normalizedFilename}` : `File was normalized to ${normalizedFilename}`
            ));
          }
          heritabilityForm.clearErrors("file");
        } else {
          const errors = validateData?.fileValid?.errors || [];
          const warnings = validateData?.fileValid?.warnings || [];
          const errorMessages = [...errors, ...warnings].join(". ");
          heritabilityForm.setError("file", {
            type: "server",
            message: errorMessages || "File validation failed. Please check the file format.",
          });
        }
      } else {
        setUploadedFilename("");
        heritabilityForm.setError("file", {
          type: "server",
          message: "Failed to upload file.",
        });
      }
    } catch (e) {
      setUploadedFilename("");
      heritabilityForm.setError("file", {
        type: "server",
        message: "An error occurred during file upload.",
      });
    } finally {
      setUploading(false);
    }
  };

  const selectedScale = heritabilityForm.watch("scale");
  const fileRegistration = heritabilityForm.register("file", {
    required: "File is required",
    validate: (file: File | FileList | undefined) => {
      // If we already have an uploaded filename or example filename, validation passes
      if (uploadedFilename || exampleFilename) return true;

      if (!file) return 'File is required';
      // Handle FileList, File[], or single File
      const f = Array.isArray(file) ? file[0] : (file instanceof FileList ? file[0] : file);
      if (!f || !f.name) return 'File is required';
      return hasSupportedSumstatsExtension(f.name) || 'Only .txt, .tsv, .csv, .gz, .sumstats, .glm, .assoc, .regenie, or .saige files are allowed';
    }
  });

  const heritabilityMutation = useMutation({
    mutationFn: fetchHeritabilityResult,
    onSuccess: (data: any) => {
      if (data?.error) {
        console.error("Heritability calculation failed:", data.error);
        return;
      }
      queryClient.setQueryData(["ldscore", data.id], data);
      router.push(`${pathname}?ref=${data.id}`);
    },
    onError: (error) => {
      console.error("Heritability mutation error:", error);
    },
  });

  const onHeritabilitySubmit = async (data: HeritabilityFormData) => {
    setHeritabilityResultRef(null);
    setHeritabilityLoading(true);
    const pop = data.pop?.value || '';
    const genomeBuild = genome_build || "grch37";
    const isExample = !!exampleFilename;
    const filename = exampleFilename || uploadedFilename;
    const params = new URLSearchParams({
      filename,
      pop,
      genome_build: genomeBuild,
      isExample: isExample ? "true" : "false",
      reference,
      summary_stats_format: data.sumstatsFormat,
    });

    if (data.scale === "liability") {
      params.append("scale", "liability");
      params.append("samp_prev", data.samplePrev || "");
      params.append("pop_prev", data.popPrev || "");
    } else {
      params.append("scale", "observed");
    }

    try {
      await fetchHeritabilityResult(params);
      setHeritabilityResultRef(reference);
    } catch (error) {
      console.error("Heritability calculation error:", error);
    } finally {
      setHeritabilityLoading(false);
    }
  };

  const onHeritabilityReset = () => {
    heritabilityForm.reset(defaultHeritabilityForm);
    setHeritabilityResultRef(null);
    setExampleFilename("");
    setUploadedFilename("");
    setUseExample(false);
    setReference("");
    setRenameWarnings("");
    heritabilityForm.clearErrors("file");
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



      <Form id="heritability-form" onSubmit={heritabilityForm.handleSubmit(onHeritabilitySubmit)} onReset={onHeritabilityReset} noValidate>
        <Row>
          <Col s={12} sm={12} md={6} lg={4}>
            <Form.Group controlId="sumstatsFormat" className="mb-3">
              <Form.Label>Summary statistics format</Form.Label>
              <Form.Select
                disabled={heritabilityLoading || useExample}
                style={{ maxWidth: "400px" }}
                {...heritabilityForm.register("sumstatsFormat", { required: "Summary statistics format is required" })}
                onChange={(e) => {
                  heritabilityForm.setValue("sumstatsFormat", e.target.value as SumstatsFormat, { shouldValidate: true });
                  setHeritabilityResultRef(null);
                  setUploadedFilename("");
                  setRenameWarnings("");
                  heritabilityForm.setValue("file", undefined);
                }}
              >
                <option value="">Select format</option>
                {sumstatsFormatOptions.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </Form.Select>
              <Form.Text className="text-danger">{heritabilityForm.formState.errors?.sumstatsFormat?.message}</Form.Text>
            </Form.Group>
            <Form.Group controlId="file" className="mb-3">
              <Form.Label>Upload GWAS summary statistics file</Form.Label>
              {typeof exampleFilename === "string" && exampleFilename !== "" ? (
                <div className="form-control bg-light">{exampleFilename}</div>
              ) : (
                <Form.Control 
                  type="file" 
                  disabled={heritabilityLoading}
                  {...fileRegistration}
                  style={{ maxWidth: "400px" }}
                  accept={sumstatsAccept}
                  title="Upload PLINK, REGENIE, SAIGE, or LDSC-ready GWAS sumstats"
                  onChange={async (e) => {
                    await fileRegistration.onChange(e);
                    const input = e.target as HTMLInputElement;
                    const file = input.files && input.files[0];
                    setHeritabilityResultRef(null);
                    if (file) {
                      const validFormat = await heritabilityForm.trigger("sumstatsFormat");
                      if (!validFormat) {
                        input.value = "";
                        heritabilityForm.setValue("file", undefined, { shouldValidate: true });
                        return;
                      }
                      await handleFileUpload(file, heritabilityForm.getValues("sumstatsFormat"));
                    }
                  }}
                />
              )}
              <div style={{ fontSize: '0.875rem', fontWeight: 'normal', maxWidth: 400 }}>Upload PLINK, REGENIE, SAIGE, or LDSC-ready summary statistics. Special characters will be removed automatically from the file name. Use only A-Z, 0-9, dots, hyphens, and underscores.</div>

              <div className="mt-2">
                <HoverUnderlineLink href="/help#LDscore">
                  Click here for sample format
                </HoverUnderlineLink>
              </div>
              {heritabilityForm.formState.errors?.file?.type !== "server" && (
                <Form.Text className="text-danger">{heritabilityForm.formState.errors?.file?.message}</Form.Text>
              )}
            </Form.Group>
            <Form.Group controlId="useEx" className="mb-3">
              <div className="mt-2">
                <Form.Check 
                  type="switch"
                  id="use-example-heritability"
                  label="Use example data"
                  checked={useExample}
                  disabled={heritabilityLoading}
                  onChange={async (e) => {
                    setUseExample(e.target.checked);
                    setHeritabilityResultRef(null);
                    if (e.target.checked) {
                      // Generate a new reference for example data
                      const newReference = generateReference();
                      setReference(newReference);
                          heritabilityForm.setValue("sumstatsFormat", "pre_munged");
                      setExampleFilename("");
                      setUploadedFilename("");
                      heritabilityForm.clearErrors("file");
                      try {
                        const response = await fetch("/LDlinkRestWeb/ldherit_example");
                        if (response.ok) {
                          const data = await response.json();
                          setExampleFilename(data.filenames || "");
                        } else {
                          setExampleFilename("");
                          console.error("Failed to fetch example data");
                        }
                      } catch (error) {
                        setExampleFilename("");
                        console.error("Error fetching example data:", error);
                      }
                    } else {
                      setExampleFilename("");
                      setUploadedFilename("");
                      setReference("");
                      heritabilityForm.setValue("sumstatsFormat", "");
                      //heritabilityForm.setValue("pop", null);
                    }
                  }}
                />
                {(exampleFilename || uploadedFilename) && (
                  <div className="mt-1" style={{ fontSize: "0.95em" }}>
                    <span style={{ fontWeight: 600 }}>Input file uploaded:</span><br />

                    <a
                      href={exampleFilename
                        ? `/LDlinkRestWeb/copy_and_download/${encodeURIComponent(exampleFilename)}`
                        : `/LDlinkRestWeb/tmp/uploads/${reference}/${encodeURIComponent(uploadedFilename)}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      download
                      style={{ textDecoration: 'underline', color: '#2a71a5' }}
                    >
                      {exampleFilename || uploadedFilename}
                    </a>
                    <div>
                      <span style={{ fontWeight: 600 }}>Selected format:</span> {sumstatsFormatLabels[heritabilityForm.getValues("sumstatsFormat")] || "Not selected"}
                    </div>
                    {!useExample && renameWarnings.length > 0 && (
                      <Alert variant="warning" className="mt-2">
                        {renameWarnings}
                      </Alert>
                    )}
                  </div>
                )}
              </div>
            </Form.Group>
          </Col>

          <Col s={12} sm={12} md={6} lg={4}>
            <Form.Group controlId="scale" className="mb-3">
              <Form.Label className="d-block">Scale</Form.Label>
              <ButtonGroup>
                <ToggleButton
                  id="radio-scale-observed"
                  title="Observed scale heritability"
                  type="radio"
                  variant="outline-primary"
                  disabled={heritabilityLoading}
                  {...heritabilityForm.register("scale")}
                  value="observed"
                  checked={selectedScale === "observed"}
                  onChange={() => {
                    heritabilityForm.setValue("scale", "observed");
                    heritabilityForm.setValue("samplePrev", "0.5");
                    heritabilityForm.setValue("popPrev", "0.01");
                    heritabilityForm.clearErrors(["samplePrev", "popPrev"]);
                  }}>
                  Observed
                </ToggleButton>
                <ToggleButton
                  id="radio-scale-liability"
                  title="Liability scale heritability"
                  type="radio"
                  variant="outline-primary"
                  disabled={heritabilityLoading}
                  {...heritabilityForm.register("scale")}
                  value="liability"
                  checked={selectedScale === "liability"}
                  onChange={() => {
                    heritabilityForm.setValue("scale", "liability");
                  }}>
                  Liability
                </ToggleButton>
              </ButtonGroup>
            </Form.Group>

            {selectedScale === "liability" && (
              <>
                <Row>
                  <Col md={6}>
                    <Form.Group controlId="samplePrev" className="mb-3">
                      <Form.Label>
                       Sample prevalence
                      </Form.Label>
                      <Form.Control
                        type="number"
                        step="0.01"
                        min={0}
                        max={1}
                        disabled={heritabilityLoading}
                        style={{ maxWidth: "160px" }}
                        placeholder="0.5"
                        {...heritabilityForm.register("samplePrev", {
                          required: "Sample prevalence is required for liability scale",
                          validate: (value) => {
                            const num = Number(value);
                            if (Number.isNaN(num)) return "Sample prevalence must be numeric";
                            return (num > 0 && num < 1) || "Sample prevalence must be between 0 and 1";
                          },
                        })}
                         title="Percentage (enter as 0–1)"
                      />
                      <Form.Text className="text-danger">{heritabilityForm.formState.errors?.samplePrev?.message}</Form.Text>
                    </Form.Group>
                  </Col>
                  <Col md={6}>
                    <Form.Group controlId="popPrev" className="mb-3">
                      <Form.Label>
                        Population prevalence
                      
                      </Form.Label>
                      <Form.Control
                        type="number"
                        step="0.01"
                        min={0}
                        max={1}
                        disabled={heritabilityLoading}
                        style={{ maxWidth: "160px" }}
                        placeholder="0.01"
                        {...heritabilityForm.register("popPrev", {
                          required: "Population prevalence is required for liability scale",
                          validate: (value) => {
                            const num = Number(value);
                            if (Number.isNaN(num)) return "Population prevalence must be numeric";
                            return (num > 0 && num < 1) || "Population prevalence must be between 0 and 1";
                          },
                        })}
                         title="Percentage (enter as 0–1)"
                      />
                      <Form.Text className="text-danger">{heritabilityForm.formState.errors?.popPrev?.message}</Form.Text>
                    </Form.Group>
                  </Col>
                </Row>
              </>
            )}
          </Col>

          <Col s={12} sm={12} md={6} lg={2}>
            <Form.Group controlId="pop" className="mb-3">
              <Form.Label>Population</Form.Label>
              <LdscorePopSelect name="pop" control={heritabilityForm.control} isLoading={heritabilityLoading} rules={{ required: "Population is required" }} />
              <Form.Text className="text-danger">{heritabilityForm.formState.errors?.pop?.message}</Form.Text>
            </Form.Group>
          </Col>

         <Col s={12} sm={12} md={12} lg={2}>
            <div className="text-end">
              <Button type="reset" variant="outline-danger" className="me-1" disabled={heritabilityLoading}>
                Reset
              </Button>
              <Button 
                type="submit" 
                variant={ "primary"}
                disabled={heritabilityMutation.isPending || heritabilityLoading}
              >
                {heritabilityLoading ? "Loading..." : "Calculate"}
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

        {heritabilityForm.formState.errors?.file?.type === "server" && heritabilityForm.formState.errors?.file?.message && (
          <Alert variant="danger" className="mt-2">
              The uploaded file has the following issues:<br />
            {heritabilityForm.formState.errors.file.message}
          </Alert>
      )}

      {heritabilityResultRef && (
           <>
         <hr />
        <LdScoreResults 
          reference={heritabilityResultRef} 
          type="heritability" 
          uploads={exampleFilename || uploadedFilename}
        />
        </>
      )}
    </>
  );
}
