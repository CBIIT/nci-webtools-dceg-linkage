import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Script from "next/script";
import "./css/ncids.css";
import "./css/LDlink.css";
import Header from "./components/Header";
import Navbar from "./components/Navbar";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "LDlink | An Interactive Web Tool for Exploring Linkage Disequilibrium in Population Groups",
  description:
    "LDlink is a suite of web-based applications designed to easily and efficiently interrogate linkage disequilibrium in population groups.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="/LD.ico" />
        <link rel="apple-touch-icon" href="/LD.ico" />
        <meta httpEquiv="X-UA-Compatible" content="IE=edge" />
        <meta name="author" content="NCI, CBIIT, DCEG, Machiela" />
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.6/dist/css/bootstrap.min.css" 
        rel="stylesheet" 
        integrity="sha384-4Q6Gf2aSP4eDXB8Miphtr37CMZZQ5oXLH2yaXMJ2w8e2ZtHTl7GptT4jmndRuHDT" 
        crossOrigin="anonymous" /> 
        
        {/* Add other stylesheets here if needed */}
      </head>
      
        <body className={`${geistSans.variable} ${geistMono.variable}`} >
          <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
            <Header />
            <Navbar />
            {children}
            <Footer />
          </div>

          {/* Load custom scripts */}

        {/* External scripts */}
        <Script
          async
          src="https://www.googletagmanager.com/gtag/js?id=G-JKSF0J7NH9"
        />
        <Script id="gtag-init">
          {`
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', 'G-JKSF0J7NH9');
          `}
        </Script>
        <Script src="https://cbiit.github.io/nci-softwaresolutions-elements/components/include-html.js" />
        <Script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js" />
        <Script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.6/dist/js/bootstrap.bundle.min.js" integrity="sha384-j1CDi7MgGQ12Z7Qab0qlWQ/Qqz24Gc6BM0thvEMVjHnfYGF0rmFCozFSxQBxwHKO" crossOrigin="anonymous"></Script>
      </body>
    </html>
  );
}
