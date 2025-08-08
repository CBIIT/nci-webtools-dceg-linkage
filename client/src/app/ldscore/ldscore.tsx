"use client";
import { useForm } from "react-hook-form";
import { Row, Col, Form, Button, Alert } from "react-bootstrap";
import { fetchLdScoreCalculationResult } from "@/services/queries";
import CalculateLoading from "@/components/calculateLoading";
import HoverUnderlineLink from "@/components/HoverUnderlineLink";
import { useState } from "react";
import LdScoreResults from "./results";

interface FormData {
  ldfiles?: FileList;
  window: number;
  windowUnit: "kb" | "cM";
}

export default function LDScore() {
  // LD calculation form state
  const form = useForm<FormData>({
    defaultValues: {
      ldfiles: undefined,
      window: 1,
      windowUnit: "cM"
    }
  });

  // State for file uploads and examples
  const [exampleBed, setExampleBed] = useState<string>("");
  const [exampleBim, setExampleBim] = useState<string>("");
  const [exampleFam, setExampleFam] = useState<string>("");
  const [uploadedBed, setUploadedBed] = useState<string>("");
  const [uploadedBim, setUploadedBim] = useState<string>("");
  const [uploadedFam, setUploadedFam] = useState<string>("");
  const [useExampleLdscore, setUseExampleLdscore] = useState(false);
  const [ldscoreLoading, setLdscoreLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [ldscoreResultRef, setLdscoreResultRef] = useState<string | null>(null);
  const [error, setError] = useState<string>("");
  const [fileError, setFileError] = useState<string>("");

  // Upload handler for LD calculation multiple files (.bed, .bim, .fam)
  const handleLdFilesUpload = async (files: FileList) => {
    setUploading(true);
    setUploadedBed(""); 
    setUploadedBim(""); 
    setUploadedFam("");
    form.clearErrors("ldfiles");
    
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
        // ignore individual file upload errors
      }
    }
    setUploading(false);
  };

  const onSubmit = async () => {
    setError("");
    setLdscoreResultRef(null);
    
    const bed = exampleBed || uploadedBed;
    const bim = exampleBim || uploadedBim;
    const fam = exampleFam || uploadedFam;
    const window = form.getValues("window");
    const windowUnit = form.getValues("windowUnit");
    const isExample = !!exampleBed;
    const filename = `${bed};${bim};${fam}`;
    const reference = Math.floor(Math.random() * (99999 - 10000 + 1)).toString();
    
    const params = new URLSearchParams({
      filename,
      ldwindow: String(window),
      windUnit: String(windowUnit),
      isExample: isExample ? "true" : "false",
      reference,
    });
    
    try {
      setLdscoreLoading(true);
      await fetchLdScoreCalculationResult(params);
      setLdscoreResultRef(reference);
    } catch (error) {
      setError("Failed to process LD Score calculation. Please check your input and try again.");
    } finally {
      setLdscoreLoading(false);
    }
  };

  const onReset = () => {
    form.reset({
      ldfiles: undefined,
      window: 1,
      windowUnit: "cM"
    });
    setLdscoreResultRef(null);
    setExampleBed("");
    setExampleBim("");
    setExampleFam("");
    setUploadedBed("");
    setUploadedBim("");
    setUploadedFam("");
    setUseExampleLdscore(false);
    setError("");
    setFileError("");
  };

  return (
    <>
      {/* Show uploading overlay */}
      {uploading && (
        <div style={{ 
          position: 'fixed', 
          top: 0, 
          left: 0, 
          width: '100vw', 
          height: '100vh', 
          background: 'rgba(255,255,255,0.7)', 
          zIndex: 9999, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center' 
        }}>
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

      <Form id="ldscore-form-ld-calculation" onSubmit={form.handleSubmit(onSubmit)} onReset={onReset} noValidate>
        <Row>
          <Col sm={5}>
            <Form.Group controlId="ldfiles" className="mb-3">
              <Form.Label >Upload *.bed, *.bim, *.fam files (all three required)</Form.Label>
              {(exampleBed || exampleBim || exampleFam) ? (
                <div className="form-control bg-light">
                  {exampleBed && <div>{exampleBed}</div>}
                  {exampleBim && <div>{exampleBim}</div>}
                  {exampleFam && <div>{exampleFam}</div>}
                </div>
              ) : (
                <Form.Control
                  type="file"
                  {...form.register("ldfiles", { required: "Files are required" })}
                  accept=".bed,.bim,.fam"
                  multiple
                  title="Upload *.bed, *.bim, *.fam files"
                  onChange={async (e) => {
                    const input = e.target as HTMLInputElement;
                    if (input.files) {
                      // Validate file count and extensions
                      if (input.files.length !== 3) {
                        setFileError('Error: Upload must include 3 files, one of each type: .bed, .bim, and .fam');
                        input.value = ''; // Clear the input
                        return;
                      }

                      // Check if we have exactly one of each required file type
                      const extensions = Array.from(input.files).map(file => 
                        file.name.split('.').pop()?.toLowerCase()
                      );
                      const hasBed = extensions.includes('bed');
                      const hasBim = extensions.includes('bim');
                      const hasFam = extensions.includes('fam');

                      if (!hasBed || !hasBim || !hasFam) {
                        setFileError('Error: Upload must include 3 files, one of each type: .bed, .bim, and .fam');
                        input.value = ''; // Clear the input
                        return;
                      }

                      // Check for duplicates
                      const bedCount = extensions.filter(ext => ext === 'bed').length;
                      const bimCount = extensions.filter(ext => ext === 'bim').length;
                      const famCount = extensions.filter(ext => ext === 'fam').length;

                      if (bedCount !== 1 || bimCount !== 1 || famCount !== 1) {
                        setFileError('Error: Upload must include 3 files, one of each type: .bed, .bim, and .fam');
                        input.value = ''; // Clear the input
                        return;
                      }

                      setFileError(""); // Clear any previous errors
                      setLdscoreResultRef(null); // Reset LD score result when new files are loaded
                      handleLdFilesUpload(input.files);
                    }
                  }}
                />
              )}
               <div className="mt-2">
                <HoverUnderlineLink href="/help#LDscore">
                  Click here for sample format
                </HoverUnderlineLink>
              </div>
              <Form.Text className="text-danger">{form.formState.errors?.ldfiles?.message}</Form.Text>
            </Form.Group>
            
            <Form.Group controlId="useExLd" className="mb-3">
              <div className="mt-2">
                <Form.Check
                  type="switch"
                  id="use-example-ld"
                  label="Use example data"
                  checked={useExampleLdscore}
                  onChange={(e) => {
                    setUseExampleLdscore(e.target.checked);
                        setLdscoreResultRef(null);
                    if (e.target.checked) {
                      setExampleBed("22.bed");
                      setExampleBim("22.bim");
                      setExampleFam("22.fam");
                      setUploadedBed("");
                      setUploadedBim("");
                      setUploadedFam("");
                      form.clearErrors("ldfiles");
                    } else {
                      setExampleBed("");
                      setExampleBim("");
                      setExampleFam("");
                    }
                  }}
                />
                {(uploadedBed || uploadedBim || uploadedFam || exampleBed || exampleBim || exampleFam) && (
                  <div className="mt-1" style={{ fontSize: "0.95em" }}>
                    <span style={{ fontWeight: 600 }}>Input files uploaded:</span><br />
                    {(exampleBed || uploadedBed) && (
                      <div>
                        <a
                          href={exampleBed ? `/LDlinkRestWeb/copy_and_download/${encodeURIComponent(exampleBed)}` : `/LDlinkRestWeb/tmp/uploads/${encodeURIComponent(uploadedBed)}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          download
                          style={{ textDecoration: 'underline', color: '#2a71a5' }}
                        >
                          {exampleBed || uploadedBed}
                        </a>
                      </div>
                    )}
                    {(exampleBim || uploadedBim) && (
                      <div>
                        <a
                          href={exampleBim ? `/LDlinkRestWeb/copy_and_download/${encodeURIComponent(exampleBim)}` : `/LDlinkRestWeb/tmp/uploads/${encodeURIComponent(uploadedBim)}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          download
                          style={{ textDecoration: 'underline', color: '#2a71a5' }}
                        >
                          {exampleBim || uploadedBim}
                        </a>
                      </div>
                    )}
                    {(exampleFam || uploadedFam) && (
                      <div>
                        <a
                          href={exampleFam ? `/LDlinkRestWeb/copy_and_download/${encodeURIComponent(exampleFam)}` : `/LDlinkRestWeb/tmp/uploads/${encodeURIComponent(uploadedFam)}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          download
                          style={{ textDecoration: 'underline', color: '#2a71a5' }}
                        >
                          {exampleFam || uploadedFam}
                        </a>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </Form.Group>
          </Col>

          <Col sm={4}>
            <Form.Group controlId="window" className="mb-3">
              <Form.Label>Window</Form.Label>
              <div className="d-flex">
                <Form.Control
                  type="number"
                  {...form.register("window", { 
                    required: "Window is required",  
                    min: { value: 1, message: "Window must be an integer greater than 0" } 
                  })}
                  defaultValue={1}
                  style={{ maxWidth: "120px", marginRight: "8px" }}
                  title="Please enter an integer greater than 0"
                />
                <Form.Select
                  {...form.register("windowUnit")}
                  style={{ maxWidth: "80px" }}
                  defaultValue="cM"
                  title="Select unit for the window size"
                >
                  <option value="kb">kb</option>
                  <option value="cM">cM</option>
                </Form.Select>
              </div>
              <Form.Text className="text-danger">{form.formState.errors?.window?.message}</Form.Text>
            </Form.Group>
          </Col>
          
          <Col />
          
          <Col sm={2}>
            <div className="text-end">
              <Button type="reset" variant="outline-danger" className="me-1">
                Reset
              </Button>
              <Button type="submit" variant="primary" disabled={ldscoreLoading}>
                {ldscoreLoading ? "Loading..." : "Calculate"}
              </Button>
            </div>
          </Col>
        </Row>
      </Form>

      {fileError && (
        <Row>
          <Col>
            <Alert variant="danger" className="mt-3">
              {fileError}
            </Alert>
          </Col>
        </Row>
      )}

      {ldscoreLoading && (
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

      {/* Show results component if reference is available */}
     
      {ldscoreResultRef && (
        <>
         <hr />
        <LdScoreResults
          reference={ldscoreResultRef}
          type="ldscore"
          uploads={
            [exampleBed || uploadedBed, exampleBim || uploadedBim, exampleFam || uploadedFam].filter(Boolean).join(';')
          }
        />
        </>
      )}

      {error && (
        <Row>
          <Col>
            <Alert variant="danger" className="mt-3">
              <Alert.Heading>Error</Alert.Heading>
              <p>{error}</p>
            </Alert>
          </Col>
        </Row>
      )}
    </>
  );
}
