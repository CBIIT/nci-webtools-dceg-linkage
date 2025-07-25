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
  snps: Record<string, SNP>;
  haplotypes: Record<string, Haplotype>;
  error?: string;
}

export interface LdhapFormData {
  snps: string;
  pop: string;
  genome_build: string;
  reference: string;
}

export interface FormData {
  snps: string;
  varFile?: string | FileList;
  pop: PopOption[];
  r2_d: "r2" | "d";
  r2_d_threshold: string;
  window: string;
  genome_build: string;
}

export interface LdtraitFormData {
  snps: string;
  pop: string;
  r2_d: "r2" | "d";
  r2_d_threshold: string;
  window: string;
  genome_build: string;
  reference: string;
  ifContinue?: string;
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
