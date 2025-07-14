import axios from "axios";

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
  return await axios.post(`/LDlinkRestWeb/upload`, formData);
}

export async function ldassoc(params: any): Promise<any> {
  const searchParams = new URLSearchParams(flattenForParams(params)).toString();
  return (await axios.get(`/LDlinkRestWeb/ldassoc?${searchParams}`)).data;
}

export async function ldassocExample(genome_build: string): Promise<any> {
  return (await axios.get(`/LDlinkRestWeb/ldassoc_example?genome_build=${genome_build}`)).data;
}

export async function ldexpress(params: any): Promise<any> {
  return (await axios.post(`/LDlinkRestWeb/ldexpress`, params)).data;
}

export async function ldexpressTissues(): Promise<any> {
  return (await axios.get(`/LDlinkRestWeb/ldexpress_tissues`)).data;
}

export async function ldhap(params: any): Promise<any> {
  const searchParams = new URLSearchParams(flattenForParams(params)).toString();
  return (await axios.get(`/LDlinkRestWeb/ldhap?${searchParams}`)).data;
}

export async function ldmatrix(params: any): Promise<any> {
  const searchParams = new URLSearchParams(flattenForParams(params)).toString();
  return (await axios.get(`/LDlinkRestWeb/ldmatrix?${searchParams}`)).data;
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
  return (await axios.post(`/LDlinkRestWeb/snpchip`, params)).data;
}

