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


