import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Redirect legacy root queries:
//  - /?snps=...&pop=...&tab=ldtraitget -> /ldtrait
//  - /?snps=...&pop=...&tissues=...&tab=ldexpressget -> /ldexpress (adds autorun=1)
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
  if (pathname === '/' && searchParams.has('snps') && searchParams.get('tab') === 'ldexpressget') {
    const snps = searchParams.get('snps') || '';
    const pop = searchParams.get('pop') || '';
    const tissues = searchParams.get('tissues') || '';
    const r2_d = searchParams.get('r2_d') || 'r2';
    const p_threshold = searchParams.get('p_threshold') || '0.1';
    const r2_d_threshold = searchParams.get('r2_d_threshold') || '0.1';
    const windowParam = searchParams.get('window') || '500000';
    const genome_build = searchParams.get('genome_build') || 'grch37';
    const params = new URLSearchParams({ snps, pop, tissues, r2_d, p_threshold, r2_d_threshold, window: windowParam, genome_build, autorun: '1' });
    return NextResponse.redirect(new URL(`/ldexpress?${params.toString()}`, request.url));
  }
  if (pathname === '/' && searchParams.has('var') && searchParams.get('tab') === 'ldproxy') {
    const variable = searchParams.get('var') || '';
    const pop = searchParams.get('pop') || '';
    const r2_d = searchParams.get('r2_d') || 'r2';
    const windowParam = searchParams.get('window') || '5000';
    const genome_build = searchParams.get('genome_build') || 'grch37';
    const collapseTranscript = searchParams.get('collapseTranscript') || 'true';
    const annotate = searchParams.get('annotate') || 'forge';
    // Provide params expected by LDproxy initial state; supplying 'var' triggers auto-submit.
    const params = new URLSearchParams({ var: variable, pop, r2_d, window: windowParam, genome_build, collapseTranscript, annotate });
    return NextResponse.redirect(new URL(`/ldproxy?${params.toString()}`, request.url));
  }
  return NextResponse.next();
}

export const config = {
  matcher: ['/'],
};
