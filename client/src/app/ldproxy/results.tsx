"use client";
import { useEffect, useRef } from "react";
import Image from "next/image";
import { Row, Col, Container, Dropdown, Alert } from "react-bootstrap";
import Spinner from "react-bootstrap/Spinner";
import { useQuery, useSuspenseQuery } from "@tanstack/react-query";
import { createColumnHelper } from "@tanstack/react-table";
import Table from "@/components/table";
import { fetchOutput, fetchOutputStatus } from "@/services/queries";
import { embed } from "@bokeh/bokehjs";
import { FormData } from "./form";

export default function LdProxyResults({ ref }: { ref: string }) {
  const handleDownload = async (format: string) => {
    const url = `/LDlinkRestWeb/tmp/proxy_plot_${ref}.${format}`;
    const response = await fetch(url);
    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = downloadUrl;
    link.download = `proxy_plot_${ref}.${format}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  };

  const { data: formData } = useQuery<FormData>({
    queryKey: ["ldproxy-form-data", ref],
    enabled: !!ref,
    queryFn: async () => {
      return {} as FormData;
    },
  });
  const { data: results } = useSuspenseQuery({
    queryKey: ["ldproxy_results", ref],
    queryFn: async () => (ref ? fetchOutput(`proxy${ref}.json`) : null),
  });
  const { data: plotJson } = useSuspenseQuery({
    queryKey: ["ldproxy_plot", ref],
    queryFn: async () => (ref && !results?.error ? fetchOutput(`ldproxy_plot_${ref}.json`) : null),
  });
  const { data: enableExport } = useQuery<FormData>({
    queryKey: ["ldproxy-export", ref],
    queryFn: async () => (ref ? fetchOutputStatus(`proxy_plot_${ref}.jpeg`) : false),
    enabled: !!ref && !results?.error,
    refetchInterval: 5000, // Check every 5 seconds
    retry: 60,
  });

  const plotRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (plotJson && plotRef.current) {
      // Remove any existing Bokeh plots
      const docs = (window as any).Bokeh?.documents || [];
      docs.forEach((doc: any) => doc.clear());

      // Clear the container
      plotRef.current.innerHTML = "";

      // Create new plot
      embed.embed_item(plotJson, plotRef.current);
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

  const columnHelper = createColumnHelper<any>();
  const columns = [
    columnHelper.accessor((row) => row[0], {
      header: "RS Number",
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor((row) => row[1], {
      header: "Chr",
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor((row) => row[2], {
      header: `Position (${genomeBuildMap[formData?.genome_build ?? "grch37"]})`,
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor((row) => row[3], {
      header: "Alleles",
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor((row) => row[4], {
      header: "MAF",
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor((row) => row[5], {
      header: "Distance",
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor((row) => row[6], {
      header: "D'",
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor((row) => row[7], {
      header: "R²",
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor((row) => row[8], {
      header: "Correlated Alleles",
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor((row) => row[10], {
      header: "FORGEdb",
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor((row) => row[11], {
      header: "RegulomeDB",
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor((row) => row[12], {
      header: "HaploReg",
      cell: (info) => {
        const rs = info.row.original[0];
        if (!rs || rs === ".") return "";
        const url = `http://pubs.broadinstitute.org/mammals/haploreg/detail_v4.2.php?id=${rs}`;
        return (
          <a href={url} target="_blank" rel="noopener noreferrer">
            Link <i className="bi bi-box-arrow-up-right"></i>
          </a>
        );
      },
    }),
    columnHelper.accessor((row) => row[13], {
      header: "Functional Class",
      cell: (info) => info.getValue() || "NA",
    }),
  ];

  return (
    <>
      {results && !results?.error ? (
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
                src="/images/LDproxy_legend.png"
                title="LDproxy Legend"
                alt="LDproxy legend"
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
                id="ldproxy-genome"
                href={`https://genome.ucsc.edu/cgi-bin/hgTracks?db=${
                  formData?.genome_build === "grch37" ? "hg19" : "hg38"
                }&hgt.customText=http://${location.hostname}/LDlinkRestWeb/tmp/track${ref}.txt`}
                target="LDProxy-genome-browser_UCSC"
                title="Genome Browser">
                View{" "}
                {(formData as any)?.dprime ? (
                  "D'"
                ) : (
                  <span>
                    R<sup>2</sup>
                  </span>
                )}{" "}
                data in UCSC Genome Browser
              </a>
            </Col>
            <Col sm={12} className="justify-content-center text-center">
              <a
                href="https://forgedb.cancer.gov/about/"
                target="LDproxy-forgedb-browser_FOREGEdb"
                title="FORGEdb scoring scheme">
                View scoring scheme for FORGEdb scores
              </a>
            </Col>
            <Col sm={12} className="justify-content-center text-center">
              <a
                href="https://www.regulomedb.org/regulome-help/"
                target="LDproxy-genome-browser_RegulomeDB"
                title="RegulomeDB scoring scheme">
                View scoring scheme for RegulomeDB scores
              </a>
            </Col>
          </Row>
          <Row>
            <Col>{results && <Table title="Proxy Variants" data={results.aaData} columns={columns} />}</Col>
          </Row>
          <Row>
            <Col>
              <a href={`/LDlinkRestWeb/tmp/proxy${ref}.txt`} download>
                Download all proxy variants
              </a>
            </Col>
          </Row>
        </Container>
      ) : (
        <Alert variant="danger">{results?.error || "An error has occured"}</Alert>
      )}
    </>
  );
}
