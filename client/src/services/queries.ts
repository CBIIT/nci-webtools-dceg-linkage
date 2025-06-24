import axios from "axios";

export async function upload(params: any, data: any): Promise<any> {
  return await axios.post(`/LDlinkRestWeb/upload`, { params, data });
}
