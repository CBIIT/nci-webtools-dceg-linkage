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
  warning?: string;
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

// Types for LDpop map locations and aaData
export interface Rs1MapLocation {
  0: string; // population code
  1: string; // population name
  2: string; // super population
  3: number; // latitude
  4: number; // longitude
  5: string; // allele frequency
}

export interface Rs2MapLocation {
  0: string; // population code
  1: string; // population name
  2: string; // super population
  3: number; // latitude
  4: number; // longitude
  5: string; // allele frequency
}

export interface Rs1Rs2LDMapLocation {
  0: string; // population code
  1: string; // population name
  2: string; // super population
  3: number; // latitude
  4: number; // longitude
  5: string; // allele frequency 1
  6: string; // allele frequency 2
  7: number; // LD value 1 (R2)
  8: number; // LD value 2 (D')
}

export interface AaDataRow {
  0: string; // population code
  1: number; // count
  2: string; // allele frequency 1
  3: string; // allele frequency 2
  4: number; // LD value 1
  5: number; // LD value 2
  6: [string, string, string]; // rs1, rs2, population code
  7: number; // count * 2
  8: number; // always 0
}
