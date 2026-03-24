import { create } from "zustand";

export interface StoreState {
  genome_build: string;
  setGenomeBuild: (genome_build: string) => void;
  formDataCache: Record<string, any>;
  setFormData: (ref: string, data: any) => void;
  getFormData: (ref: string) => any;
  resetStore: () => void;
}

export const defaultState = {
  genome_build: "grch37",
  formDataCache: {},
};

export const useStore = create<StoreState>((set, get) => ({
  ...defaultState,
  setGenomeBuild: (genome_build: string) => set(() => ({ genome_build })),
  setFormData: (ref: string, data: any) => 
    set((state) => ({ 
      formDataCache: { ...state.formDataCache, [ref]: data } 
    })),
  getFormData: (ref: string) => get().formDataCache[ref],
  resetStore: () => set(() => defaultState),
}));

export const genomeBuildMap: Record<string, string> = {
    grch37: "GRCh37",
    grch38: "GRCh38",
    grch38_high_coverage: "GRCh38 High Coverage",
  };