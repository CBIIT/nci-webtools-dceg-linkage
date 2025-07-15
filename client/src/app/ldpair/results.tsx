"use client";
import { Row, Col, Container, Alert } from "react-bootstrap";
import { useQuery, useSuspenseQuery } from "@tanstack/react-query";
import { fetchOutput } from "@/services/queries";
import { FormData, ResultsData } from "./types";
import "./styles.scss";

export default function LdPairResults({ ref }: { ref: string }) {
  // Helper to get NCBI SNP URL
  function getNcbiSnpUrl(rsnum?: string) {
    if (!rsnum) return undefined;
    // Ensure rsnum starts with 'rs'
    return `https://www.ncbi.nlm.nih.gov/snp/${rsnum.replace(/^rs/, "")}`;
  }
  // Helper to get UCSC Genome Browser URL
  function getUcscUrl(coord?: string, rsnum?: string, genomeBuild?: string) {
    if (!coord || !rsnum) return undefined;
    const [chr, pos] = coord.split(":");
    const mid = parseInt(pos);
    const offset = 250;
    const range = `${mid - offset}-${mid + offset}`;
    const db = genomeBuild === "grch37" ? "hg19" : "hg38";
    const params = new URLSearchParams({
      db,
      "position": `${chr}:${range}`,
      "snp151": "pack",
      "hgFind.matches": rsnum,
    });
    return `https://genome.ucsc.edu/cgi-bin/hgTracks?${params.toString()}`;
  }

  const { data: formData } = useQuery<FormData>({
    queryKey: ["ldpair-form-data", ref],
    enabled: !!ref,
    queryFn: async () => {
      return {} as FormData;
    },
  });

  const { data: results } = useSuspenseQuery<ResultsData>({
    queryKey: ["ldpair_results", ref],
    queryFn: async () => (ref ? fetchOutput(`ldpair${ref}.json`) : null),
  });
  console.log(results);
  console.log(formData);
  return (
    <>
      {results && !results?.error ? (
        <Container fluid="md" className="justify-content-center">
          {/* Main LDpair Table */}
          <Row>
            <Col>
              <table className="ldpair-table w-100">
                <tbody>
                  {/* SNP 1 rsnum and coordinates */}
                  <tr>
                    <td></td>
                    <td></td>
                    <td colSpan={2} className="text-center">
                      <div>
                        <a
                          href={getNcbiSnpUrl(results.snp2?.rsnum)}
                          target="_blank"
                          rel="noopener noreferrer"
                          title="Cluster Report:">
                          {results.snp2?.rsnum}
                        </a>
                      </div>
                      <div>
                        <a
                          href={getUcscUrl(results.snp2?.coord, results.snp2?.rsnum, formData.genome_build)}
                          target="_blank"
                          rel="noopener noreferrer"
                          title="Genome Browser">
                          {results.snp2?.coord}
                        </a>
                      </div>
                    </td>
                    <td></td>
                    <td></td>
                  </tr>
                  {/* Header row */}
                  <tr>
                    <td></td>
                    <td></td>
                    <td className="text-center">{results.snp2?.allele_1?.allele}</td>
                    <td className="text-center">{results.snp2?.allele_2?.allele}</td>
                    <td></td>
                    <td></td>
                  </tr>
                  {/* Row 2 */}
                  <tr>
                    <td className="text-center align-middle" rowSpan={2}>
                      <div>
                        <a
                          href={getNcbiSnpUrl(results.snp1?.rsnum)}
                          target="_blank"
                          rel="noopener noreferrer"
                          title="Cluster Report:">
                          {results.snp1?.rsnum}
                        </a>
                      </div>
                      <div>
                        <a
                          href={getUcscUrl(results.snp1?.coord, results.snp1?.rsnum, results.genome_build)}
                          target="_blank"
                          rel="noopener noreferrer"
                          title="Genome Browser">
                          {results.snp1?.coord}
                        </a>
                      </div>
                    </td>
                    <td className="text-center">{results.snp1?.allele_1?.allele}</td>
                    <td colSpan={2} rowSpan={2}>
                      {/* Two-by-two sub table */}
                      <table className="ldpair-two-by-two-table w-100">
                        <tbody>
                          <tr>
                            <td className="ldpair-cell text-center" width="50%">
                              {results.two_by_two?.cells?.c11}
                            </td>
                            <td className="ldpair-cell text-center">{results.two_by_two?.cells?.c12}</td>
                          </tr>
                          <tr>
                            <td className="ldpair-cell text-center">{results.two_by_two?.cells?.c21}</td>
                            <td className="ldpair-cell text-center">{results.two_by_two?.cells?.c22}</td>
                          </tr>
                        </tbody>
                      </table>
                    </td>
                    <td>{results.snp1?.allele_1?.count}</td>
                    <td className="text-start">({results.snp1?.allele_1?.frequency})</td>
                  </tr>
                  {/* Row 3 */}
                  <tr>
                    <td className="text-center">{results.snp1?.allele_2?.allele}</td>
                    <td>{results.snp1?.allele_2?.count}</td>
                    <td className="text-start">({results.snp1?.allele_2?.frequency})</td>
                  </tr>
                  {/* Row 4 */}
                  <tr>
                    <td></td>
                    <td></td>
                    <td className="text-center">
                      <span>{results.snp2?.allele_1?.count}</span>
                      <br />(<span>{results.snp2?.allele_1?.frequency}</span>)
                    </td>
                    <td className="text-center">
                      <span>{results.snp2?.allele_2?.count}</span>
                      <br />(<span>{results.snp2?.allele_2?.frequency}</span>)
                    </td>
                    <td>{results.two_by_two?.total}</td>
                    <td></td>
                  </tr>
                </tbody>
              </table>
            </Col>
          </Row>
          {/* Haplotypes and Statistics */}
          <Row>
            <Col>
              <table className="ldpair-table w-100">
                <tbody>
                  <tr>
                    <td colSpan={2} className="text-center">
                      <u>Haplotypes</u>
                    </td>
                    <td className="ldpair-spacer"></td>
                    <td colSpan={2} className="text-center">
                      <u>Statistics</u>
                    </td>
                  </tr>
                  <tr>
                    <td className="text-end">
                      <span>{results.haplotypes?.hap1?.alleles}</span>:
                      <br />
                      <span>{results.haplotypes?.hap2?.alleles}</span>:
                      <br />
                      <span>{results.haplotypes?.hap3?.alleles}</span>:
                      <br />
                      <span>{results.haplotypes?.hap4?.alleles}</span>:
                      <br />
                    </td>
                    <td style={{ whiteSpace: "nowrap" }}>
                      <span>{results.haplotypes?.hap1?.count}</span>&nbsp; (
                      <span>{results.haplotypes?.hap1?.frequency}</span>)
                      <br />
                      <span>{results.haplotypes?.hap2?.count}</span>&nbsp; (
                      <span>{results.haplotypes?.hap2?.frequency}</span>)
                      <br />
                      <span>{results.haplotypes?.hap3?.count}</span>&nbsp; (
                      <span>{results.haplotypes?.hap3?.frequency}</span>)
                      <br />
                      <span>{results.haplotypes?.hap4?.count}</span>&nbsp; (
                      <span>{results.haplotypes?.hap4?.frequency}</span>)
                      <br />
                    </td>
                    <td className="ldpair-spacer"></td>
                    <td className="text-end">
                      D&apos;:
                      <br />R<sup>2</sup>:
                      <br />
                      Chi-sq:
                      <br />
                      p-value:
                    </td>
                    <td>
                      <span>{results.statistics?.d_prime}</span>
                      <br />
                      <span>{results.statistics?.r2}</span>
                      <br />
                      <span>{results.statistics?.chisq}</span>
                      <br />
                      <span>{results.statistics?.p}</span>
                      <br />
                    </td>
                  </tr>
                </tbody>
              </table>
            </Col>
          </Row>
          {/* Correlated Alleles */}
          {Array.isArray(results.corr_alleles) && results.corr_alleles.length > 0 && (
            <Row className="mb-2">
              <Col>
                {results.corr_alleles.map((item: string, idx: number) => (
                  <div key={idx} className="text-center">
                    {item}
                  </div>
                ))}
              </Col>
            </Row>
          )}
          {/* Download Links */}
          <Row>
            <Col sm="auto">
              <a href={`/LDlinkRestWeb/tmp/LDpair_${ref}.txt`} download>
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
