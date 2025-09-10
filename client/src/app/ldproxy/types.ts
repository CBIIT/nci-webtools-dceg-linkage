import { PopOption } from "@/components/select/pop-select";

export interface ResultsData {
  corr_alleles: string[];
  haplotypes: {
    [key: string]: {
      alleles: string;
      count: string;
      frequency: string;
    };
  };
  pair: [string, string];
  request: string;
  snp1: {
    allele_1: {
      allele: string;
      count: string;
      frequency: string;
    };
    allele_2: {
      allele: string;
      count: string;
      frequency: string;
    };
    coord: string;
    rsnum: string;
  };
  snp2: {
    allele_1: {
      allele: string;
      count: string;
      frequency: string;
    };
    allele_2: {
      allele: string;
      count: string;
      frequency: string;
    };
    coord: string;
    rsnum: string;
  };
  statistics: {
    chisq: string;
    d_prime: string;
    p: string;
    r2: string;
    reference: string;
  };
  two_by_two: {
    cells: {
      c11: string;
      c12: string;
      c21: string;
      c22: string;
    };
    total: string;
  };
  error?: string;
}

export interface SubmitFormData {
  var: string;
  pop: string;
  genome_build: string;
  r2_d: string;
  window: string;
  collapseTranscript: boolean;
  annotate: "forge" | "regulome" | "no";
  reference: string;
}

export interface FormData {
  var: string;
  pop: PopOption[];
  reference: string;
  genome_build: string;
  r2_d: string;
  window: string;
  collapseTranscript: boolean;
  annotate: "forge" | "regulome" | "no";
}
