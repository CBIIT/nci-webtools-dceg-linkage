import { PopOption } from "@/components/select/pop-select";

export interface LdmatrixFormData {
  snps: string;
  pop: string;
  reference: string;
  genome_build: string;
  r2_d: string
  collapseTranscript: boolean;
  annotate: string
}

export interface FormData {
  varFile?: FileList | string;
  snps: string;
  pop: PopOption[];
  reference: string;
  genome_build: string;
  r2_d: string
  collapseTranscript: boolean;
  annotate: string
}
