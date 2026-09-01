import { useState } from "react";
import { fetchLdScoreCalculationResult, fetchLdScoreRuns, importLdScoreRun, upload, validateBfile, LdScoreRunSummary } from "@/services/queries";
import { generateReference } from "@/services/utils";

const LDSCORE_OUTPUT_SUFFIX = ".l2.ldscore.gz";

export interface LdScoreUploadState {
  uploading: boolean;
  computing: boolean;
  importing: boolean;
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
  importing: false,
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

  // Registers an already-computed LD score output directly, skipping the bed/bim/fam
  // upload + compute step, for callers who already have LDSC output (e.g. from a
  // prior run outside this tool) they want to reuse. Requires all three matching
  // files -- .l2.M/.l2.M_5_50 can't be reliably derived from .l2.ldscore.gz alone, and
  // a wrong SNP count would silently bias the downstream heritability/genetic
  // correlation regression -- see server/ldscore_compatibility.validate_ldscore_import_files.
  const importPrecomputedLdScore = async (files: FileList, genomeBuild: string): Promise<LdScoreRunSummary | null> => {
    const requiredSuffixes = [LDSCORE_OUTPUT_SUFFIX, ".l2.M", ".l2.M_5_50"];
    const fileList = Array.from(files);

    if (fileList.length !== requiredSuffixes.length) {
      setState((prev) => ({ ...prev, fileError: `Select all 3 matching files: *${requiredSuffixes.join(", *")}` }));
      return null;
    }

    const fileBySuffix = new Map<string, File>();
    for (const suffix of requiredSuffixes) {
      const match = fileList.find((file) => file.name.toLowerCase().endsWith(suffix.toLowerCase()));
      if (match) fileBySuffix.set(suffix, match);
    }
    if (fileBySuffix.size !== requiredSuffixes.length) {
      setState((prev) => ({ ...prev, fileError: `Select all 3 matching files: *${requiredSuffixes.join(", *")}` }));
      return null;
    }

    const ldscoreFile = fileBySuffix.get(LDSCORE_OUTPUT_SUFFIX)!;
    const fileroot = ldscoreFile.name.slice(0, -LDSCORE_OUTPUT_SUFFIX.length);
    const mismatched = requiredSuffixes.some((suffix) => fileBySuffix.get(suffix)!.name.slice(0, -suffix.length) !== fileroot);
    if (mismatched) {
      setState((prev) => ({ ...prev, fileError: "All 3 files must share the same base filename." }));
      return null;
    }

    setState((prev) => ({ ...prev, uploading: true, importing: true, fileError: "" }));
    const newReference = generateReference();

    try {
      let ldscoreFilename = ldscoreFile.name;
      for (const suffix of requiredSuffixes) {
        const file = fileBySuffix.get(suffix)!;
        const formData = new FormData();
        formData.append("ldscoreFile", file);
        formData.append("reference", newReference);

        const uploadResponse = await upload(formData);
        if (!uploadResponse || uploadResponse.status !== 200) {
          setState((prev) => ({ ...prev, fileError: `Failed to upload ${file.name}.` }));
          return null;
        }

        if (suffix === LDSCORE_OUTPUT_SUFFIX) {
          const renamed = uploadResponse.data?.renamed;
          if (Array.isArray(renamed) && renamed.length > 0 && renamed[0].original !== renamed[0].sanitized) {
            ldscoreFilename = renamed[0].sanitized;
          }
        }
      }

      const params = new URLSearchParams({
        reference: newReference,
        filename: ldscoreFilename,
        genome_build: genomeBuild,
      });
      const { run } = await importLdScoreRun(params);
      setState((prev) => ({ ...prev, reference: newReference }));
      return run;
    } catch (e: any) {
      const message = e?.response?.data?.error || "Failed to import the LD score files.";
      setState((prev) => ({ ...prev, fileError: message }));
      return null;
    } finally {
      setState((prev) => ({ ...prev, uploading: false, importing: false }));
    }
  };

  return { ...state, uploadFiles, computeLdScore, importPrecomputedLdScore, reset };
}
