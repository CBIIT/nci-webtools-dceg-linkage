import { NextRequest, NextResponse } from "next/server";
import { createHmac, randomBytes, timingSafeEqual } from "node:crypto";

export const dynamic = "force-dynamic";
export const revalidate = 0;

const DEFAULT_COOKIE_NAME = "ldlink_browser_session";
const COOKIE_MAX_AGE_SECONDS = 7 * 24 * 60 * 60;
const COOKIE_MAX_AGE_MS = COOKIE_MAX_AGE_SECONDS * 1000;

function getSessionCookieName(): string {
  return (
    process.env.LDLINK_BROWSER_SESSION_COOKIE_NAME?.trim() ||
    process.env.NEXT_PUBLIC_LDLINK_BROWSER_SESSION_COOKIE_NAME?.trim() ||
    DEFAULT_COOKIE_NAME
  );
}

function shouldUseSecureCookie(request: NextRequest): boolean {
  const protoHeader = request.headers.get("x-forwarded-proto");
  if (protoHeader?.toLowerCase().includes("https")) {
    return true;
  }

  return request.nextUrl.protocol === "https:";
}

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

function isSignedSessionValueValid(value: string, secret: string): boolean {
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
  const expectedSignature = signPayload(payload, secret);
  return safeSignatureEqual(expectedSignature, signature);
}

function createSignedSessionValue(secret: string): string {
  const issuedAt = Date.now().toString();
  const nonce = toBase64Url(randomBytes(16));
  const payload = `${issuedAt}.${nonce}`;
  const signature = signPayload(payload, secret);
  return `${payload}.${signature}`;
}

export async function GET(request: NextRequest) {
  const cookieName = getSessionCookieName();
  const signingSecret = getSessionSigningSecret();

  if (!signingSecret) {
    return NextResponse.json(
      { error: "Session signing secret is not configured." },
      {
        status: 500,
        headers: {
          "Cache-Control": "no-store, no-cache, must-revalidate, private",
        },
      }
    );
  }

  const existingValue = request.cookies.get(cookieName)?.value?.trim();
  if (existingValue && isSignedSessionValueValid(existingValue, signingSecret)) {
    return NextResponse.json(
      { ok: true, initialized: true, alreadyInitialized: true },
      {
        headers: {
          "Cache-Control": "no-store, no-cache, must-revalidate, private",
        },
      }
    );
  }

  const response = NextResponse.json({ ok: true, initialized: true, alreadyInitialized: false });
  response.headers.set("Cache-Control", "no-store, no-cache, must-revalidate, private");

  response.cookies.set(cookieName, createSignedSessionValue(signingSecret), {
    httpOnly: true,
    secure: shouldUseSecureCookie(request),
    sameSite: "strict",
    path: "/",
    maxAge: COOKIE_MAX_AGE_SECONDS,
  });

  return response;
}
