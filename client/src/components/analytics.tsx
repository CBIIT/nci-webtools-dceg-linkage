"use client";
import Script from "next/script";

interface GoogleAnalyticsProps {
  id: string;
}

export default function GoogleAnalytics({ id }: GoogleAnalyticsProps) {
  return (
    <>
      <Script strategy="afterInteractive" src={`https://www.googletagmanager.com/gtag/js?id=${id}`}></Script>
      <Script id="gtag" strategy="afterInteractive">
        {`
        window.dataLayer = window.dataLayer || [];
        function gtag() {
          dataLayer.push(arguments);
        }
        gtag("js", new Date());
        gtag("config", "${id}");
      `}
      </Script>
    </>
  );
}
