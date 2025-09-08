import { LDproxyState } from "./LDproxy.state";
import { getOptionsFromKeys } from "../select/pop-select";

export function getInitialState(query: any): LDproxyState {
  // Helper to safely decode URI components; falls back to raw string on failure.
  const safeDecode = (val: string) => {
    if (typeof val !== "string") return "";
    try {
      return decodeURIComponent(val);
    } catch {
      return val; // If already decoded or malformed, just return original
    }
  };

  // Handle population list which may arrive URL-encoded with %2B ("+") separators, e.g. "CEU%2BTSI%2BFIN".
  // Support legacy comma-separated format as well. Filter out empties just in case.
  const popOptions = query.pop
    ? (() => {
        const normalized = safeDecode(query.pop)
          .replace(/,/g, "+") // support legacy commas
          .replace(/\++/g, "+") // collapse duplicate separators
          .replace(/^\+|\+$/g, ""); // trim leading/trailing plus
        return getOptionsFromKeys(normalized);
      })()
    : [{ value: "YRI", label: "(YRI) Yoruba in Ibadan, Nigeria" }];

  try {
    // Attach to global for manual inspection: window.__LDproxyPopOptions
    (globalThis as any).__LDproxyPopOptions = popOptions;
  } catch {
    /* ignore if not in a browser-like environment */
  }
  

  const initialState = {
    ...new LDproxyState(),
    var: query.var || "",
    pop: popOptions,
    r2_d: query.r2_d || "r2",
    genome_build: query.genome_build || "grch37",
    window: query.window || "500000",
    collapseTranscript: query.collapseTranscript === "true",
    annotate: query.annotate || "forge",
    showAllSNPs: query.showAllSNPs === "true",
    submitted: false,
  };

  // If a variant is provided in the query, mark the form as submitted
  // so the calculation runs automatically on page load.
  if (query.var) {
    initialState.submitted = true;
  }

  return initialState;
}
