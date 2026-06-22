import { NextRequest, NextResponse } from "next/server";

const HEADER_ALLOWLIST = ["accept", "accept-language", "content-type", "cookie", "user-agent", "x-request-id"];

function decodeBase64Url(value: string): Uint8Array {
  const normalized = value.replace(/-/g, "+").replace(/_/g, "/");
  const padded = normalized + "=".repeat((4 - (normalized.length % 4 || 4)) % 4);
  return Uint8Array.from(Buffer.from(padded, "base64"));
}

function decodeJwtJsonPart(value: string): Record<string, unknown> | null {
  try {
    const bytes = decodeBase64Url(value);
    const json = Buffer.from(bytes).toString("utf8");
    const parsed = JSON.parse(json);
    if (parsed && typeof parsed === "object") {
      return parsed as Record<string, unknown>;
    }
    return null;
  } catch {
    return null;
  }
}

function getRequestJwt(request: NextRequest): string {
  const authorization = request.headers.get("authorization") || "";
  if (authorization.toLowerCase().startsWith("bearer ")) {
    const bearerToken = authorization.slice(7).trim();
    if (bearerToken) {
      return bearerToken;
    }
  }

  const cookieName = process.env.LDLINK_WEB_AUTH_COOKIE_NAME?.trim();
  if (cookieName) {
    const cookieToken = request.cookies.get(cookieName)?.value?.trim() || "";
    if (cookieToken) {
      return cookieToken;
    }
  }

  return "";
}

function isUserJwtEnforced(): boolean {
  const raw = process.env.LDLINK_WEB_ENFORCE_USER_JWT?.trim().toLowerCase();
  return raw === "1" || raw === "true" || raw === "yes";
}

function isValidSameOriginUrl(urlValue: string, expectedOrigin: string): boolean {
  try {
    return new URL(urlValue).origin === expectedOrigin;
  } catch {
    return false;
  }
}

function isBrowserLikeRequest(request: NextRequest): boolean {
  const host = request.headers.get("host") || "";
  const expectedOrigin = `${request.nextUrl.protocol}//${host}`;

  const origin = request.headers.get("origin") || "";
  const referer = request.headers.get("referer") || "";
  const secFetchSite = (request.headers.get("sec-fetch-site") || "").toLowerCase();
  const secFetchMode = (request.headers.get("sec-fetch-mode") || "").toLowerCase();

  const hasSameOriginOrigin = origin ? origin === expectedOrigin : false;
  const hasSameOriginReferer = referer ? isValidSameOriginUrl(referer, expectedOrigin) : false;
  const hasSameOriginSource = hasSameOriginOrigin || hasSameOriginReferer;

  const hasBrowserFetchSignals = secFetchSite === "same-origin" && (secFetchMode === "cors" || secFetchMode === "same-origin" || secFetchMode === "navigate");

  return hasSameOriginSource && hasBrowserFetchSignals;
}

async function validateJwt(token: string, secret: string): Promise<boolean> {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) {
      return false;
    }

    const [encodedHeader, encodedPayload, encodedSignature] = parts;
    const header = decodeJwtJsonPart(encodedHeader);
    const payload = decodeJwtJsonPart(encodedPayload);

    if (!header || !payload) {
      return false;
    }

    if (header.alg !== "HS256") {
      return false;
    }

    const now = Math.floor(Date.now() / 1000);
    const exp = typeof payload.exp === "number" ? payload.exp : null;
    const nbf = typeof payload.nbf === "number" ? payload.nbf : null;
    const iat = typeof payload.iat === "number" ? payload.iat : null;

    if (exp !== null && now >= exp) {
      return false;
    }

    if (nbf !== null && now < nbf) {
      return false;
    }

    if (iat !== null && iat > now + 60) {
      return false;
    }

    const key = await crypto.subtle.importKey(
      "raw",
      new TextEncoder().encode(secret),
      { name: "HMAC", hash: "SHA-256" },
      false,
      ["verify"]
    );

    const signingInput = `${encodedHeader}.${encodedPayload}`;
    const signature = decodeBase64Url(encodedSignature);
    const signatureBytes: BufferSource = signature as unknown as BufferSource;
    const signingBytes: BufferSource = new TextEncoder().encode(signingInput) as unknown as BufferSource;

    return await crypto.subtle.verify(
      "HMAC",
      key,
      signatureBytes,
      signingBytes
    );
  } catch {
    return false;
  }
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
  if (!isBrowserLikeRequest(request)) {
    return NextResponse.json(
      { error: "Forbidden. Browser-origin request is required." },
      { status: 403 }
    );
  }

  const enforceUserJwt = isUserJwtEnforced();
  if (enforceUserJwt) {
    const userJwtSecret = process.env.LDLINK_WEB_JWT_SECRET?.trim();
    if (!userJwtSecret) {
      return NextResponse.json(
        { error: "Web auth JWT secret is not configured for web proxy." },
        { status: 500 }
      );
    }

    const userJwt = getRequestJwt(request);
    if (!userJwt) {
      return NextResponse.json(
        { error: "Unauthorized. Valid user JWT is required." },
        { status: 401 }
      );
    }

    const isValidJwt = await validateJwt(userJwt, userJwtSecret);
    if (!isValidJwt) {
      return NextResponse.json(
        { error: "Forbidden. User JWT validation failed." },
        { status: 403 }
      );
    }
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
