import "server-only";
import { createHmac, randomBytes, timingSafeEqual } from "node:crypto";

export const DEFAULT_COOKIE_NAME = "ldlink_browser_session";
export const COOKIE_MAX_AGE_SECONDS = 7 * 24 * 60 * 60;
export const COOKIE_MAX_AGE_MS = COOKIE_MAX_AGE_SECONDS * 1000;

export function getSessionCookieName(): string {
  return (
    process.env.LDLINK_BROWSER_SESSION_COOKIE_NAME?.trim() ||
    process.env.NEXT_PUBLIC_LDLINK_BROWSER_SESSION_COOKIE_NAME?.trim() ||
    DEFAULT_COOKIE_NAME
  );
}

export function getSessionSigningSecret(): string {
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

export function isSignedSessionValueValid(value: string, secret: string): boolean {
  const parts = value.split(".");
  if (parts.length !== 3) {
    return false;
  }

  const [issuedAtRaw, nonce, signature] = parts;
  const issuedAt = Number(issuedAtRaw);

  if (!Number.isFinite(issuedAt) || issuedAt <= 0 || !nonce || !signature) {
    return false;
  }

  const now = Date.now();
  if (issuedAt > now + 5 * 60 * 1000) {
    return false;
  }

  if (now - issuedAt > COOKIE_MAX_AGE_MS) {
    return false;
  }

  const payload = `${issuedAtRaw}.${nonce}`;
  const expectedSignature = signPayload(payload, secret);
  return safeSignatureEqual(expectedSignature, signature);
}

export function createSignedSessionValue(secret: string): string {
  const issuedAt = Date.now().toString();
  const nonce = toBase64Url(randomBytes(16));
  const payload = `${issuedAt}.${nonce}`;
  const signature = signPayload(payload, secret);
  return `${payload}.${signature}`;
}
