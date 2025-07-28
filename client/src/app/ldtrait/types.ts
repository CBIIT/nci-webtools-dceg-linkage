import { PopOption } from "@/components/select/pop-select";

export interface SNP {
  RS: string;
  Coord: string;
  Alleles: string;
}

export interface Haplotype {
  Count: number;
  Frequency: number;
  Haplotype: string;
}

export interface ResultsData {
  query_snps: Array<Array<string>>;
  thinned_snps: string[];
  details: {
    [key: string]: {
      aaData: Array<[
        string, // GWAS Trait
        string, // PMID
        string, // RS Number
        string, // Position
        string, // Alleles
        number, // R²
        number, // D'
        Array<string>, // LDpair link data
        string, // Risk Allele
        number | string, // Beta or OR
        string, // Effect Size
        string, // P-value
        string  // RS Number for link
      ]>;
    };
  };
  error?: string;
}


export interface FormData {
  snps: string;
  varFile?: string | FileList;
  pop: PopOption[];
  r2_d: "r2" | "d";
  r2_d_threshold: string;
  window: string;
  genome_build: string;
  ifContinue?: "Continue" | "False";
}

export interface LdtraitFormData {
  snps: string;
  pop: string;
  r2_d: "r2" | "d";
  r2_d_threshold: string;
  window: string;
  genome_build: string;
  reference: number;
  ifContinue: "Continue" | "False";
}

export interface Ldtrait {
  query_snps: string[];
  thinned_snps: string[];
  details: {
    [key: string]: {
      aaData: Array<any>;
    };
  };
  warning?: string;
  error?: string;
}

export interface Warning {
  rs_number: string;
  position: string;
  alleles: string;
  comment: string;
}
export interface Detail {
  rs_number: string;
  position: string;
  alleles: string;
  comment: string;
}