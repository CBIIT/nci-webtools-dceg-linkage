"use client";
import { ReactNode } from "react";
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
import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap-icons/font/bootstrap-icons.css";
import "./styles/main.scss";
import "./styles/ncids.scss";

export default function RootLayout({ children }: { children: ReactNode }) {
  const routes: Route[] = [
    { title: "Home", path: "/", subRoutes: [] },
    { title: "LD Tools", path: "/ldtools", subRoutes: [
      {title: "LDassoc", path: "/ldtools/ldassoc"},
      {title: "LDexpress", path: "/ldtools/ldexpress"},
      {title: "LDhap", path: "/ldtools/ldhap"},
      {title: "LDmatrix", path: "/ldtools/ldmatrix"},
      {title: "LDpair", path: "/ldtools/ldpair"},
      {title: "LDpop", path: "/ldtools/ldpop"},
      {title: "LDproxy", path: "/ldtools/ldproxy"},
      {title: "LDtrait", path: "/ldtools/ldtrait"},
      {title: "LDscore", path: "/ldtools/ldscore"},
      {title: "SNPchip", path: "/ldtools/SNPchip"},
      {title: "SNPclip", path: "/ldtools/SNPclip"}

      
    ] },
    { title: "API Access", path: "/apiaccess", subRoutes: [] },
    { title: "Citations", path: "/citations", subRoutes: [] },
    { title: "Version History", path: "/history", subRoutes: [] },
    { title: "Documentations", path: "/docs", subRoutes: [] },
  ];
  const queryClient = new QueryClient({});
  const pathname = usePathname();
  // const currentRoute = routes.find((route) => route.path === pathname);
  const currentRoute =
  routes.find((route) => route.path === pathname) ||
  routes
    .flatMap((route) => route.subRoutes)
    .find((subRoute) => subRoute.path === pathname);
  const pageTitle = currentRoute ? `${currentRoute.title} | Survival Stats Tools` : "Survival Stats Tools";

  return (
    <html lang="en">
      <head>
        <title>{pageTitle}</title>
        <meta name="keywords" content="ldlink" />
        <link rel="icon" href="/favicon.ico" sizes="any" />
        <GoogleAnalytics id="G-DGFTR3EY14" />
        <Script src="https://cbiit.github.io/nci-softwaresolutions-elements/components/include-html.js" />
      </head>
      <body>
        {/* <include-html src="https://cbiit.github.io/nci-softwaresolutions-elements/banners/government-shutdown.html"></include-html> */}
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
