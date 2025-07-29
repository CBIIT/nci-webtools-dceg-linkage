"use client";
import { Row, Col, Container, Alert } from "react-bootstrap";
import { useSuspenseQuery, useQueryClient } from "@tanstack/react-query";
import { fetchOutput } from "@/services/queries";
import { FormData, ResultsData } from "./types";
import { genomeBuildMap } from "@/store";
import { useState } from "react";
import "./styles.scss";

export default function LdTraitResults({ ref }: { ref: string }) {
  const [activeKey, setActiveKey] = useState<string | null>(null);
  const [showWarnings, setShowWarnings] = useState(false);

  const queryClient = useQueryClient();
  const formData = queryClient.getQueryData(["ldtrait-form-data", ref]) as FormData | undefined;

  const { data: results } = useSuspenseQuery<ResultsData>({
    queryKey: ["ldtrait_results", ref],
    queryFn: async () => {
      if (!ref) return null;
      console.log("Fetching data for ref:", ref);
      try {
        let data = await fetchOutput(`ldtrait${ref}.json`);
        console.log("Raw API response:", data);
        
        // Ensure we're working with an object, not a string
        const parsed = typeof data === 'string' ? JSON.parse(data) : data;
        console.log("Parsed results:", parsed);
        
        if (parsed.error) {
          throw new Error(parsed.error);
        }
        
        return parsed;
      } catch (e) {
        console.error("Error fetching or parsing results:", e);
        throw e;
      }
    },
    retry: 3,
  });

  // Early return if no meaningful data
  if (!results || !results.thinned_snps || !results.details) {
    return <Alert variant="warning">No data available</Alert>;
  }

  return (
    <>
      {!results.error ? (
        <Container fluid="fluid" className="p-3" id="ldtrait-results-container">
          <Row id="ldtrait-table-container">
            <Col md={2} className="ldtrait-table-scroller">
              <div>Variants in LD with GWAS Catalog</div>
              <table id="ldtrait-table-thin" className="table table-striped">
                <thead>
                  <tr>
                    <th className="rs-number">RS Number</th>
                  </tr>
                </thead>
                <tbody id="ldtrait-snp-list">
                  {results.thinned_snps.map((snp: string) => (
                    <tr key={snp} onClick={() => setActiveKey(snp)} className={activeKey === snp ? "active" : ""}>
                      <td>
                        <a className="ldtrait-link">{snp}</a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {(results.queryWarnings?.aaData?.length ?? 0) > 0 && (
                <a
                  id="ldtrait-warnings-button"
                  title="View details."
                  onClick={() => setShowWarnings(!showWarnings)}
                  style={{ cursor: "pointer" }}>
                  {showWarnings ? "Hide" : "Show"} Variants with Warnings
                </a>
              )}
            </Col>

            <Col md={10} className="ldtrait-table-scroller" id="ldtrait-detail">
              {activeKey && (
                <>
                  <Row>
                    <Col>
                      <div id="ldtrait-detail-title">Details for {activeKey}</div>
                    </Col>
                  </Row>
                  <table id="new-ldtrait" className="table table-striped table-chip">
                    <thead title="Shift-click column headers to sort by multiple levels">
                      <tr>
                        <th className="dt-head-left dt-body-left">GWAS Trait</th>
                        <th className="dt-head-left dt-body-left">PMID</th>
                        <th className="dt-head-left dt-body-left">RS Number</th>
                        <th className="dt-head-left dt-body-left">Position ({genomeBuildMap[formData?.genome_build || "grch37"]})</th>
                        <th className="dt-head-left dt-body-left">Alleles</th>
                        <th className="dt-head-left dt-body-left">R²</th>
                        <th className="dt-head-left dt-body-left">D'</th>
                        <th className="dt-head-left dt-body-left">Risk Allele</th>
                        <th className="dt-head-left dt-body-left">Effect Size</th>
                        <th className="dt-head-left dt-body-left">P-value</th>
                      </tr>
                    </thead>
                    <tbody>
                      {results.thinned_snps.includes(activeKey) &&
                        results.details[activeKey]?.aaData.map((row, i) => (
                          <tr key={`${activeKey}-${i}`}>
                            <td>{row[0]}</td>
                            <td>
                              <a href={`https://pubmed.ncbi.nlm.nih.gov/${row[1]}`} target="_blank" rel="noopener noreferrer">
                                {row[1]}
                              </a>
                            </td>
                            <td>
                              <a href={`http://www.ncbi.nlm.nih.gov/snp/${row[2]}`} target="_blank" rel="noopener noreferrer">
                                {row[2]}
                              </a>
                            </td>
                            <td>{row[3]}</td>
                            <td>{row[4]}</td>
                            <td>{typeof row[5] === 'number' ? row[5].toFixed(3) : row[5]}</td>
                            <td>{typeof row[6] === 'number' ? row[6].toFixed(3) : row[6]}</td>
                            <td>{row[8]}</td>
                            <td>{row[10]}</td>
                            <td>{row[11]}</td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </>
              )}

              {showWarnings && (results.queryWarnings?.aaData?.length ?? 0) > 0 && (
                <table id="new-ldtrait-query-warnings" className="table table-striped table-chip">
                  <caption>Query Variants with Warnings</caption>
                  <thead>
                    <tr>
                      <th className="dt-head-left dt-body-left">Variant</th>
                      <th className="dt-head-left dt-body-left">Position ({genomeBuildMap[formData?.genome_build || "grch37"]})</th>
                      <th className="dt-head-left dt-body-left">Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.queryWarnings?.aaData?.map((warning, i) => (
                      <tr key={i}>
                        <td>{warning[0]}</td>
                        <td>{warning[1]}</td>
                        <td>{warning[2]}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {!activeKey && !showWarnings && (
                <div id="ldtrait-initial-message">Click a variant on the left to view details.</div>
              )}
            </Col>
          </Row>

          {results.warning && (
            <Row className="mt-3">
              <Col>
                <Alert variant="warning">{results.warning}</Alert>
              </Col>
            </Row>
          )}

          <Row className="mt-3">
            <Col>
              <a href={`/LDlinkRestWeb/tmp/trait_variants_annotated_${ref}.txt`} download>
                Download GWAS Catalog annotated variant list
              </a>
            </Col>
          </Row>
          <Row className="mt-2">
            <Col>
              <i>GWAS Catalog last updated on <span id="ldtrait-timestamp">...</span></i>
            </Col>
          </Row>
        </Container>
      ) : (
        <Alert variant="danger">{results.error || "An error has occurred"}</Alert>
      )}
    </>
  );
}
