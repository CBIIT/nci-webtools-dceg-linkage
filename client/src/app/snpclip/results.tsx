"use client";
import { Row, Col, Container, Table, Nav } from "react-bootstrap";
import { useQuery, useSuspenseQuery } from "@tanstack/react-query";
import { fetchOutput } from "@/services/queries";
import { FormData, ResultsData, Detail, Warning } from "./types";
import { genomeBuildMap } from "@/store";
import { useState } from "react";
import "./styles.scss";

export default function SNPClipResults({ ref_id }: { ref_id: string }) {
  const [activeKey, setActiveKey] = useState<string | null>(null);
  const [showWarnings, setShowWarnings] = useState(false);

  const { data: formData } = useQuery<FormData>({
    queryKey: ["snpclip-form-data", ref_id],
    enabled: !!ref_id,
    staleTime: Infinity,
  });

  const { data: results } = useSuspenseQuery<ResultsData>({
    queryKey: ["snpclip_results", ref_id],
    queryFn: async () => (ref_id ? fetchOutput(`snpclip${ref_id}.json`) : null),
  });

  const details: string[] = results?.details || [];
  const warnings: string[] = results?.warnings || [];
  const thinnedSnps = results?.snps_ld_pruned || [];

  const selectedDetail = activeKey ? details.find((d) => d.startsWith(activeKey)) : null;

  const getUCSCUrl = (snp: string) => {
    const parts = snp.split("\t");
    const rsNumber = parts[0];
    const position = parts[1];
    if (!position) return "#";
    const [chr, pos] = position.split(":");
    const start = Math.max(0, parseInt(pos) - 250);
    const end = parseInt(pos) + 250;
    const newPosition = `${chr}:${start}-${end}`;
    const db = formData?.genome_build === "grch37" ? "hg19" : "hg38";
    return `https://genome.ucsc.edu/cgi-bin/hgTracks?db=${db}&position=${newPosition}&snp151=pack&hgFind.matches=${rsNumber}`;
  };

  const renderRow = (data: string, isWarning = false) => {
    const [rs_number, position, alleles, comment] = data.split("\t");
    return (
      <tr key={rs_number}>
        <td>
          <a href={`http://www.ncbi.nlm.nih.gov/snp/${rs_number}`} target="_blank" rel="noopener noreferrer">
            {rs_number}
          </a>
        </td>
        <td>
          <a href={getUCSCUrl(data)} target="_blank" rel="noopener noreferrer">
            {position}
          </a>
        </td>
        <td>{alleles}</td>
        <td>{comment}</td>
      </tr>
    );
  };

  return (
    <Container fluid="fluid" className="p-3 jumbotron">
      <Row>
        <Col md={3} xl={2}>
          <div className="snpclip-table-scroller">
            <Table striped bordered hover size="sm">
              <caption>LD Thinned Variant List</caption>
              <thead>
                <tr>
                  <th>RS Number</th>
                </tr>
              </thead>
              <tbody>
                {thinnedSnps.map((snp, i) => (
                  <tr
                    key={i}
                    className={activeKey === snp ? "active-row" : ""}
                    onClick={() => {
                      setActiveKey(snp);
                      setShowWarnings(false);
                    }}>
                    <td>{snp}</td>
                  </tr>
                ))}
              </tbody>
            </Table>
            {warnings.length > 0 && (
              <Nav.Link onClick={() => setShowWarnings(true)} className="text-primary">
                Variants with Warnings
              </Nav.Link>
            )}
          </div>
        </Col>
        <Col md={9} xl={10}>
          <div className="snpclip-table-scroller">
            {showWarnings ? (
              <Table striped bordered hover size="sm">
                <caption>Variants With Warnings</caption>
                <thead>
                  <tr>
                    <th>RS Number</th>
                    <th>Position ({genomeBuildMap[formData?.genome_build || "grch37"]})</th>
                    <th>Alleles</th>
                    <th>Details</th>
                  </tr>
                </thead>
                <tbody>
                  {warnings.map((warning) => renderRow(warning, true))}
                </tbody>
              </Table>
            ) : selectedDetail ? (
              <Table striped bordered hover size="sm">
                <caption>Details for {selectedDetail.split("\t")[0]}</caption>
                <thead>
                  <tr>
                    <th>RS Number</th>
                    <th>Position ({genomeBuildMap[formData?.genome_build || "grch37"]})</th>
                    <th>Alleles</th>
                    <th>Details</th>
                  </tr>
                </thead>
                <tbody>{renderRow(selectedDetail)}</tbody>
              </Table>
            ) : (
              <div>Click a variant on the left to view details.</div>
            )}
          </div>
        </Col>
      </Row>
      <Row className="mt-3">
        <Col>
          <a href={`/LDlinkRestWeb/tmp/snpclip_snps_${ref_id}.txt`} download className="me-4">
            Download Thinned Variant List
          </a>
          <a href={`/LDlinkRestWeb/tmp/snpclip_details_${ref_id}.txt`} download>
            Download Thinned Variant List with Details
          </a>
        </Col>
      </Row>
    </Container>
  );
}