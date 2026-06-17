import { NextRequest } from "next/server";

const HEADER_ALLOWLIST = ["accept", "accept-language", "content-type", "cookie", "user-agent", "x-request-id"];

function getBackendBaseUrl(): string {
  return process.env.API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:80";
}

function buildTargetUrl(pathSegments: string[], requestUrl: string): string {
  const baseUrl = getBackendBaseUrl().replace(/\/$/, "");
  const targetPath = pathSegments.join("/");
  const incoming = new URL(requestUrl);
  const queryString = incoming.search || "";
  return `${baseUrl}/LDlinkRestWeb/${targetPath}${queryString}`;
}

function buildForwardHeaders(request: NextRequest): Headers {
  const headers = new Headers();

  for (const headerName of HEADER_ALLOWLIST) {
    const value = request.headers.get(headerName);
    if (value) {
      headers.set(headerName, value);
    }
  }

  const internalAuthToken = process.env.LDLINK_INTERNAL_AUTH_TOKEN || "";
  if (internalAuthToken) {
    headers.set("X-Internal-Auth", internalAuthToken);
  }

  headers.set("X-LDlink-BFF", "1");
  return headers;
}

async function proxyRequest(request: NextRequest, pathSegments: string[]): Promise<Response> {
  const targetUrl = buildTargetUrl(pathSegments, request.url);
  const headers = buildForwardHeaders(request);
  const method = request.method.toUpperCase();

  const init: RequestInit = {
    method,
    headers,
    redirect: "manual",
  };

  if (method !== "GET" && method !== "HEAD") {
    init.body = await request.arrayBuffer();
  }

  const upstream = await fetch(targetUrl, init);

  return new Response(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: upstream.headers,
  });
}

export async function GET(request: NextRequest, context: { params: { path: string[] } }) {
  return proxyRequest(request, context.params.path || []);
}

export async function POST(request: NextRequest, context: { params: { path: string[] } }) {
  return proxyRequest(request, context.params.path || []);
}

export async function PUT(request: NextRequest, context: { params: { path: string[] } }) {
  return proxyRequest(request, context.params.path || []);
}

export async function PATCH(request: NextRequest, context: { params: { path: string[] } }) {
  return proxyRequest(request, context.params.path || []);
}

export async function DELETE(request: NextRequest, context: { params: { path: string[] } }) {
  return proxyRequest(request, context.params.path || []);
}

export async function OPTIONS(request: NextRequest, context: { params: { path: string[] } }) {
  return proxyRequest(request, context.params.path || []);
}
