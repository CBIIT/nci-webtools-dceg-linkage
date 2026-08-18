import { useState } from "react";
import { fetchLdScoreCalculationResult, fetchLdScoreRuns, upload, validateBfile, LdScoreRunSummary } from "@/services/queries";
import { generateReference } from "@/services/utils";

export interface LdScoreUploadState {
  uploading: boolean;
  computing: boolean;
  fileError: string;
  renameWarnings: string;
  reference: string;
  uploadedBed: string;
  uploadedBim: string;
  uploadedFam: string;
  allUploadedFiles: string[];
}

const initialState: LdScoreUploadState = {
  uploading: false,
  computing: false,
  fileError: "",
  renameWarnings: "",
  reference: "",
  uploadedBed: "",
  uploadedBim: "",
  uploadedFam: "",
  allUploadedFiles: [],
};

// Shared bed/bim/fam upload + validateBfile flow used by the LD Score Calculation tab
// and, inline, by Heritability/Genetic Correlation when the user chooses to compute a
// new custom LD score rather than reuse an existing one.
export function useLdScoreUpload() {
  const [state, setState] = useState<LdScoreUploadState>(initialState);

  const reset = () => setState(initialState);

  const uploadFiles = async (files: FileList) => {
    setState((prev) => ({
      ...prev,
      uploading: true,
      uploadedBed: "",
      uploadedBim: "",
      uploadedFam: "",
      allUploadedFiles: [],
      renameWarnings: "",
      fileError: "",
    }));

    const newReference = generateReference();

    const baseNames = new Set<string>();
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const lastDotIndex = file.name.lastIndexOf(".");
      const baseName = lastDotIndex > 0 ? file.name.substring(0, lastDotIndex) : file.name;
      baseNames.add(baseName);
    }

    if (baseNames.size > 1) {
      setState((prev) => ({
        ...prev,
        uploading: false,
        fileError: `All files must have the same base filename. Found: ${Array.from(baseNames).join(", ")}`,
      }));
      return null;
    }

    let uploadedBed = "";
    let uploadedBim = "";
    let uploadedFam = "";
    const uploadedFileNames: string[] = [];
    let renameWarnings = "";

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const ext = file.name.split(".").pop()?.toLowerCase();
      const formData = new FormData();
      formData.append("ldscoreFile", file);
      formData.append("reference", newReference);

      try {
        const response = await upload(formData);
        if (response && response.status === 200) {
          const data = response.data;
          let savedName = file.name;
          if (data?.renamed && Array.isArray(data.renamed) && data.renamed.length > 0) {
            const mapping = data.renamed[0];
            if (mapping.original !== mapping.sanitized) {
              renameWarnings = `File was renamed to ${mapping.sanitized}`;
            }
            savedName = mapping.sanitized;
          }
          uploadedFileNames.push(savedName);
          if (ext === "bed") uploadedBed = savedName;
          if (ext === "bim") uploadedBim = savedName;
          if (ext === "fam") uploadedFam = savedName;
        }
      } catch (e) {
        // ignore individual file upload errors
      }
    }

    setState((prev) => ({
      ...prev,
      reference: newReference,
      uploadedBed,
      uploadedBim,
      uploadedFam,
      allUploadedFiles: uploadedFileNames,
      renameWarnings,
    }));

    if (uploadedFileNames.length === 3) {
      const baseName = uploadedFileNames[0].substring(0, uploadedFileNames[0].lastIndexOf("."));
      try {
        const { fileValid } = await validateBfile(baseName, newReference);
        if (!fileValid.valid) {
          const errorMessages = fileValid.errors || [];
          const warningMessages = fileValid.warnings || [];
          const allMessages = [...errorMessages, ...warningMessages];
          const errorText = allMessages.length > 0 ? allMessages.join("\n") : "Invalid bfile format. Please check your files.";
          setState((prev) => ({
            ...prev,
            uploading: false,
            fileError: errorText,
            uploadedBed: "",
            uploadedBim: "",
            uploadedFam: "",
            allUploadedFiles: [],
          }));
          return null;
        }
      } catch (e) {
        setState((prev) => ({ ...prev, uploading: false, fileError: "Failed to validate files. Please try again." }));
        return null;
      }
    }

    setState((prev) => ({ ...prev, uploading: false }));
    return { reference: newReference, uploadedBed, uploadedBim, uploadedFam };
  };

  const computeLdScore = async (
    uploadResult: { reference: string; uploadedBed: string; uploadedBim: string; uploadedFam: string }
  ): Promise<LdScoreRunSummary | null> => {
    setState((prev) => ({ ...prev, computing: true, fileError: "" }));
    try {
      const filename = `${uploadResult.uploadedBed},${uploadResult.uploadedBim},${uploadResult.uploadedFam}`;
      const params = new URLSearchParams({
        filename,
        ldwindow: "1",
        windUnit: "cM",
        isExample: "false",
        reference: uploadResult.reference,
      });
      await fetchLdScoreCalculationResult(params);
      const { runs } = await fetchLdScoreRuns();
      const computedRun = runs.find((run) => run.reference === uploadResult.reference) || null;
      if (!computedRun) {
        setState((prev) => ({ ...prev, fileError: "LD score was computed but could not be found for reuse. Please try again." }));
      }
      return computedRun;
    } catch (e) {
      setState((prev) => ({ ...prev, fileError: "Failed to compute LD score from the uploaded files." }));
      return null;
    } finally {
      setState((prev) => ({ ...prev, computing: false }));
    }
  };

  return { ...state, uploadFiles, computeLdScore, reset };
}
