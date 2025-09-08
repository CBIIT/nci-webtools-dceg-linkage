import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Redirect legacy root queries like /?snps=...&pop=...&tab=ldtraitget to /ldtrait
export function middleware(request: NextRequest) {
  const { pathname, searchParams } = request.nextUrl;
  if (pathname === '/' && searchParams.has('snps') && searchParams.get('tab') === 'ldtraitget') {
    const snps = searchParams.get('snps') || '';
    const pop = searchParams.get('pop') || '';
    const r2_d = searchParams.get('r2_d') || 'r2';
    const windowParam = searchParams.get('window') || '500000';
    const genome_build = searchParams.get('genome_build') || 'grch37';
    const r2_d_threshold = searchParams.get('r2_d_threshold') || '0.1';
    const params = new URLSearchParams({ snps, pop, r2_d, window: windowParam, genome_build, r2_d_threshold });
    return NextResponse.redirect(new URL(`/ldtrait?${params.toString()}`, request.url));
  }
  return NextResponse.next();
}

export const config = {
  matcher: ['/'],
};
