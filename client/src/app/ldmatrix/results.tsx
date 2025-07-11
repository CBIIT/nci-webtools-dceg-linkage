"use client";
import { useEffect, useRef } from "react";
import Script from "next/script";
import Image from "next/image";
import { Row, Col, Container, Dropdown } from "react-bootstrap";
import Spinner from "react-bootstrap/Spinner";
import { useQuery, useSuspenseQuery } from "@tanstack/react-query";
import { fetchOutput, fetchOutputStatus } from "@/services/queries";
import { FormData } from "./types";

export default function LdAMatrixResults({ ref }: { ref: string }) {
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

  const { data: formData } = useQuery<FormData>({
    queryKey: ["ldmatrix-form-data", ref],
    enabled: !!ref,
    queryFn: async () => {
      return {} as FormData;
    },
  });
  const { data: enableExport } = useQuery<FormData>({
    queryKey: ["ldmatrix-export", ref],
    queryFn: async () => (ref ? fetchOutputStatus(`matrix_plot_${ref}.jpeg`) : false),
    enabled: !!ref,
    refetchInterval: 5000, // Check every 5 seconds
    retry: 60,
  });

  const { data: plotJson } = useSuspenseQuery({
    queryKey: ["ldmatrix_plot", ref],
    queryFn: async () => (ref ? fetchOutput(`ldmatrix_plot_${ref}.json`) : null),
  });

  const plotRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (plotJson && plotRef.current && (window as any).Bokeh) {
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
  }, [plotJson]);

  const genomeBuildMap: any = {
    grch37: "GRCh37",
    grch38: "GRCh38",
    grch38_high_coverage: "GRCh38 High Coverage",
  };

  return (
    <>
      <Script
        src="https://cdn.bokeh.org/bokeh/release/bokeh-3.4.3.min.js"
        strategy="afterInteractive"
        crossOrigin="anonymous"
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
              id="ldmatrix-legend"
              src="/images/LDmatrix_legend.png"
              title="LDmatrix Legend"
              alt="LDmatrix legend"
              width={700}
              height={0}
              priority
              style={{
                height: "auto",
                width: "100%",
                maxWidth: "700px",
              }}
            />
          </Col>
          <Col sm={12} className="justify-content-center text-center">
            <a href="https://forgedb.cancer.gov/about/" target="_blank" title="FORGEdb scoring scheme">
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
  );
}
