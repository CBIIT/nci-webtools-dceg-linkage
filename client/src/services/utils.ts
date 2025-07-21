export function parseSnps(text: string): string {
  const lines = text.split("\n");
  const snps = lines
    .map((line) => {
      const snp = line.trim();
      const variantRegex = /^(([rR][sS]\d+)|([cC][hH][rR][\dxXyY]\d?:\d+))$/;
      if (variantRegex.test(snp)) {
        return snp;
      }
      return null;
    })
    .filter(Boolean)
    .join("\n");
  return snps;
}

export const rsChrRegex = /^\s*(?:[rR][sS]\d+|[cC][hH][rR](?:[xXyY]|\d+)?(?::\d+))\s*$/;
