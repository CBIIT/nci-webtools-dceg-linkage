"use client";
import { useForm } from "react-hook-form";
import { Row, Col, Form, Button, Alert } from "react-bootstrap";
import { fetchLdScoreCalculationResult, upload, validateBfile } from "@/services/queries";
import CalculateLoading from "@/components/calculateLoading";
import HoverUnderlineLink from "@/components/HoverUnderlineLink";
import { useState } from "react";
import LdScoreResults from "./results";
import { map } from "@bokeh/bokehjs/build/js/lib/core/util/iterator";

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
  const [allUploadedFiles, setAllUploadedFiles] = useState<string[]>([]);
  const [useExampleLdscore, setUseExampleLdscore] = useState(false);
  const [ldscoreLoading, setLdscoreLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [ldscoreResultRef, setLdscoreResultRef] = useState<string | null>(null);
  const [error, setError] = useState<string>("");
  const [fileError, setFileError] = useState<string>("");
  const [reference, setReference] = useState<string>("");
  const [renameWarnings, setRenameWarnings] = useState<string>("");

  // Upload handler for LD calculation multiple files (.bed, .bim, .fam)
  const handleLdFilesUpload = async (files: FileList) => {
    setUploading(true);
    setUploadedBed(""); 
    setUploadedBim(""); 
    setUploadedFam("");
    setAllUploadedFiles([]);
    setRenameWarnings("");
    form.clearErrors("ldfiles");
    setError(""); // Clear any previous errors
    
    // Generate a new reference for this upload session
    const newReference = Math.floor(Math.random() * (99999 - 10000 + 1)).toString();
    setReference(newReference);
    
    // Validate that all files have the same base name (excluding extension)
    const baseNames = new Set<string>();
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const lastDotIndex = file.name.lastIndexOf('.');
      const baseName = lastDotIndex > 0 ? file.name.substring(0, lastDotIndex) : file.name;
      baseNames.add(baseName);
    }
    
    if (baseNames.size > 1) {
      setFileError(`All files must have the same base filename. Found: ${Array.from(baseNames).join(', ')}`);
      setUploading(false);
      return;
    }
    
    const uploadedFileNames: string[] = [];
    
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const ext = file.name.split('.').pop()?.toLowerCase();
      const formData = new FormData();
      formData.append("ldscoreFile", file);
      formData.append("reference", newReference);
      
      try {
        const response = await upload(formData);
        if (response && response.status === 200) {
          const data = response.data;
          // If server returned a renamed mapping, surface it as a user warning
          if (data && data.renamed) {
            if (Array.isArray(data.renamed) && data.renamed.length > 0) {
              const mapping = data.renamed[0];
              if(mapping.original !== mapping.sanitized)
                setRenameWarnings(`File was renamed to ${mapping.sanitized}`);
              uploadedFileNames.push(mapping.sanitized);
          // Keep the specific type tracking for the submission logic
              if (ext === 'bed') setUploadedBed(mapping.sanitized);
              if (ext === 'bim') setUploadedBim(mapping.sanitized);
              if (ext === 'fam') setUploadedFam(mapping.sanitized);
            }
         
          }
          else{
            uploadedFileNames.push(file.name);
            // Keep the specific type tracking for the submission logic
            if (ext === 'bed') setUploadedBed(file.name);
            if (ext === 'bim') setUploadedBim(file.name);
            if (ext === 'fam') setUploadedFam(file.name);
          }
        
        }
      } catch (e) {
        // ignore individual file upload errors
      }
    }
    
    setAllUploadedFiles(uploadedFileNames);
    
    // Validate the uploaded bfile
    if (uploadedFileNames.length === 3) {
      const baseName = uploadedFileNames[0].substring(0, uploadedFileNames[0].lastIndexOf('.'));
      try {
        const { fileValid } = await validateBfile(baseName, newReference);
               
        if (!fileValid.valid) {
          const errorMessages = fileValid.errors || [];
          const warningMessages = fileValid.warnings || [];
          const allMessages = [...errorMessages, ...warningMessages];
          const errorText = allMessages.length > 0 
            ? allMessages.join('\n') 
            : "Invalid bfile format. Please check your files.";
          
          setFileError(errorText);
          setUploadedBed("");
          setUploadedBim("");
          setUploadedFam("");
          setAllUploadedFiles([]);
        }
      } catch (e) {
        console.error("Validation error:", e);
        setFileError("Failed to validate files. Please try again.");
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
    
    // Validate that all three files are present
    if (!bed || !bim || !fam) {
      form.setError("ldfiles", {
        type: "manual",
        message: "Upload must include 3 files, one of each type: .bed, .bim, and .fam"
      });
      return;
    }
    
    const window = form.getValues("window");
    const windowUnit = form.getValues("windowUnit");
    const isExample = !!exampleBed;
    const filename = `${bed};${bim};${fam}`;
  
    
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
    setAllUploadedFiles([]);
    setUseExampleLdscore(false);
    setReference("");
    setError("");
    setFileError("");
    setRenameWarnings("");
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
           <Col s={12} sm={12} md={6} lg={4}>
            <Form.Group controlId="ldfiles" className="mb-3">
              <Form.Label>
                <div>Upload *.bed, *.bim, *.fam files</div>
                <div style={{ fontSize: '0.875rem', fontWeight: 'normal' }}>(all three required and must have the same name)</div>
                <div style={{ fontSize: '0.875rem', fontWeight: 'normal' }}>Special characters will be removed automatically, Use: A-Z, 0-9, dots, hyphens, and underscores only</div>
              </Form.Label>
              {(exampleBed || exampleBim || exampleFam) ? (
                <div className="form-control bg-light">
                  {exampleBed && <div>{exampleBed}</div>}
                  {exampleBim && <div>{exampleBim}</div>}
                  {exampleFam && <div>{exampleFam}</div>}
                </div>
              ) : (
                <Form.Control
                  type="file"
                  {...form.register("ldfiles", { 
                    required: "Files are required",
                    validate: (fileList: FileList | undefined) => {
                      if (!fileList || fileList.length === 0) return true;
                      
                      // Validate file count
                      if (fileList.length !== 3) {
                        return 'Upload must include 3 files, one of each type: .bed, .bim, and .fam';
                      }

                      // Check if we have exactly one of each required file type
                      const extensions = Array.from(fileList).map(file => 
                        file.name.split('.').pop()?.toLowerCase()
                      );
                      const hasBed = extensions.includes('bed');
                      const hasBim = extensions.includes('bim');
                      const hasFam = extensions.includes('fam');

                      if (!hasBed || !hasBim || !hasFam) {
                        return 'Upload must include 3 files, one of each type: .bed, .bim, and .fam';
                      }

                      // Check for duplicates
                      const bedCount = extensions.filter(ext => ext === 'bed').length;
                      const bimCount = extensions.filter(ext => ext === 'bim').length;
                      const famCount = extensions.filter(ext => ext === 'fam').length;

                      if (bedCount !== 1 || bimCount !== 1 || famCount !== 1) {
                        return 'Upload must include 3 files, one of each type: .bed, .bim, and .fam';
                      }

                      return true;
                    }
                  })}
                  accept=".bed,.bim,.fam"
                  multiple
                  disabled={ldscoreLoading}
                  title="Upload *.bed, *.bim, *.fam files"
                  onChange={async (e) => {
                    const input = e.target as HTMLInputElement;
                    if (input.files) {
                      setFileError(""); // Clear any previous errors
                      setLdscoreResultRef(null); // Reset LD score result when new files are loaded
                      handleLdFilesUpload(input.files);
                    }
                  }}
                />
              )}
               <Form.Text className="text-danger">{form.formState.errors?.ldfiles?.message}</Form.Text>

               <div className="mt-2">
                <HoverUnderlineLink href="/help#LDscore">
                  Click here for sample format
                </HoverUnderlineLink>
              </div>
             
            </Form.Group>
            
            <Form.Group controlId="useExLd" className="mb-3">
              <div className="mt-2">
                <Form.Check
                  type="switch"
                  id="use-example-ld"
                  label="Use example data"
                  checked={useExampleLdscore}
                  disabled={ldscoreLoading}
                  onChange={(e) => {
                    setUseExampleLdscore(e.target.checked);
                        setLdscoreResultRef(null);
                    if (e.target.checked) {
                      // Generate a new reference for example data
                      const newReference = Math.floor(Math.random() * (99999 - 10000 + 1)).toString();
                      setReference(newReference);
                      setExampleBed("22.bed");
                      setExampleBim("22.bim");
                      setExampleFam("22.fam");
                      setUploadedBed("");
                      setUploadedBim("");
                      setUploadedFam("");
                      setAllUploadedFiles([]);
                      form.clearErrors("ldfiles");
                      setError(""); // Clear any previous errors
                      setFileError(""); // Clear file validation errors
                    } else {
                      setExampleBed("");
                      setExampleBim("");
                      setExampleFam("");
                      setReference("");
                      setError(""); // Clear any previous errors
                      setFileError(""); // Clear file validation errors
                    }
                  }}
                />
                {((allUploadedFiles.length > 0) || (exampleBed || exampleBim || exampleFam)) && (
                  <div className="mt-1" style={{ fontSize: "0.95em" }}>
                    <span style={{ fontWeight: 600 }}>Input files uploaded:</span><br />
                    {/* Show example files when using example data */}
                    {useExampleLdscore && (
                      <>
                        {exampleBed && (
                          <div>
                            <a
                              href={`/LDlinkRestWeb/copy_and_download/${encodeURIComponent(exampleBed)}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              download
                              style={{ textDecoration: 'underline', color: '#2a71a5' }}
                            >
                              {exampleBed}
                            </a>
                          </div>
                        )}
                        {exampleBim && (
                          <div>
                            <a
                              href={`/LDlinkRestWeb/copy_and_download/${encodeURIComponent(exampleBim)}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              download
                              style={{ textDecoration: 'underline', color: '#2a71a5' }}
                            >
                              {exampleBim}
                            </a>
                          </div>
                        )}
                        {exampleFam && (
                          <div>
                            <a
                              href={`/LDlinkRestWeb/copy_and_download/${encodeURIComponent(exampleFam)}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              download
                              style={{ textDecoration: 'underline', color: '#2a71a5' }}
                            >
                              {exampleFam}
                            </a>
                          </div>
                        )}
                      </>
                    )}
                    {/* Show all uploaded files */}
                    {!useExampleLdscore && allUploadedFiles.map((fileName, index) => (
                      <div key={index}>
                        <a
                          href={`/LDlinkRestWeb/tmp/uploads/${encodeURIComponent(fileName)}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          download
                          style={{ textDecoration: 'underline', color: '#2a71a5' }}
                        >
                          {fileName}
                        </a>
                      </div>
                    ))}
                    {!useExampleLdscore && renameWarnings.length > 0 && (
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
            <Form.Group controlId="window" className="mb-3">
              <Form.Label>Window</Form.Label>
              <div className="d-flex">
                <Form.Control
                  type="number"
                  {...form.register("window", { 
                    required: "Window is required",  
                    min: { value: 1, message: "Window must be an integer greater than 0" },
                    validate: (value) => {
                      const num = Number(value);
                      if (!Number.isInteger(num)) {
                        return "Window must be an integer greater than 0";
                      }
                      return true;
                    }
                  })}
                  defaultValue={1}
                  style={{ maxWidth: "120px", marginRight: "8px" }}
                  title="Please enter an integer greater than 0"
                  disabled={ldscoreLoading}
                />
                <Form.Select
                  {...form.register("windowUnit")}
                  style={{ maxWidth: "80px" }}
                  disabled={ldscoreLoading}
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
          
          <Col s={12} sm={12} md={6} lg={3} style={{ minWidth: "180px" }}>
            <div className="text-end">
              <Button type="reset" variant="outline-danger" className="me-1" disabled={ldscoreLoading}>
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
                <Alert variant="danger" className="mt-2">
                  {fileError}
                </Alert>
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
