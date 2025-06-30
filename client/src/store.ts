import { create } from "zustand";

export interface StoreState {
  genome_build: string;
  setGenomeBuild: (genome_build: string) => void;
  resetStore: () => void;
}

export const defaultState = {
  genome_build: "grch37",
};

export const useStore = create<StoreState>((set) => ({
  ...defaultState,
  setGenomeBuild: (genome_build: string) => set(() => ({ genome_build })),
  resetStore: () => set(() => defaultState),
}));
