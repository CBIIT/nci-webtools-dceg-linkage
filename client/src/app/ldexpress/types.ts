import { PopOption } from "@/components/select/pop-select";

export interface LocusDetails {
  results: {
    aaData: string[][];
  };
  queryWarnings: {
    aaData: any[];
  };
}

export interface LocusData {
  query_snps: string[][];
  thinned_snps: string[];
  thinned_genes: string[];
  thinned_tissues: string[];
  details: LocusDetails;
  error?: string;
}

export interface FormData {
  snps: string;
  ldexpressFile?: FileList | string;
  pop: PopOption[];
  tissues: { value: string; label: string }[];
  r2_d: string;
  p_threshold: number;
  r2_d_threshold: number;
  window: number | string;
  genome_build: string;
}

export interface Ldexpress {
  reference: string;
}

export type LdexpressFormData = Omit<FormData, "pop" | "tissues"> & {
  reference: string;
  genome_build: string;
  pop: string;
  tissues: string;
};

export type Tissue = { tissueSiteDetailId: string; tissueSiteDetail: string };