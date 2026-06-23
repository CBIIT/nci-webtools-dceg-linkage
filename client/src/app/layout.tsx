"use client";
import { ReactNode, useEffect } from "react";
import Script from "next/script";
import { Suspense } from "react";
import { ErrorBoundary } from "next/dist/client/components/error-boundary";
import Alert from "react-bootstrap/Alert";
import Loading from "@/components/loading";
import GoogleAnalytics from "@/components/analytics";
import { Header, Route } from "@/components/header";
import Footer from "@/components/footer";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import { usePathname } from "next/navigation";
import "./styles/main.scss";

async function initializeBrowserSession() {
  try {
<<<<<<< HEAD
    // Initialize browser session. The session cookie is httpOnly, so we cannot check for it
    // via document.cookie. The endpoint is idempotent and handles existing valid sessions.
=======
>>>>>>> c0bbcdf201b98cfc3e0b9bf85f59f13725fbd590
    const response = await fetch("/api/init-browser-session", {
      method: "GET",
      credentials: "include",
    });
    if (!response.ok) {
      console.warn("Failed to initialize browser session:", response.status);
    }
  } catch (error) {
    console.warn("Error initializing browser session:", error);
  }
}

export default function RootLayout({ children }: { children: ReactNode }) {
  useEffect(() => {
    initializeBrowserSession();
  }, []);
  const routes: Route[] = [
    { title: "Home", path: "/", subRoutes: [] },
    {
      title: "LD Tools",
      path: "/ldtools",
      subRoutes: [
        { title: "LDassoc", path: "/ldassoc" },
        { title: "LDexpress", path: "/ldexpress" },
        { title: "LDhap", path: "/ldhap" },
        { title: "LDmatrix", path: "/ldmatrix" },
        { title: "LDpair", path: "/ldpair" },
        { title: "LDpop", path: "/ldpop" },
        { title: "LDproxy", path: "/ldproxy" },
        { title: "LDscore", path: "/ldscore" },
        { title: "LDtrait", path: "/ldtrait" },
        { title: "SNPchip", path: "/snpchip" },
        { title: "SNPclip", path: "/snpclip" },
      ],
    },
    { title: "API Access", path: "/apiaccess", subRoutes: [] },
    { title: "Documentation", path: "/help", subRoutes: [] },
    { title: "Citations", path: "/citations", subRoutes: [] },
    { title: "Version History", path: "/version", subRoutes: [] },
  ];
  const queryClient = new QueryClient({});
  const pathname = usePathname();
  // const currentRoute = routes.find((route) => route.path === pathname);
  const currentRoute =
    routes.find((route) => route.path === pathname) ||
    routes.flatMap((route) => route.subRoutes).find((subRoute) => subRoute.path === pathname);
  const pageTitle = currentRoute ? `LDlink | ${currentRoute.title}` : "LDlink";

  return (
    <html lang="en">
      <head>
        <title>{pageTitle}</title>
        <meta name="keywords" content="ldlink" />
        <link rel="icon" href="/favicon.ico" sizes="any" />
        <GoogleAnalytics id="G-JKSF0J7NH9" />
        <Script src="https://cbiit.github.io/nci-softwaresolutions-elements/components/include-html.js" />
        <Script
          src="https://assets.adobedtm.com/6a4249cd0a2c/785de09de161/launch-70d67a6a40a8.min.js"
          async={true}></Script>
      </head>
      <body>
        {/* @ts-expect-error - include-html is a custom element */}
        <include-html src="https://cbiit.github.io/nci-softwaresolutions-elements/banners/government-shutdown.html"></include-html>
        <Header routes={routes} />
        <main
          className="position-relative d-flex flex-column flex-grow-1 align-items-stretch bg-light"
          style={{ minHeight: "600px" }}>
          <ErrorBoundary errorComponent={() => <Alert variant="warning">Error loading Form</Alert>}>
            <Suspense fallback={<Loading message="Loading..." />}>
              <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
            </Suspense>
          </ErrorBoundary>
        </main>
        <Footer />
      </body>
    </html>
  );
}
