import { PopOption } from "@/components/select/pop-select";

// Tuple type for snpclip detail data: [position, alleles, comment]
export type SnpClipDetailTuple = [string, string, string];

export interface ResultsData {
  details: Record<string, SnpClipDetailTuple>;
  warnings: string[][];
  snp_list: string[];
  snps_ld_pruned?: string[];
  warning?: string;
  error?: string;
}

export interface FormData {
  snps: string;
  pop: PopOption[];
  r2_threshold: string;
  maf_threshold: string;
  genome_build: string;
  varFile: string | FileList;
}

export interface SnpClipFormData {
  snps: string;
  pop: string;
  r2_threshold: string;
  maf_threshold: string;
  genome_build: string;
  reference: number;
}

export interface VariantDetails {
  rs_number: string;
  position: string;
  alleles: string;
  comment: string;
}

