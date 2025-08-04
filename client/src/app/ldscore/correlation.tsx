"use client";
import { useForm } from "react-hook-form";
import { Row, Col, Form, Button, Alert } from "react-bootstrap";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter, usePathname } from "next/navigation";
import { fetchGeneticCorrelationResult } from "@/services/queries";
import LdscorePopSelect, { LdscorePopOption } from "@/components/select/ldscore-pop-select";
import CalculateLoading from "@/components/calculateLoading";
import { useStore } from "@/store";
import { useState } from "react";
import LdScoreResults from "./results";

interface CorrelationFormData {
  file?: File;
  file2?: File;
  pop: LdscorePopOption | null;
}

export default function Correlation() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const pathname = usePathname();
  const { genome_build } = useStore((state) => state);
  
  const [exampleFile1, setExampleFile1] = useState<string>("");
  const [exampleFile2, setExampleFile2] = useState<string>("");
  const [uploadedFile1, setUploadedFile1] = useState<string>("");
  const [uploadedFile2, setUploadedFile2] = useState<string>("");
  const [uploading, setUploading] = useState(false);
  const [useExampleCorrelation, setUseExampleCorrelation] = useState(false);
  const [geneticLoading, setGeneticLoading] = useState(false);
  const [geneticCorrelationResultRef, setGeneticCorrelationResultRef] = useState<string | null>(null);

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
        return file.name;
      } else {
        return "";
      }
    } catch (e) {
      return "";
    } finally {
      setUploading(false);
    }
  };

  const geneticForm = useForm<CorrelationFormData>({
    defaultValues: {
      file: undefined,
      file2: undefined,
      pop: null
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
    setGeneticCorrelationResultRef(null);
    setGeneticLoading(true);
    const pop = data.pop?.value || '';
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
    setExampleFile1("");
    setExampleFile2("");
    setUploadedFile1("");
    setUploadedFile2("");
    setUseExampleCorrelation(false);
    geneticForm.setValue("pop", null);
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
            <CalculateLoading />
          </div>
        </div>
      )}

      <Form id="correlation-form" onSubmit={geneticForm.handleSubmit(onGeneticSubmit)} onReset={onGeneticReset} noValidate>
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
                    setGeneticCorrelationResultRef(null);
                    if (file) {
                      const filename = await handleFileUpload(file);
                      setUploadedFile1(filename);
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
                    setGeneticCorrelationResultRef(null);
                    if (file) {
                      const filename = await handleFileUpload(file);
                      setUploadedFile2(filename);
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
                checked={useExampleCorrelation}
                onChange={(e) => {
                  setUseExampleCorrelation(e.target.checked);
                  if (e.target.checked) {
                    setExampleFile1("BBJ_HDLC22.txt");
                    setExampleFile2("BBJ_LDLC22.txt");
                    setUploadedFile1("");
                    setUploadedFile2("");
                  } else {
                    setExampleFile1("");
                    setExampleFile2("");
                    geneticForm.setValue("pop", null);
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

      {geneticCorrelationResultRef && (
        <LdScoreResults
          reference={geneticCorrelationResultRef}
          type="correlation"
          uploads={
            [exampleFile1 || uploadedFile1, exampleFile2 || uploadedFile2].filter(Boolean).join(',')
          }
        />
      )}
    </>
  );
}
