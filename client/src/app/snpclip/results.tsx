"use client";
import { Row, Col, Container, Form, Alert } from "react-bootstrap";
import { useSuspenseQuery, useQueryClient } from "@tanstack/react-query";
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
    queryFn: async () => (ref_id ? fetchOutput(`snpclip${ref_id}.json`) : null),
  });

  // Process warnings (equivalent to populateSNPwarnings from LDlink.js)
  const { warnings, thinnedSnps } = useMemo(() => {
    if (!results?.details) return { warnings: [] as Warning[], thinnedSnps: results?.snp_list || [] };

    const snpList = [...(results.snp_list || [])];
    const warnings: Warning[] = Object.entries(results.details)
      .filter(
        ([, [, , comment]]) => !comment || (!comment.includes("Variant kept.") && !comment.includes("Variant in LD"))
      )
      .map(([rsNumber, [position, alleles, comment]]) => {
        // Remove from SNP list
        const index = snpList.indexOf(rsNumber);
        if (index > -1) snpList.splice(index, 1);
        return {
          rs_number: rsNumber,
          position: position || "",
          alleles: alleles || "",
          comment: comment || "",
        };
      });

    return { warnings, thinnedSnps: snpList };
  }, [results]);

  const detailsToShow = useMemo(() => {
    const details = results?.details || {};
    if (!activeKey || !details) {
      return [] as Detail[];
    }
    const allDetails = Object.entries(details);
    const relevantDetails: Detail[] = [];
    const match = `Variant in LD with ${activeKey}`;

    for (const [rs_number, [position, alleles, comment]] of allDetails) {
      if (rs_number === activeKey) {
        if (comment?.includes("Variant kept.")) {
          relevantDetails.push({
            rs_number,
            position: position || "",
            alleles: alleles || "",
            comment: comment || "",
          });
        }
      } else if (comment?.includes(match)) {
        relevantDetails.push({
          rs_number,
          position: position || "",
          alleles: alleles || "",
          comment: comment || "",
        });
      }
    }
    return relevantDetails;
  }, [activeKey, results?.details]);

  const getUCSCUrl = (rsNumber: string, position: string) => {
    if (!position) return "#";
    const [chr, pos] = position.split(":");
    const start = Math.max(0, parseInt(pos) - 250);
    const end = parseInt(pos) + 250;
    const newPosition = `${chr}:${start}-${end}`;
    const db = formData?.genome_build === "grch37" ? "hg19" : "hg38";
    return `https://genome.ucsc.edu/cgi-bin/hgTracks?db=${db}&position=${newPosition}&hgFind.matches=${rsNumber}`;
  };

  const renderRow = (item: Detail | Warning) => {
    return (
      <tr key={item.rs_number}>
        <td>
          <a href={`http://www.ncbi.nlm.nih.gov/snp/${item.rs_number}`} target="_blank" rel="noopener noreferrer">
            {item.rs_number}
          </a>
        </td>
        <td>
          <a href={getUCSCUrl(item.rs_number, item.position)} target="_blank" rel="noopener noreferrer">
            {item.position}
          </a>
        </td>
        <td>{item.alleles}</td>
        <td>{item.comment}</td>
      </tr>
    );
  };

  return (
    <>
      <hr />
      {results ? (
        <Container fluid="fluid" className="p-3" id="snpclip-results-container">
          <Row id="snpclip-table-container">
            <Col md={2} className="snpclip-table-scroller">
              <h5>LD Thinned Variant List</h5>
              <table id="snpclip-table-thin" className="table table-striped">
                <thead>
                  <tr>
                    <th className="rs-number">RS Number</th>
                  </tr>
                </thead>
                <tbody id="snpclip-snp-list">
                  {thinnedSnps.map((snp: string) => (
                    <tr
                      key={snp}
                      onClick={() => (setShowWarnings(false), setActiveKey(snp))}
                      className={activeKey === snp ? "active" : ""}>
                      <td>
                        <a className="snpclip-link">{snp}</a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {warnings.length > 0 && (
                <Form className="my-3">
                  <Form.Check
                    type="switch"
                    id="view-warnings"
                    label="Variants With Warnings"
                    checked={showWarnings}
                    onChange={() => setShowWarnings(!showWarnings)}
                  />
                </Form>
              )}
            </Col>

            <Col md={9} className="snpclip-table-scroller" id="snpclip-detail">
              {activeKey && !showWarnings && (
                <div>
                  <Row>
                    <Col col={12}>
                      <h5>Details for {activeKey}</h5>
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
                    <tbody>{detailsToShow.map((detail) => renderRow(detail))}</tbody>
                  </table>
                </div>
              )}

              {showWarnings && warnings.length > 0 && (
                <div>
                  <h5>Variants With Warnings</h5>
                  <table id="snpclip-warnings" className="table table-striped table-chip">
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
                    <tbody style={{ border: "1px solid #ccc" }}>{warnings.map((warning) => renderRow(warning))}</tbody>
                  </table>
                </div>
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
      ) : (
        <Alert variant="danger">{"An error has occured"}</Alert>
      )}
    </>
  );
}
