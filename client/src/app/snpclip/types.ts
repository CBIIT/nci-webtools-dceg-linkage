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
}

export interface SNPChipFormData {
  snps: string;
  pop: string;
  genome_build: string;
  reference: string;
}

export interface FormData {
  snps: string;
  pop: PopOption[];
  genome_build: string;
  varFile?: FileList | string;
}

export interface SNPChip {
  reference: string;
}

