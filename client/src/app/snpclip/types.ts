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
  details: string[];
  warnings: string[];
  snps_ld_pruned: string[];
}

export interface FormData {
  snps: string;
  pop: PopOption[];
  r2_threshold: string;
  maf_threshold: string;
  genome_build: string;
  varFile: string | FileList;
}

export interface SnpClipData {
  snps: string;
  pop: string;
  r2_threshold: string;
  maf_threshold: string;
  genome_build: string;
  reference: number;
}

export interface Detail {
  rs_number: string;
  position: string;
  alleles: string;
  comment: string;
}

export interface Warning {
  rs_number: string;
  position: string;
  alleles: string;
  comment: string;
}

