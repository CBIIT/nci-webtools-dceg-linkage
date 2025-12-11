export type FormData = {
  snps: string;
  pop: string[];
  genome_build: string;
  varFile: string | FileList;
  reference?: number;
  platforms: string[];
};

export interface ResultsData {
  details: Record<string, string[]>;
  warnings: string[][];
  snp_list: string[];
  snps_ld_pruned?: string[];
}

export interface SnpChipData {
  snps: string;
  genome_build: string;
  reference: number;
  platforms: string[];
}

export interface Platform {
  id: string;
  name: string;
}