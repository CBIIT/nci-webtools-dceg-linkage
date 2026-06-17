import { NextRequest, NextResponse } from "next/server";

const HEADER_ALLOWLIST = ["accept", "accept-language", "content-type", "cookie", "user-agent", "x-request-id"];

function getBackendBaseUrl(): string {
  return process.env.API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:80";
}

function normalizeTarget(target: string | null): string | null {
  if (!target) {
    return null;
  }

  const trimmed = target.trim().replace(/^\/+/, "");
  if (!trimmed || trimmed.includes("..")) {
    return null;
  }

  return trimmed;
}

function buildTargetUrl(request: NextRequest): string | null {
  const backendBaseUrl = getBackendBaseUrl().replace(/\/$/, "");
  const params = request.nextUrl.searchParams;
  const target = normalizeTarget(params.get("target"));

  if (!target) {
    return null;
  }

  const forwardParams = new URLSearchParams();
  for (const [key, value] of params.entries()) {
    if (key !== "target") {
      forwardParams.append(key, value);
    }
  }

  const query = forwardParams.toString();
  return `${backendBaseUrl}/LDlinkRestWeb/${target}${query ? `?${query}` : ""}`;
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

  // Request uncompressed upstream responses to avoid encoding/header mismatch.
  headers.set("accept-encoding", "identity");
  headers.set("X-LDlink-BFF", "1");
  return headers;
}

function buildClientHeaders(upstreamHeaders: Headers): Headers {
  const headers = new Headers(upstreamHeaders);

  // These hop-by-hop/size/encoding headers can mismatch when proxied streams are transformed.
  headers.delete("content-encoding");
  headers.delete("content-length");
  headers.delete("transfer-encoding");
  headers.delete("connection");

  return headers;
}

async function proxyRequest(request: NextRequest): Promise<Response> {
  const targetUrl = buildTargetUrl(request);
  if (!targetUrl) {
    return NextResponse.json({ error: "Missing or invalid 'target' parameter." }, { status: 400 });
  }

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

  try {
    const upstream = await fetch(targetUrl, init);
    return new Response(upstream.body, {
      status: upstream.status,
      statusText: upstream.statusText,
      headers: buildClientHeaders(upstream.headers),
    });
  } catch (error) {
    const details = error instanceof Error ? error.message : "Unknown upstream fetch error";
    return NextResponse.json(
      {
        error: "Upstream LDlinkRestWeb request failed.",
        targetUrl,
        details,
      },
      { status: 502 }
    );
  }
}

export async function GET(request: NextRequest) {
  return proxyRequest(request);
}

export async function POST(request: NextRequest) {
  return proxyRequest(request);
}

export async function PUT(request: NextRequest) {
  return proxyRequest(request);
}

export async function PATCH(request: NextRequest) {
  return proxyRequest(request);
}

export async function DELETE(request: NextRequest) {
  return proxyRequest(request);
}

export async function OPTIONS(request: NextRequest) {
  return proxyRequest(request);
}
