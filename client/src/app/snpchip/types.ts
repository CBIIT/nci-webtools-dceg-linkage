export type FormData = {
  snps: string;
  pop: string[];
  genome_build: string;
  varFile: string | FileList;
  reference?: number;
  platforms: string[];
};

export type ResultData = {
  // Define result data structure here
  [key: string]: any;
};
