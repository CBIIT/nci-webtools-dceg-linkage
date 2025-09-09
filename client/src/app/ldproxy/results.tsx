"use client";
import { useEffect, useRef } from "react";
import Image from "next/image";
import { Row, Col, Container, Dropdown, Alert } from "react-bootstrap";
import Spinner from "react-bootstrap/Spinner";
import { useQuery, useSuspenseQuery, useQueryClient } from "@tanstack/react-query";
import { createColumnHelper } from "@tanstack/react-table";
import Table from "@/components/table";
import { fetchOutput, fetchOutputStatus } from "@/services/queries";
import { embed } from "@bokeh/bokehjs";
import { FormData } from "./form";

// Helper functions for column rendering
function ldproxy_rs_results_link(data: any) {
  if (!data || !data.includes("rs") || data.length <= 2) return ".";
  return (
    <a
      href={`https://www.ncbi.nlm.nih.gov/snp/${data}`}
      target={`rs_number_${Math.floor(Math.random() * 90000 + 10000)}`}
      rel="noopener noreferrer">
      {data}
    </a>
  );
}

function ldproxy_position_link(data: any, row: any, genomeBuild: string) {
  const chr = row[1];
  const mid_value = parseInt(data);
  const offset = 250;
  const position = `${chr}:${mid_value - offset}-${mid_value + offset}`;
  const build = genomeBuild === "grch37" ? "hg19" : "hg38";
  const url = `https://genome.ucsc.edu/cgi-bin/hgTracks?db=${build}&position=${position}&snp151=pack&hgFind.matches=${row[0]}`;
  return (
    <a href={url} target={`position_${Math.floor(Math.random() * 90000 + 10000)}`} rel="noopener noreferrer">
      {data}
    </a>
  );
}

function ldproxy_FORGEdb_link(score: any, row: any) {
  return (
    <a href={`https://forgedb.cancer.gov/explore?rsid=${row[0]}`} target="_blank" rel="noopener noreferrer">
      {score}
    </a>
  );
}

function ldproxy_regulome_link(data: any, row: any, genomeBuild: string) {
  const chr = row[1];
  const mid_value = parseInt(row[2]);
  const zero_base = mid_value - 1;
  const genome = genomeBuild === "grch37" ? "GRCh37" : "GRCh38";
  const url = `https://www.regulomedb.org/regulome-search/?genome=${genome}&regions=${chr}:${zero_base}-${mid_value}`;
  return (
    <a href={url} target="_blank" rel="noopener noreferrer">
      {data}
    </a>
  );
}

function ldproxy_haploreg_link(row: any) {
  const rs_number = row[0];
  if (!rs_number || rs_number === ".") return "";
  const url = `http://pubs.broadinstitute.org/mammals/haploreg/detail_v4.2.php?id=${rs_number}`;
  const target = `haploreg_${Math.floor(Math.random() * 90000 + 10000)}`;
  return (
    <a href={url} target={target} rel="noopener noreferrer">
      <Image
        src="/images/LDproxy_external_link.png"
        alt="HaploReg Details"
        title="HaploReg Details"
        className="haploreg_external_link"
        width={16}
        height={16}
      />
    </a>
  );
}

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
  const queryClient = useQueryClient();
  const formData = queryClient.getQueryData(["ldproxy-form-data", ref]) as FormData | undefined;
  const { data: results } = useSuspenseQuery({
    queryKey: ["ldproxy_results", ref],
    queryFn: async () => (ref ? fetchOutput(`proxy${ref}.json`) : null),
  });
  const { data: plotJson } = useSuspenseQuery({
    queryKey: ["ldproxy_plot", ref],
    queryFn: async () => (ref && !results?.error ? fetchOutput(`ldproxy_plot_${ref}.json`) : null),
  });
  const { data: enableExport } = useQuery<boolean>({
    queryKey: ["ldproxy-export", ref],
    queryFn: async () => (ref ? fetchOutputStatus(`proxy_plot_${ref}.jpeg`) : false),
    enabled: !!ref && !results?.error,
    refetchInterval: (query) => (query.state.data ? false : 5000),
    retry: 60,
  });

  const plotRef = useRef<HTMLDivElement>(null);
    // Separate scroll container so we don't combine flex centering with horizontal scrolling (which clipped the left axis)
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (plotJson && plotRef.current) {
      // Remove any existing Bokeh plots
      const docs = (window as any).Bokeh?.documents || [];
      docs.forEach((doc: any) => doc.clear());

      // Clear the container
      plotRef.current.innerHTML = "";

      // Create new plot
      embed.embed_item(plotJson, plotRef.current);

      // After Bokeh renders, center horizontally once (without losing ability to scroll fully left)
      requestAnimationFrame(() => {
        if (scrollContainerRef.current) {
          const sc = scrollContainerRef.current;
            const maxScroll = sc.scrollWidth - sc.clientWidth;
            if (maxScroll > 0) {
              sc.scrollLeft = maxScroll / 2;
            }
        }
      });
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
      cell: (info) => ldproxy_rs_results_link(info.getValue()),
    }),
    columnHelper.accessor((row) => row[1], {
      header: "Chr",
      cell: (info) => info.getValue().substring(3),
    }),
    columnHelper.accessor((row) => row[2], {
      header: `Position (${genomeBuildMap[formData?.genome_build ?? "grch37"]})`,
      cell: (info) => ldproxy_position_link(info.getValue(), info.row.original, formData?.genome_build ?? "grch37"),
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
    columnHelper.accessor((row) => row[9], {
      header: "FORGEdb",
      cell: (info) => ldproxy_FORGEdb_link(info.getValue(), info.row.original),
    }),
    columnHelper.accessor((row) => row[10], {
      header: "RegulomeDB",
      cell: (info) => ldproxy_regulome_link(info.getValue(), info.row.original, formData?.genome_build ?? "grch37"),
    }),
    columnHelper.accessor((row) => row[11], {
      header: "HaploReg",
      cell: (info) => ldproxy_haploreg_link(info.row.original),
    }),
    columnHelper.accessor((row) => row[12], {
      header: "Functional Class",
      cell: (info) => info.getValue() || "NA",
    }),
  ];

  return (
    <>
      <hr />
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
            <Col sm={12} className="text-center">
              <div
                ref={scrollContainerRef}
                className="overflow-x-auto"
                style={{ width: "100%" }}
              >
                {plotJson && (
                  <div
                    ref={plotRef}
                    className="mt-4"
                    style={{ display: "inline-block" }}
                  />
                )}
              </div>
            </Col>
          
            <Col sm={12} className="d-flex justify-content-center my-4">
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
            <Col>            
                {results && <Table  title="Proxy Variants" data={results.aaData} columns={columns} />}
            </Col>
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
