"use client";
import { Row, Col, Container, Alert } from "react-bootstrap";
import { useSuspenseQuery, useQueryClient } from "@tanstack/react-query";
import { fetchOutput } from "@/services/queries";
import { FormData, ResultsData, SNP, Haplotype } from "./types";
import { genomeBuildMap } from "@/store";
import "./styles.scss";

export default function LdTraitResults({ ref }: { ref: string }) {
  const queryClient = useQueryClient();
  const formData = queryClient.getQueryData(["ldtrait-form-data", ref]) as FormData | undefined;

  const { data: results } = useSuspenseQuery<ResultsData>({
    queryKey: ["ldtrait_results", ref],
    queryFn: async () => {
      if (!ref) return null;
      const data = await fetchOutput(`ldtrait${ref}.json`);
      console.log("Raw API response:", data);
      try {
        // Try parsing if it's a string
        const parsed = typeof data === 'string' ? JSON.parse(data) : data;
        console.log("Parsed results:", parsed);
        return parsed;
      } catch (e) {
        console.error("Error parsing results:", e);
        return data;
      }
    },
  });

  console.log("Rendering with results:", results);
  
  // Early return if no meaningful data
  if (!results || !results.query_snps || !results.thinned_snps || !results.details) {
    return <Alert variant="warning">No data available</Alert>;
  }

  return (
    <>
      {!results.error ? (
        <Container fluid="md" className="justify-content-center">
          <Row>
            <Col sm="auto">
              <table className="table table-condensed w-auto">
                <thead>
                  <tr>
                    <th>GWAS Trait</th>
                    <th>PMID</th>
                    <th>RS Number</th>
                    <th>Position ({genomeBuildMap[formData?.genome_build || "grch37"]})</th>
                    <th>Alleles</th>
                    <th>R²</th>
                    <th>D'</th>
                    <th>Risk Allele</th>
                    <th>Effect Size</th>
                    <th>P-value</th>
                  </tr>
                </thead>
                <tfoot>
                  <tr>
                    <td colSpan={2} rowSpan={2}></td>
                    <td>Haplotype Count</td>
                  </tr>
                  <tr>
                    <td style={{ whiteSpace: "nowrap" }}>Haplotype Frequency</td>
                  </tr>
                </tfoot>
                <tbody className="table-body-border">
                  {results.thinned_snps.map((snp) => 
                    results.details[snp]?.aaData.map((row, i) => (
                      <tr key={`${snp}-${i}`}>
                        <td>{row[0]}</td>
                        <td>
                          <a href={`https://pubmed.ncbi.nlm.nih.gov/${row[1]}`} target="_blank" rel="noopener">
                            {row[1]}
                          </a>
                        </td>
                        <td>
                          <a href={`http://www.ncbi.nlm.nih.gov/snp/${row[2]}`} target="_blank" rel="noopener">
                            {row[2]}
                          </a>
                        </td>
                        <td>{row[3]}</td>
                        <td>{row[4]}</td>
                        <td>{row[5].toFixed(3)}</td>
                        <td>{row[6].toFixed(3)}</td>
                        <td>{row[8]}</td>
                        <td>{row[10]}</td>
                        <td>{row[11]}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </Col>
          </Row>
          {results.details.queryWarnings?.aaData?.length > 0 && (
            <Row className="mt-3">
              <Col>
                <Alert variant="warning">
                  <h4>Warnings:</h4>
                  <ul>
                    {results.details.queryWarnings.aaData.map((warning, i) => (
                      <li key={i}>{warning.join(": ")}</li>
                    ))}
                  </ul>
                </Alert>
              </Col>
            </Row>
          )}
          <Row className="mt-3">
            <Col sm="auto">
              <a href={`/LDlinkRestWeb/tmp/trait_variants_annotated_${ref}.txt`} download>
                Download Results
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
