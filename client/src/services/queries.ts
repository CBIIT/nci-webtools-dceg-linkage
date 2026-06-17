import axios from "axios";

const WEB_API_PREFIX = "/api/ldlink-web";

// Flattens nested objects into bracket notation keys for URLSearchParams
function flattenForParams(obj: any, prefix = ""): Record<string, any> {
  return Object.keys(obj).reduce((acc: any, key) => {
    let value = obj[key];
    const newKey = prefix ? `${prefix}[${key}]` : key;
    if (typeof value === "boolean") {
      value = value ? "True" : "False";
    }
    if (value && typeof value === "object" && !Array.isArray(value)) {
      Object.assign(acc, flattenForParams(value, newKey));
    } else {
      acc[newKey] = value;
    }
    return acc;
  }, {});
}

export async function upload(formData: any): Promise<any> {
  return await axios.post(`${WEB_API_PREFIX}/upload`, formData);
}

export async function ldassoc(params: any): Promise<any> {
  const searchParams = new URLSearchParams(flattenForParams(params)).toString();
  return (await axios.get(`${WEB_API_PREFIX}/ldassoc?${searchParams}`)).data;
}

export async function ldassocExample(genome_build: string): Promise<any> {
  return (await axios.get(`${WEB_API_PREFIX}/ldassoc_example?genome_build=${genome_build}`)).data;
}

export async function ldexpress(params: any): Promise<any> {
  return (await axios.post(`${WEB_API_PREFIX}/ldexpress`, params)).data;
}

export async function ldexpressTissues(): Promise<any> {
  return (await axios.get(`${WEB_API_PREFIX}/ldexpress_tissues`)).data;
}

export async function ldhap(params: any): Promise<any> {
  const searchParams = new URLSearchParams(params).toString();
  return (await axios.get(`${WEB_API_PREFIX}/ldhap?${searchParams}`)).data;
}

export async function ldmatrix(params: any): Promise<any> {
  const searchParams = new URLSearchParams(params).toString();
  return (await axios.get(`${WEB_API_PREFIX}/ldmatrix?${searchParams}`)).data;
}

export async function ldpair(params: any): Promise<any> {
  const searchParams = new URLSearchParams(params).toString();
  return (await axios.get(`${WEB_API_PREFIX}/ldpair?${searchParams}`)).data;
}

export async function ldpop(params: any): Promise<any> {
  const searchParams = new URLSearchParams(params).toString();
  return (await axios.get(`${WEB_API_PREFIX}/ldpop?${searchParams}`)).data;
}

export async function ldproxy(params: any): Promise<any> {
  const searchParams = new URLSearchParams(params).toString();
  return (await axios.get(`${WEB_API_PREFIX}/ldproxy?${searchParams}`)).data;
}

export async function fetchOutput(filename: string): Promise<any> {
  return (await axios.get(`${WEB_API_PREFIX}/tmp/${filename}`)).data;
}

export async function fetchOutputText(filename: string): Promise<any> {
  return (await axios.get(`${WEB_API_PREFIX}/tmp/${filename}`, { responseType: "text" })).data;
}

export async function fetchOutputStatus(filename: string): Promise<any> {
  return (await axios.get(`${WEB_API_PREFIX}/status/${filename}`)).data;
}

export async function snpchipPlatforms(): Promise<any> {
  return (await axios.get(`${WEB_API_PREFIX}/snpchip_platforms`)).data;
}

export async function snpchip(params: any): Promise<any> {
  return (await axios.post(`${WEB_API_PREFIX}/snpchip`, params)).data;
}

export async function ldscore(params: any): Promise<any> {
  return (await axios.post(`${WEB_API_PREFIX}/ldscore`, params)).data;
}
export async function snpclip(params: any): Promise<any> {
  return (await axios.post(`${WEB_API_PREFIX}/snpclip`, params)).data;
}

export async function fetchHeritabilityResult(params: URLSearchParams): Promise<any> {
  return (await axios.get(`${WEB_API_PREFIX}/ldherit?${params.toString()}`)).data;
}

export async function fetchGeneticCorrelationResult(params: URLSearchParams): Promise<any> {
  return (await axios.get(`${WEB_API_PREFIX}/ldcorrelation?${params.toString()}`)).data;
}

export async function fetchLdScoreCalculationResult(params: URLSearchParams): Promise<any> {
  // Try BFF route first, fallback to the existing /api rewrite for LDlinkRest.
  try {
    return (await axios.get(`${WEB_API_PREFIX}/ldscore?${params.toString()}`)).data;
  } catch (err) {
    return (await axios.get(`/api/ldscore?${params.toString()}`)).data;
  }
}

export async function ldtrait(params: any): Promise<any> {
  return (await axios.post(`${WEB_API_PREFIX}/ldtrait`, params)).data;
}

export async function validateSumstats(filename: string, reference: string): Promise<any> {
  return (await axios.get(`${WEB_API_PREFIX}/validate_sumstats?filename=${filename}&reference=${reference}`)).data;
}

export async function validateBfile(filename: string, reference: string): Promise<any> {
  return (
    await axios.get(`${WEB_API_PREFIX}/validate_bfile?filename=${encodeURIComponent(filename)}&reference=${reference}`)
  ).data;
}
