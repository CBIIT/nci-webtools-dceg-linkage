import { populations } from "@/components/select/pop-select";
import { AxiosError, isAxiosError } from "axios";

export const rsChrRegex = /^\s*(?:[rR][sS]\d+|[cC][hH][rR](?:[xXyY]|\d+)?(?::\d+))\s*$/;

export const rsChrMultilineRegex = /^(?:\s*(?:[rR][sS]\d+|[cC][hH][rR](?:[xXyY]|\d+)?(?::\d+))\s*)(?:\r?\n(?:\s*(?:[rR][sS]\d+|[cC][hH][rR](?:[xXyY]|\d+)?(?::\d+))\s*))*$/;

const uuidV4Regex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export function isValidUuidV4(value: string): boolean {
  return uuidV4Regex.test(value.trim());
}

export function generateReference(): string {
  const cryptoApi = globalThis.crypto;
  if (!cryptoApi || typeof cryptoApi.randomUUID !== "function") {
    throw new Error("Secure UUID generator is not available (crypto.randomUUID).");
  }
  const reference = cryptoApi.randomUUID();
  if (!isValidUuidV4(reference)) {
    throw new Error("Generated reference is not a valid UUIDv4 string.");
  }
  return reference;
}

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

// Extracts the backend's "error" message from a failed LDscore/Heritability/Genetic
// Correlation calculation request (e.g. LDSC failures returned as 422 JSON), falling
// back to a generic message when the response didn't include one.
export function parseLdScoreCalculationError(error: unknown, fallback: string): string {
  if (isAxiosError(error)) {
    const data = error.response?.data as { error?: string } | undefined;
    if (data?.error) return data.error;
  }
  return fallback;
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

