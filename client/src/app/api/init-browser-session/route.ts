import { NextRequest, NextResponse } from "next/server";
import {
  COOKIE_MAX_AGE_SECONDS,
  createSignedSessionValue,
  getSessionCookieName,
  getSessionSigningSecret,
  isSignedSessionValueValid,
} from "@/lib/session";

export const dynamic = "force-dynamic";
export const revalidate = 0;

function shouldUseSecureCookie(request: NextRequest): boolean {
  const protoHeader = request.headers.get("x-forwarded-proto");
  if (protoHeader?.toLowerCase().includes("https")) {
    return true;
  }

  return request.nextUrl.protocol === "https:";
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
