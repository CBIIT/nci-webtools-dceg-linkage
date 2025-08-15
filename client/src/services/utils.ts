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
