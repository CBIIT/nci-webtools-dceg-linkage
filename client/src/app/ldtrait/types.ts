import { PopOption } from "@/components/select/pop-select";

// Better typed tuple for GWAS trait data
export type GwasTraitData = [
  string,          // GWAS Trait
  string,          // PMID
  string,          // RS Number
  string,          // Position
  string,          // Alleles
  number,          // R²
  number,          // D'
  string[],        // LDpair link data
  string,          // Risk Allele
  number | string, // Beta or OR
  string,          // Effect Size
  string,          // P-value
  string           // RS Number for link
];

export interface ResultsData {
  query_snps: string[][];
  thinned_snps: string[];
  details: {
    [key: string]: {
      aaData: GwasTraitData[];
    };
  } & {
    queryWarnings?: {
      aaData: string[][];
    };
  };
  error?: string;
  warning?: string;
}

export interface FormData {
  snps: string;
  varFile?: string | FileList;
  pop: PopOption[];
  r2_d: "r2" | "d";
  r2_d_threshold: string;
  window: string;
  genome_build: string;
  reference: string;
  ifContinue?: "Continue" | "False";
}

export interface submitFormData {
  snps: string;
  pop: string;
  r2_d: "r2" | "d";
  r2_d_threshold: string;
  window: string;
  genome_build: string;
  reference: string;
  ifContinue: "Continue" | "False";
}

export interface Ldtrait {
  query_snps: string[];
  thinned_snps: string[];
  details: {
    [key: string]: {
      aaData: GwasTraitData[];
    };
  } & {
    queryWarnings?: {
      aaData: string[][];
    };
  };
  warning?: string;
  error?: string;
}