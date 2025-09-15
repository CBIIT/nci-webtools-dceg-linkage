"use client";
import { useForm } from "react-hook-form";
import { Row, Col, Form, Button, Alert } from "react-bootstrap";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter, usePathname } from "next/navigation";
import { fetchHeritabilityResult } from "@/services/queries";
import LdscorePopSelect, { LdscorePopOption } from "@/components/select/ldscore-pop-select";
import CalculateLoading from "@/components/calculateLoading";
import HoverUnderlineLink from "@/components/HoverUnderlineLink";
import { useStore } from "@/store";
import { useState } from "react";
import LdScoreResults from "./results";

interface HeritabilityFormData {
  file?: File;
  pop: LdscorePopOption | null;
}

export default function Heritability() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const pathname = usePathname();
  const { genome_build } = useStore((state) => state);
  
  const [exampleFilename, setExampleFilename] = useState<string>("");
  const [exampleFilepath, setExampleFilepath] = useState<string>("");
  const [uploadedFilename, setUploadedFilename] = useState<string>("");
  const [uploading, setUploading] = useState(false);
  const [useExample, setUseExample] = useState(false);
  const [heritabilityLoading, setHeritabilityLoading] = useState(false);
  const [heritabilityResultRef, setHeritabilityResultRef] = useState<string | null>(null);

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

  const heritabilityForm = useForm<HeritabilityFormData>({
    defaultValues: {
      file: undefined,
      pop: null
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
      await fetchHeritabilityResult(params);
      setHeritabilityResultRef(reference);
    } catch (error) {
      console.error("Heritability calculation error:", error);
    } finally {
      setHeritabilityLoading(false);
    }
  };

  const onHeritabilityReset = () => {
    heritabilityForm.reset();
    setHeritabilityResultRef(null);
    setExampleFilename("");
    setExampleFilepath("");
    setUploadedFilename("");
    setUseExample(false);
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
            <Form.Group controlId="file" className="mb-3">
              <Form.Label>Upload pre-munged GWAS sumstats file</Form.Label>
              {typeof exampleFilename === "string" && exampleFilename !== "" ? (
                <div className="form-control bg-light">{exampleFilename}</div>
              ) : (
                <Form.Control 
                  type="file" 
                   {...heritabilityForm.register("file", { 
                    required: "File is required",
                    validate: (file: File | File[] | FileList | undefined) => {
                      if (!file) return 'File is required';
                      // Handle FileList, File[], or single File
                      const f = Array.isArray(file) ? file[0] : (file instanceof FileList ? file[0] : file);
                      if (!f || !f.name) return 'File is required';
                      const ext = f.name.split('.').pop()?.toLowerCase();
                      return ext === 'txt' || 'Only .txt files are allowed';
                    }
                  })}
                  accept=".txt"
                  title="Upload pre-munged GWAS sumstats"
                  onChange={async (e) => {
                    const input = e.target as HTMLInputElement;
                    const file = input.files && input.files[0];
                    setHeritabilityResultRef(null);
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
                <HoverUnderlineLink href="/help#LDscore">
                  Click here for sample format
                </HoverUnderlineLink>
              </div>
              <Form.Text className="text-danger">{heritabilityForm.formState.errors?.file?.message}</Form.Text>
            </Form.Group>
            <Form.Group controlId="useEx" className="mb-3">
              <div className="mt-2">
                <Form.Check 
                  type="switch"
                  id="use-example-heritability"
                  label="Use example data"
                  checked={useExample}
                  onChange={async (e) => {
                    setUseExample(e.target.checked);
                    setHeritabilityResultRef(null);
                    if (e.target.checked) {
                      setExampleFilename("");
                      setExampleFilepath("");
                      setUploadedFilename("");
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
                      setUploadedFilename("");
                      //heritabilityForm.setValue("pop", null);
                    }
                  }}
                />
                {(exampleFilename || uploadedFilename) && (
                  <div className="mt-1" style={{ fontSize: "0.95em" }}>
                    <span style={{ fontWeight: 600 }}>Input file uploaded:{heritabilityResultRef}</span><br />

                    <a
                      href={exampleFilename
                        ? `/LDlinkRestWeb/copy_and_download/${heritabilityResultRef}/${encodeURIComponent(exampleFilename)}`
                        : `/LDlinkRestWeb/tmp/uploads/${heritabilityResultRef}/${encodeURIComponent(uploadedFilename)}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      download
                      style={{ textDecoration: 'underline', color: '#2a71a5' }}
                    >
                      {exampleFilename || uploadedFilename}
                    </a>
                  </div>
                )}
              </div>
            </Form.Group>
          </Col>

          <Col s={12} sm={12} md={6} lg={4}>
            <Form.Group controlId="pop" className="mb-3">
              <Form.Label>Population</Form.Label>
              <LdscorePopSelect name="pop" control={heritabilityForm.control} rules={{ required: "Population is required" }} />
              <Form.Text className="text-danger">{heritabilityForm.formState.errors?.pop?.message}</Form.Text>
            </Form.Group>
          </Col>

          <Col />
         <Col s={12} sm={12} md={5} lg={3} style={{ minWidth: "180px" }}>
            <div className="text-end">
              <Button type="reset" variant="outline-danger" className="me-1">
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
