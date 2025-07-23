"use client";
import { Row, Col, Container, Table, Nav } from "react-bootstrap";
import {  useSuspenseQuery, useQueryClient } from "@tanstack/react-query";
import { fetchOutput } from "@/services/queries";
import { FormData, ResultsData, Detail, Warning } from "./types";
import { genomeBuildMap } from "@/store";
import { useState, useMemo } from "react";
import "./styles.scss";

export default function SNPClipResults({ ref_id }: { ref_id: string }) {
  const [activeKey, setActiveKey] = useState<string | null>(null);
  const [showWarnings, setShowWarnings] = useState(false);

  const queryClient = useQueryClient();
  const formData = queryClient.getQueryData(["snpclip-form-data", ref_id]) as FormData | undefined;

  const { data: results } = useSuspenseQuery<ResultsData>({
    queryKey: ["snpclip_results", ref_id],
    queryFn: async () => {
      if (!ref_id) return null;
      const output = await fetchOutput(`snpclip${ref_id}.json`);
      return typeof output === "string" ? JSON.parse(output) : output;
    },
  });

  const details = results?.details || {};
  const warnings = results?.warnings || [];
  const thinnedSnps = results?.snp_list || [];

  const detailsToShow = useMemo(() => {
    if (!activeKey || !details) {
      return [];
    }
    const allDetails = Object.entries(details);
    const relevantDetails: [string, string[]][] = [];
    const match = `Variant in LD with ${activeKey}`;

    for (const [rs_number, value] of allDetails) {
      const comment = value[2];
      if (rs_number === activeKey) {
        if (comment?.includes("Variant kept.")) {
          relevantDetails.push([rs_number, value]);
        }
      } else if (comment?.includes(match)) {
        relevantDetails.push([rs_number, value]);
      }
    }
    return relevantDetails;
  }, [activeKey, details]);

  const getUCSCUrl = (rsNumber: string, position: string) => {
    if (!position) return "#";
    const [chr, pos] = position.split(":");
    const start = Math.max(0, parseInt(pos) - 250);
    const end = parseInt(pos) + 250;
    const newPosition = `${chr}:${start}-${end}`;
    const db = formData?.genome_build === "grch37" ? "hg19" : "hg38";
    return `https://genome.ucsc.edu/cgi-bin/hgTracks?db=${db}&position=${newPosition}&hgFind.matches=${rsNumber}`;
  };

  const renderRow = (rs_number: string, data: string[], isWarning = false) => {
    const [position, alleles, comment] = data;
    return (
      <tr key={rs_number}>
        <td>
          <a href={`http://www.ncbi.nlm.nih.gov/snp/${rs_number}`} target="_blank" rel="noopener noreferrer">
            {rs_number}
          </a>
        </td>
        <td>
          <a href={getUCSCUrl(rs_number, position)} target="_blank" rel="noopener noreferrer">
            {position}
          </a>
        </td>
        <td>{alleles}</td>
        <td>{comment}</td>
      </tr>
    );
  };

  return (
    <Container fluid="fluid" className="p-3" id="snpclip-results-container">        
      <Row id="snpclip-table-container">            
        <Col className="col-md-2 snpclip-table-scroller">
          <div>LD Thinned Variant List</div>               
          <table id="snpclip-table-thin" className="table table-striped">               
            <thead>
              <tr>
                <th>RS Number</th>
              </tr>
            </thead>
            <tbody id="snpclip-snp-list">
              {thinnedSnps.map((snp: string) => (
                <tr key={snp} onClick={() => setActiveKey(snp)} className={activeKey === snp ? "active" : ""}>
                  <td>
                    <a className="snpclip-link">{snp}</a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {warnings.length > 0 && (
            <a
              id="snpclip-warnings-button"
              title="View details."
              onClick={() => setShowWarnings(!showWarnings)}
              style={{ cursor: "pointer" }}>
              {showWarnings ? "Hide" : "Show"} Variants with Warnings
            </a>
          )}
        </Col>

        <Col className="col-sm-9 col-md-9 snpclip-table-scroller" id="snpclip-detail">

          {activeKey && (
            <div>
            <Row>
              <Col col={12}>
                <div id="snpclip-detail-title">Details for {activeKey}</div>
              </Col>
            </Row>
            <table id="snpclip-details" className="table table-striped table-chip">                  
              <thead>
                <tr>
                  <th>RS Number</th>
                  <th>
                    Position (
                    <span className="snpclip-position-genome-build-header">
                      {genomeBuildMap[formData?.genome_build || "grch37"]}
                    </span>
                    )
                  </th>
                  <th>Alleles</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                {detailsToShow.map(([rs_number, detail]) => renderRow(rs_number, detail))}
              </tbody>
            </table>
            </div>
          )}

          {showWarnings && warnings.length > 0 && (
            <table id="snpclip-warnings" className="table table-striped table-chip">
              <caption>Variants With Warnings</caption>
              <thead>
                <tr>
                  <th>RS Number</th>
                  <th>
                    Position (
                    <span className="snpclip-position-genome-build-header">
                      {genomeBuildMap[formData?.genome_build || "grch37"]}
                    </span>
                    )
                  </th>
                  <th>Alleles</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody style={{ border: "1px solid #ccc" }}>
                {warnings.map((warning: string[]) => renderRow(warning[0], warning.slice(1), true))}
              </tbody>
            </table>
          )}

          {!activeKey && !showWarnings && (
            <div id="snpclip-initial-message">Click a variant on the left to view details.</div>
          )}
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