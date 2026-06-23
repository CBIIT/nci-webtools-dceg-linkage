import { NextRequest, NextResponse } from "next/server";
import { createHmac, timingSafeEqual } from "node:crypto";

const HEADER_ALLOWLIST = ["accept", "accept-language", "content-type", "cookie", "user-agent", "x-request-id"];
const COOKIE_MAX_AGE_MS = 7 * 24 * 60 * 60 * 1000;

function getSessionSigningSecret(): string {
  return process.env.LDLINK_INTERNAL_AUTH_TOKEN?.trim() || "";
}

function toBase64Url(input: Buffer): string {
  return input
    .toString("base64")
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/g, "");
}

function signPayload(payload: string, secret: string): string {
  return toBase64Url(createHmac("sha256", secret).update(payload).digest());
}

function safeSignatureEqual(expected: string, provided: string): boolean {
  const expectedBuffer = Buffer.from(expected);
  const providedBuffer = Buffer.from(provided);

  if (expectedBuffer.length !== providedBuffer.length) {
    return false;
  }

  return timingSafeEqual(expectedBuffer, providedBuffer);
}

function hasValidBrowserSession(request: NextRequest, signingSecret: string): boolean {
  const sessionCookieName = process.env.LDLINK_BROWSER_SESSION_COOKIE_NAME?.trim() || "ldlink_browser_session";
  const sessionCookie = request.cookies.get(sessionCookieName);
  const value = sessionCookie?.value?.trim();
  if (!value) {
    return false;
  }

  const parts = value.split(".");
  if (parts.length !== 3) {
    return false;
  }

  const [issuedAtRaw, nonce, signature] = parts;
  const issuedAt = Number(issuedAtRaw);

  if (!Number.isFinite(issuedAt) || issuedAt <= 0 || !nonce || !signature) {
    return false;
  }

  if (Date.now() - issuedAt > COOKIE_MAX_AGE_MS) {
    return false;
  }

  const payload = `${issuedAtRaw}.${nonce}`;
  const expectedSignature = signPayload(payload, signingSecret);
  return safeSignatureEqual(expectedSignature, signature);
}

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

function buildForwardHeaders(request: NextRequest, internalAuthToken: string): Headers {
  const headers = new Headers();

  for (const headerName of HEADER_ALLOWLIST) {
    const value = request.headers.get(headerName);
    if (value) {
      headers.set(headerName, value);
    }
  }

  headers.set("X-Internal-Auth", internalAuthToken);
  headers.set("accept-encoding", "identity");
  return headers;
}

function buildClientHeaders(upstreamHeaders: Headers): Headers {
  const headers = new Headers(upstreamHeaders);
  headers.delete("content-encoding");
  headers.delete("content-length");
  headers.delete("transfer-encoding");
  headers.delete("connection");
  return headers;
}

async function proxyRequest(request: NextRequest): Promise<Response> {
  const signingSecret = getSessionSigningSecret();
  if (!signingSecret) {
    return NextResponse.json(
      { error: "Session signing secret is not configured for web proxy." },
      { status: 500 }
    );
  }

  if (!hasValidBrowserSession(request, signingSecret)) {
    return NextResponse.json(
      { error: "Forbidden. Valid browser session is required. Please refresh and try again." },
      { status: 403 }
    );
  }

  const targetUrl = buildTargetUrl(request);
  if (!targetUrl) {
    return NextResponse.json({ error: "Missing or invalid 'target' parameter." }, { status: 400 });
  }

  const internalAuthToken = process.env.LDLINK_INTERNAL_AUTH_TOKEN?.trim();
  if (!internalAuthToken) {
    return NextResponse.json(
      { error: "Internal auth token is not configured for web proxy." },
      { status: 500 }
    );
  }

  const headers = buildForwardHeaders(request, internalAuthToken);
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
