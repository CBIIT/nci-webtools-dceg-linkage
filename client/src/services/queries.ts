import axios from "axios";

const WEB_PROXY_ENDPOINT = "/api/ldlink-web-proxy";

function webProxyUrl(target: string, queryString = ""): string {
  const encodedTarget = encodeURIComponent(target);
  return `${WEB_PROXY_ENDPOINT}?target=${encodedTarget}${queryString ? `&${queryString}` : ""}`;
}

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
  return await axios.post(webProxyUrl("upload"), formData);
}

export async function ldassoc(params: any): Promise<any> {
  const searchParams = new URLSearchParams(flattenForParams(params)).toString();
  return (await axios.get(webProxyUrl("ldassoc", searchParams))).data;
}

export async function ldassocExample(genome_build: string): Promise<any> {
  return (await axios.get(webProxyUrl("ldassoc_example", `genome_build=${encodeURIComponent(genome_build)}`))).data;
}

export async function ldexpress(params: any): Promise<any> {
  return (await axios.post(webProxyUrl("ldexpress"), params)).data;
}

export async function ldexpressTissues(): Promise<any> {
  return (await axios.get(webProxyUrl("ldexpress_tissues"))).data;
}

export async function ldhap(params: any): Promise<any> {
  const searchParams = new URLSearchParams(params).toString();
  return (await axios.get(webProxyUrl("ldhap", searchParams))).data;
}

export async function ldmatrix(params: any): Promise<any> {
  const searchParams = new URLSearchParams(params).toString();
  return (await axios.get(webProxyUrl("ldmatrix", searchParams))).data;
}

export async function ldpair(params: any): Promise<any> {
  const searchParams = new URLSearchParams(params).toString();
  return (await axios.get(webProxyUrl("ldpair", searchParams))).data;
}

export async function ldpop(params: any): Promise<any> {
  const searchParams = new URLSearchParams(params).toString();
  return (await axios.get(webProxyUrl("ldpop", searchParams))).data;
}

export async function ldproxy(params: any): Promise<any> {
  const searchParams = new URLSearchParams(params).toString();
  return (await axios.get(webProxyUrl("ldproxy", searchParams))).data;
}

export async function fetchOutput(filename: string): Promise<any> {
  return (await axios.get(`/LDlinkRestWeb/tmp/${filename}`)).data;
}

export async function fetchOutputText(filename: string): Promise<any> {
  return (await axios.get(`/LDlinkRestWeb/tmp/${filename}`, { responseType: "text" })).data;
}

export async function fetchOutputStatus(filename: string): Promise<any> {
  return (await axios.get(`/LDlinkRestWeb/status/${filename}`)).data;
}

export async function snpchipPlatforms(): Promise<any> {
  return (await axios.get(`/LDlinkRestWeb/snpchip_platforms`)).data;
}

export async function snpchip(params: any): Promise<any> {
  return (await axios.post(webProxyUrl("snpchip"), params)).data;
}

export async function ldscore(params: any): Promise<any> {
  return (await axios.post(webProxyUrl("ldscore"), params)).data;
}
export async function snpclip(params: any): Promise<any> {
  return (await axios.post(webProxyUrl("snpclip"), params)).data;
}

export async function fetchHeritabilityResult(params: URLSearchParams): Promise<any> {
  return (await axios.get(webProxyUrl("ldherit", params.toString()))).data;
}

export async function fetchGeneticCorrelationResult(params: URLSearchParams): Promise<any> {
  return (await axios.get(webProxyUrl("ldcorrelation", params.toString()))).data;
}

export async function fetchLdScoreCalculationResult(params: URLSearchParams): Promise<any> {
  return (await axios.get(webProxyUrl("ldscore", params.toString()))).data;
}

export async function ldtrait(params: any): Promise<any> {
  return (await axios.post(webProxyUrl("ldtrait"), params)).data;
}

export async function validateSumstats(filename: string, reference: string): Promise<any> {
  const query = `filename=${encodeURIComponent(filename)}&reference=${encodeURIComponent(reference)}`;
  return (await axios.get(webProxyUrl("validate_sumstats", query))).data;
}

export async function validateBfile(filename: string, reference: string): Promise<any> {
  const query = `filename=${encodeURIComponent(filename)}&reference=${encodeURIComponent(reference)}`;
  return (await axios.get(webProxyUrl("validate_bfile", query))).data;
}
