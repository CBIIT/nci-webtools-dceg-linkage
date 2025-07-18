import { PopOption } from "@/components/select/pop-select";

export interface ResultsData {
  aaData: [
    string, // population code
    number, // count
    string, // allele frequency 1
    string, // allele frequency 2
    number, // LD value 1
    number, // LD value 2
    [string, string, string], // rs1, rs2, population code
    number, // count * 2
    number // always 0
  ][];
  inputs: {
    LD: string;
    rs1: string;
    rs2: string;
  };
  locations: {
    rs1_map: [
      string, // population code
      string, // population name
      string, // super population
      number, // value 1
      number, // value 2
      string // allele frequency
    ][];
    rs1_rs2_LD_map: [
      string, // population code
      string, // population name
      string, // super population
      number, // value 1
      number, // value 2
      string, // allele frequency 1
      string, // allele frequency 2
      number, // LD value 1
      number // LD value 2
    ][];
    rs2_map: [
      string, // population code
      string, // population name
      string, // super population
      number, // value 1
      number, // value 2
      string // allele frequency
    ][];
  };
  error?: string;
}

export interface submitFormData {
  var1: string;
  var2: string;
  pop: string;
  genome_build: string;
  reference: string;
  r2_d: string;
}

export interface FormData {
  var1: string;
  var2: string;
  pop: PopOption[];
  genome_build: string;
  r2_d: string;
}

export interface LdPop {
  reference: string;
}
