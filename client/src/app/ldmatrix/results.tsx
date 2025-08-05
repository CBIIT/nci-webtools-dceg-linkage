"use client";
import { useEffect, useRef, useState } from "react";
import Script from "next/script";
import Image from "next/image";
import { Row, Col, Container, Dropdown, Alert } from "react-bootstrap";
import Spinner from "react-bootstrap/Spinner";
import { useQuery, useSuspenseQuery } from "@tanstack/react-query";
import { fetchOutput, fetchOutputStatus } from "@/services/queries";
import { FormData } from "./types";

export default function LdAMatrixResults({ ref }: { ref: string }) {
  const [bokehLoaded, setBokehLoaded] = useState(false);

  const handleDownload = async (format: string) => {
    const url = `/LDlinkRestWeb/tmp/matrix_plot_${ref}.${format}`;
    const response = await fetch(url);
    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = downloadUrl;
    link.download = `matrix_plot_${ref}.${format}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  };

  const { data: status } = useSuspenseQuery({
    queryKey: ["ldmatrix_status", ref],
    queryFn: async () => (ref ? fetchOutput(`matrix${ref}.json`) : null),
  });
  const { data: enableExport } = useQuery<boolean>({
    queryKey: ["ldmatrix-export", ref],
    queryFn: async () => (ref ? fetchOutputStatus(`matrix_plot_${ref}.jpeg`) : false),
    enabled: !!ref && !status?.error,
    refetchInterval: (query) => (query.state.data ? false : 5000),
    retry: 60,
  });

  const { data: plotJson } = useSuspenseQuery({
    queryKey: ["ldmatrix_plot", ref],
    queryFn: async () => (ref && !status?.error ? fetchOutput(`ldmatrix_plot_${ref}.json`) : null),
  });

  const plotRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (plotJson && plotRef.current && bokehLoaded && (window as any).Bokeh) {
      // Remove any existing Bokeh plots
      const docs = (window as any).Bokeh?.documents || [];
      docs.forEach((doc: any) => doc.clear());

      // Clear the container
      plotRef.current.innerHTML = "";

      // Create new plot using global Bokeh
      (window as any).Bokeh.embed.embed_item(plotJson, plotRef.current);
    }

    // Cleanup on unmount
    return () => {
      const docs = (window as any).Bokeh?.documents || [];
      docs.forEach((doc: any) => doc.clear());
    };
  }, [plotJson, bokehLoaded]);

  const genomeBuildMap: any = {
    grch37: "GRCh37",
    grch38: "GRCh38",
    grch38_high_coverage: "GRCh38 High Coverage",
  };

  return (
    <>
      <hr />
      {status?.warning && <Alert variant="warning">{status.warning}</Alert>}
      {status && !status?.error ? (
        <>
          <Script
            src="https://cdn.bokeh.org/bokeh/release/bokeh-3.4.3.min.js"
            strategy="afterInteractive"
            crossOrigin="anonymous"
            onLoad={() => setBokehLoaded(true)}
          />
          <Container fluid="md" className="justify-content-center">
            <Row className="align-items-center">
              <Col sm={12} className="justify-content-end text-end">
                <Dropdown>
                  <Dropdown.Toggle variant="outline-primary" disabled={!enableExport}>
                    {enableExport ? (
                      "Export Plot"
                    ) : (
                      <>
                        <Spinner size="sm" animation="border" /> Export Plot
                      </>
                    )}
                  </Dropdown.Toggle>
                  <Dropdown.Menu>
                    <Dropdown.Item onClick={() => handleDownload("svg")}>SVG</Dropdown.Item>
                    <Dropdown.Item onClick={() => handleDownload("pdf")}>PDF</Dropdown.Item>
                    <Dropdown.Item onClick={() => handleDownload("png")}>PNG</Dropdown.Item>
                    <Dropdown.Item onClick={() => handleDownload("jpeg")}>JPEG</Dropdown.Item>
                  </Dropdown.Menu>
                </Dropdown>
              </Col>
              <Col sm={12} className="d-flex justify-content-center">
                {plotJson && <div ref={plotRef} className="mt-4" />}
              </Col>
              <Col sm={12} className="d-flex justify-content-center">
                <Image
                  src="/images/LDmatrix_legend.png"
                  title="LDmatrix Legend"
                  alt="LDmatrix legend"
                  width={700}
                  height={0}
                  style={{
                    height: "auto",
                    width: "100%",
                    maxWidth: "700px",
                  }}
                />
              </Col>
              <Col sm={12} className="justify-content-center text-center">
                <a
                  href="https://forgedb.cancer.gov/about/"
                  target="_blank"
                  rel="noopener noreferrer"
                  title="FORGEdb scoring scheme">
                  View scoring scheme for FORGEdb scores
                </a>
              </Col>
            </Row>
            <Row>
              <Col sm="auto">
                <a href={`/LDlinkRestWeb/tmp/d_prime_${ref}.txt`} download>
                  Download D&#39; File
                </a>
              </Col>
              <Col>
                <a href={`/LDlinkRestWeb/tmp/r2_${ref}.txt`} download>
                  Download R<sup>2</sup>
                </a>
              </Col>
            </Row>
          </Container>
        </>
      ) : (
        <Alert variant="danger">{status?.error || "An error has occured"}</Alert>
      )}
    </>
  );
}
