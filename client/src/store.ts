import { create } from "zustand";
import type { LdScoreRunSummary } from "@/services/queries";

export interface StoreState {
  genome_build: string;
  setGenomeBuild: (genome_build: string) => void;
  formDataCache: Record<string, any>;
  setFormData: (ref: string, data: any) => void;
  getFormData: (ref: string) => any;
  // LD score runs computed earlier in this page visit (LD Score Calculation tab),
  // available instantly to Heritability/Genetic Correlation without a network round-trip.
  ldScoreRuns: LdScoreRunSummary[];
  addLdScoreRun: (run: LdScoreRunSummary) => void;
  resetStore: () => void;
}

export const defaultState = {
  genome_build: "grch37",
  formDataCache: {},
  ldScoreRuns: [] as LdScoreRunSummary[],
};

export const useStore = create<StoreState>((set, get) => ({
  ...defaultState,
  setGenomeBuild: (genome_build: string) => set(() => ({ genome_build })),
  setFormData: (ref: string, data: any) => 
    set((state) => ({ 
      formDataCache: { ...state.formDataCache, [ref]: data } 
    })),
  getFormData: (ref: string) => get().formDataCache[ref],
  addLdScoreRun: (run: LdScoreRunSummary) =>
    set((state) => ({
      ldScoreRuns: [run, ...state.ldScoreRuns.filter((existing) => existing.reference !== run.reference)],
    })),
  resetStore: () => set(() => defaultState),
}));

export const genomeBuildMap: Record<string, string> = {
    grch37: "GRCh37",
    grch38: "GRCh38",
    grch38_high_coverage: "GRCh38 High Coverage",
  };