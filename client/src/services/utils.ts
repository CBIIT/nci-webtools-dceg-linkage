import { populations } from "@/components/select/pop-select";
import { AxiosError } from "axios";

export const rsChrRegex = /^\s*(?:[rR][sS]\d+|[cC][hH][rR](?:[xXyY]|\d+)?(?::\d+))\s*$/;

export const rsChrMultilineRegex = /^(?:\s*(?:[rR][sS]\d+|[cC][hH][rR](?:[xXyY]|\d+)?(?::\d+))\s*)(?:\r?\n(?:\s*(?:[rR][sS]\d+|[cC][hH][rR](?:[xXyY]|\d+)?(?::\d+))\s*))*$/;

export function parseSnps(text: string): string {
  const lines = text.split("\n");
  const snps = lines
    .map((line) => {
      const snp = line.trim();
      if (rsChrRegex.test(snp)) {
        return snp;
      }
      return null;
    })
    .filter(Boolean)
    .join("\n");
  return snps;
}

// Helper function to extract rate limit info from HTML error response
export function parseRateLimitError(error: AxiosError): string {
  if (error.response?.status === 429 && typeof error.response.data === 'string') {
    const htmlData = error.response.data;
    
    // Extract the rate limit details from the <p> tag
    const pMatch = htmlData.match(/<p>(.*?)<\/p>/i);
    const rateLimitInfo = pMatch ? pMatch[1].trim() : '';
    
    if (rateLimitInfo) {
      return `Too many requests. Rate limit: ${rateLimitInfo}. Please try again later.`;
    }
  }
  return "Too many requests. Please try again later.";
}


// Minimal local types used by utils (keep narrow and safe)
export interface Tissue {
  tissueSiteDetailId: string;
  tissueSiteDetail: string;
  [k: string]: any;
}

export interface LdexpressTissues {
  tissueInfo: Tissue[];
}

/**
 * Convert a `tissue` param ("all" or plus-separated ids) together with
 * the API response `tissues` into an array of select option objects or the
 * join-string used by the backend.
 *
 * Returns an array of { value, label } objects suitable for react-select.
 */
export function getTissueOptionsFromKeys(tissue: string | undefined, tissues?: LdexpressTissues | null) {
  // defensive: when tissues are not available yet, return empty array
  if (!tissues || !Array.isArray(tissues.tissueInfo) || tissues.tissueInfo.length === 0) return [];

  // tissue may be 'all' or a plus-separated string like 't1+t2'
  if (tissue?.toLocaleLowerCase() === "all") {
    return [{ value: "all", label: "All Tissues" }];
  }

  // Accept plus-separated codes, but be robust to other separators or URL-encoded values
  const raw = typeof tissue === "string" ? tissue.trim() : "";
  // split on plus signs, commas, or whitespace so 'Adrenal_Gland+Artery_Aorta' or
  // 'Adrenal_Gland Artery_Aorta' both produce separate codes
  const splitCodes = raw === "" ? [] : raw.split(/[+,\s]+/).map((s) => s.trim()).filter(Boolean);

  // Map codes to matching tissue objects; fall back to returning code as label when not found
  const options = splitCodes
    .map((code) => {
      // decode any URL-encoded sequences and normalize underscores
      const decoded = decodeURIComponent(code);
      const normalized = decoded.replace(/\s+/g, " ").replace(/_/g, " ").trim();

      // try exact id match first
      const match = tissues.tissueInfo.find((t) => t.tissueSiteDetailId === code || t.tissueSiteDetailId === decoded);
      if (match) return { value: match.tissueSiteDetailId, label: match.tissueSiteDetail };

      // try matching by name (some params might be passed as names)
      const byName = tissues.tissueInfo.find(
        (t) => t.tissueSiteDetail.toLowerCase() === normalized.toLowerCase(),
      );
      if (byName) return { value: byName.tissueSiteDetailId, label: byName.tissueSiteDetail };

      // fallback: return original code as value with a cleaned-up label
      return { value: code, label: normalized || code };
  })
  .filter(Boolean);
  return options;
}

