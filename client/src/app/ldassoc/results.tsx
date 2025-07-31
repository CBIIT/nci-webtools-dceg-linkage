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

export default function LdAssocResults({ ref }: { ref: string }) {
  const handleDownload = async (format: string) => {
    const url = `/LDlinkRestWeb/tmp/assoc_plot_${ref}.${format}`;
    const response = await fetch(url);
    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = downloadUrl;
    link.download = `assoc_plot_${ref}.${format}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  };

  const queryClient = useQueryClient();
  const formData = queryClient.getQueryData(["ldassoc-form-data", ref]) as FormData | undefined;
  const { data: results } = useSuspenseQuery({
    queryKey: ["ldassoc_results", ref],
    queryFn: async () => (ref ? fetchOutput(`assoc${ref}.json`) : null),
  });
  const { data: plotJson } = useSuspenseQuery({
    queryKey: ["ldassoc_plot", ref],
    queryFn: async () => (ref && !results?.error ? fetchOutput(`ldassoc_plot_${ref}.json`) : null),
  });
  const { data: enableExport } = useQuery<FormData>({
    queryKey: ["ldassoc-export", ref],
    queryFn: async () => (ref ? fetchOutputStatus(`assoc_plot_${ref}.jpeg`) : false),
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
      cell: (info) => {
        const rs = info.getValue();
        if (!rs || rs === ".") return rs;
        const url = `http://www.ncbi.nlm.nih.gov/snp/${rs}`;
        return (
          <a href={url} target="_blank" rel="noopener noreferrer">
            {rs} 
          </a>
        );
      },
    }),
    columnHelper.accessor((row) => row[1], {
      header: "Chr",
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor((row) => row[2], {
      header: `Position (${genomeBuildMap[formData?.genome_build ?? "grch37"]})`,
      cell: (info) => {
        const position = info.getValue();
        const rs = info.row.original[0];
        const chr = info.row.original[1];
        if (!position || !rs || rs === "." || !chr) return position;
        // Show +/-250bp window around position
        const start = Math.max(Number(position) - 250, 0);
        const end = Number(position) + 250;
        const region = `${chr}:${start}-${end}`;
        const params = {
          db: formData?.genome_build === "grch37" ? "hg19" : "hg38",
          position: region,
          snp151: "pack",
          "hgFind.matches": rs,
        };
        const url = `https://genome.ucsc.edu/cgi-bin/hgTracks?${new URLSearchParams(params)}`;
        return (
          <a href={url} target="_blank" rel="noopener noreferrer">
            {position} 
          </a>
        );
      },
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
      header: "Association P-value",
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor((row) => row[10], {
      header: "FORGEdb",
      cell: (info) => {
        const value = info.getValue();
        const rs = info.row.original[0];
        if (!rs || rs === ".") return value;
        const url = `https://forgedb.cancer.gov/explore?rsid=${rs}`;
        return (
          <a href={url} target="_blank" rel="noopener noreferrer">
            {value} 
          </a>
        );
      },
    }),
    columnHelper.accessor((row) => row[11], {
      header: "RegulomeDB",
      cell: (info) => {
        const value = info.getValue();
        const chr = info.row.original[1];
        const position = info.row.original[2];
        if (!chr || !position || !value || value === ".") return value;
        // Use +/-250bp window around position, same as Position column
        const start = Math.max(Number(position) - 250, 0);
        const end = Number(position) + 250;
        const region = `${chr}:${start}-${end}`;
        const genome = formData?.genome_build === "grch37" ? "GRCh37" : "GRCh38";
        const url = `https://www.regulomedb.org/regulome-search?genome=${genome}&regions=${encodeURIComponent(region)}`;
        return (
          <a href={url} target="_blank" rel="noopener noreferrer">{value}</a>
        );
      },
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
      cell: (info) => info.getValue(),
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
            <Col sm={12} className="d-flex justify-content-center">
              {plotJson && <div ref={plotRef} className="mt-4" />}
            </Col>
            <Col sm={12} className="d-flex justify-content-center">
              <Image
                src="/images/LDassoc_legend.png"
                title="LDassoc Legend"
                alt="LDassoc legend"
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
                id="ldassoc-genome"
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
                target="LDassoc-forgedb-browser_FOREGEdb"
                title="FORGEdb scoring scheme">
                View scoring scheme for FORGEdb scores
              </a>
            </Col>
            <Col sm={12} className="justify-content-center text-center">
              <a
                href="https://www.regulomedb.org/regulome-help/"
                target="LDassoc-genome-browser_RegulomeDB"
                title="RegulomeDB scoring scheme">
                View scoring scheme for RegulomeDB scores
              </a>
            </Col>
            <Col sm={12} className="justify-content-center">
              <ul style={{ listStyleType: "none" }}>
                <li>
                  Number of Individuals: <b>{results.report.statistics.individuals}</b>
                </li>
                <li>
                  SNPs in Region: <b>{results.report.statistics.in_region}</b>
                </li>
                <li>
                  Run time: <b>{Number(results.report.statistics.runtime).toFixed(2)}</b> seconds
                </li>
              </ul>
            </Col>
          </Row>
          <Row>
            <Col>{results && <Table title="Association Results" data={results.aaData} columns={columns} />}</Col>
          </Row>
          <Row>
            <Col>
              <a href={`/LDlinkRestWeb/tmp/assoc${ref}.txt`} download>
                Download association data for all variants
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
