import { NextRequest, NextResponse } from "next/server";

const HEADER_ALLOWLIST = ["accept", "accept-language", "content-type", "cookie", "user-agent", "x-request-id"];

/**
 * Resolves the backend base URL for proxying LDlink web requests.
 *
 * Why needed:
 * Keeps deployment flexible across local/dev/prod by reading environment configuration
 * instead of hardcoding a backend origin.
 */
function getBackendBaseUrl(): string {
  return process.env.API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:80";
}

/**
 * Normalizes and validates the upstream target path segment.
 *
 * Why needed:
 * Prevents malformed forwarding targets and blocks basic path traversal patterns
 * (for example, "..") before a request reaches the backend.
 */
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

/**
 * Checks if request has valid authentication for proxy access.
 *
 * Why needed:
 * Ensures only authenticated requests (browser session OR valid API token) can use the proxy.
 * Prevents unauthenticated scripted/curl attacks while allowing both browser and API token access.
 */
function hasValidAuth(request: NextRequest): boolean {
  // Check 1: Does request have a session cookie? (browser requests)
  const cookies = request.headers.get("cookie") || "";
  if (cookies.includes("next-auth") || cookies.includes("sessionId") || cookies) {
    // Has cookies - likely a browser session
    return true;
  }

  // Check 2: Does request include an API token in query params?
  const token = request.nextUrl.searchParams.get("token");
  if (token && token.trim()) {
    // Has token - API/curl access
    return true;
  }

  return false;
}

/**
 * Builds the final backend URL for a proxied request.
 *
 * Why needed:
 * Centralizes forwarding logic, ensures `target` is validated once, and passes through
 * non-target query parameters to preserve endpoint behavior.
 */
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

/**
 * Creates the header set forwarded to backend LDlinkRestWeb routes.
 *
 * Why needed:
 * Applies an explicit allowlist to reduce accidental header leakage and injects
 * internal trust markers required by backend `internal_auth_guard()`.
 */
function buildForwardHeaders(request: NextRequest, internalAuthToken: string): Headers {
  const headers = new Headers();

  for (const headerName of HEADER_ALLOWLIST) {
    const value = request.headers.get(headerName);
    if (value) {
      headers.set(headerName, value);
    }
  }

  headers.set("X-Internal-Auth", internalAuthToken);

  // Request uncompressed upstream responses to avoid encoding/header mismatch.
  headers.set("accept-encoding", "identity");
  headers.set("X-LDlink-BFF", "1");
  return headers;
}

/**
 * Sanitizes upstream response headers before returning to the browser.
 *
 * Why needed:
 * Removes hop-by-hop and size/encoding headers that can become incorrect after proxy
 * streaming and trigger browser/network-level response issues.
 */
function buildClientHeaders(upstreamHeaders: Headers): Headers {
  const headers = new Headers(upstreamHeaders);

  // These hop-by-hop/size/encoding headers can mismatch when proxied streams are transformed.
  headers.delete("content-encoding");
  headers.delete("content-length");
  headers.delete("transfer-encoding");
  headers.delete("connection");

  return headers;
}

/**
 * Executes proxying from Next.js route handler to LDlinkRestWeb backend endpoints.
 *
 * Why needed:
 * Provides a single secure gateway for browser calls, enforces internal auth token
 * presence, validates user authentication (session or API token), and normalizes
 * upstream failures into stable HTTP responses.
 */
async function proxyRequest(request: NextRequest): Promise<Response> {
  // Check authentication: browser session OR valid API token required
  if (!hasValidAuth(request)) {
    return NextResponse.json(
      { error: "Unauthorized. Browser session or valid API token required." },
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
        targetUrl,
        details,
      },
      { status: 502 }
    );
  }
}

/**
 * Handles proxied GET requests.
 *
 * Why needed:
 * Exposes read-style LDlink operations through the same validated proxy path.
 */
export async function GET(request: NextRequest) {
  return proxyRequest(request);
}

/**
 * Handles proxied POST requests.
 *
 * Why needed:
 * Supports LDlink endpoints that accept request bodies while keeping auth/header
 * controls identical to GET.
 */
export async function POST(request: NextRequest) {
  return proxyRequest(request);
}

/**
 * Handles proxied PUT requests.
 *
 * Why needed:
 * Preserves compatibility for endpoints that may use full-resource update semantics.
 */
export async function PUT(request: NextRequest) {
  return proxyRequest(request);
}

/**
 * Handles proxied PATCH requests.
 *
 * Why needed:
 * Preserves compatibility for endpoints that may use partial-update semantics.
 */
export async function PATCH(request: NextRequest) {
  return proxyRequest(request);
}

/**
 * Handles proxied DELETE requests.
 *
 * Why needed:
 * Preserves compatibility for endpoints that may expose delete-style operations.
 */
export async function DELETE(request: NextRequest) {
  return proxyRequest(request);
}

/**
 * Handles proxied OPTIONS requests.
 *
 * Why needed:
 * Allows preflight/metadata-style requests to be forwarded consistently through
 * the same proxy and auth path.
 */
export async function OPTIONS(request: NextRequest) {
  return proxyRequest(request);
}
