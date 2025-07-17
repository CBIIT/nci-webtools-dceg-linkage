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

  return (
    <>
      {results && !results?.error ? (
        <Container fluid="md">
          <Row className="justify-content-center w-100">
            <Col xs={12} md={8} lg={6} className="d-flex flex-column align-items-center">
              <table className="ldpair-table mb-0" style={{ width: 340, margin: "0 auto" }}>
                <tbody>
                  {/* SNP2 header */}
                  <tr>
                    <td />
                    <td />
                    <td colSpan={2} className="text-center pb-0">
                      <div className="ldpair-snp2-rsnum">
                        <a
                          href={getNcbiSnpUrl(results.snp2?.rsnum)}
                          target="_blank"
                          rel="noopener noreferrer"
                          title="Cluster Report:">
                          {results.snp2?.rsnum}
                        </a>
                      </div>
                      <div className="ldpair-snp2-coord">
                        <a
                          href={getUcscUrl(results.snp2?.coord, results.snp2?.rsnum, formData?.genome_build)}
                          target="_blank"
                          rel="noopener noreferrer"
                          title="Genome Browser">
                          {results.snp2?.coord}
                        </a>
                      </div>
                    </td>
                    <td />
                    <td />
                  </tr>
                  {/* Header row */}
                  <tr>
                    <td />
                    <td />
                    <td className="text-center">{results.snp2?.allele_1?.allele}</td>
                    <td className="text-center">{results.snp2?.allele_2?.allele}</td>
                    <td />
                    <td />
                  </tr>
                  {/* Row 2 */}
                  <tr>
                    {/* SNP1 label */}
                    <td className="text-center align-middle" rowSpan={2}>
                      <div className="ldpair-snp1-rsnum">
                        <a
                          href={getNcbiSnpUrl(results.snp1?.rsnum)}
                          target="_blank"
                          rel="noopener noreferrer"
                          title="Cluster Report:">
                          {results.snp1?.rsnum}
                        </a>
                      </div>
                      <div className="ldpair-snp1-coord">
                        <a
                          href={getUcscUrl(results.snp1?.coord, results.snp1?.rsnum, formData?.genome_build)}
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
                      <table className="ldpair-two-by-two-table m-0" style={{ width: 120 }}>
                        <tbody>
                          <tr>
                            <td className="ldpair-cell text-center" style={{ width: 60 }}>
                              {results.two_by_two?.cells?.c11}
                            </td>
                            <td className="ldpair-cell text-center" style={{ width: 60 }}>
                              {results.two_by_two?.cells?.c12}
                            </td>
                          </tr>
                          <tr>
                            <td className="ldpair-cell text-center" style={{ width: 60 }}>
                              {results.two_by_two?.cells?.c21}
                            </td>
                            <td className="ldpair-cell text-center" style={{ width: 60 }}>
                              {results.two_by_two?.cells?.c22}
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </td>
                    <td className="text-center">{results.snp1?.allele_1?.count}</td>
                    <td className="text-start">({results.snp1?.allele_1?.frequency})</td>
                  </tr>
                  {/* Row 3 */}
                  <tr>
                    <td className="text-center">{results.snp1?.allele_2?.allele}</td>
                    <td className="text-center">{results.snp1?.allele_2?.count}</td>
                    <td className="text-start">({results.snp1?.allele_2?.frequency})</td>
                  </tr>
                  {/* Row 4: Totals and frequencies below the two-by-two table */}
                  <tr>
                    <td></td>
                    <td></td>
                    <td className="text-center">
                      {results.snp2?.allele_1?.count}
                      <span> ({results.snp2?.allele_1?.frequency})</span>
                    </td>
                    <td className="text-center">
                      {results.snp2?.allele_2?.count}
                      <span> ({results.snp2?.allele_2?.frequency})</span>
                    </td>
                    <td className="text-center" colSpan={2}>
                      {results.two_by_two?.total}
                    </td>
                  </tr>
                </tbody>
              </table>

              {/* Haplotypes and Statistics Section */}
              <Row className="mt-4 w-100 justify-content-center">
                <Col sm={3} />
                <Col sm={3}>
                  <div className="text-decoration-underline mb-2">Haplotypes</div>
                  {["hap1", "hap2", "hap3", "hap4"].map((hap) => (
                    <div key={hap}>
                      {results.haplotypes?.[hap]?.alleles}: {results.haplotypes?.[hap]?.count} (
                      {results.haplotypes?.[hap]?.frequency})
                    </div>
                  ))}
                </Col>
                <Col sm={3} className="text-start">
                  <div className="text-decoration-underline mb-2">Statistics</div>
                  <div>D&apos;: {results.statistics?.d_prime}</div>
                  <div>
                    R<sup>2</sup>: {results.statistics?.r2}
                  </div>
                  <div>Chi-sq: {results.statistics?.chisq}</div>
                  <div>p-value: {results.statistics?.p}</div>
                </Col>
              </Row>
              {/* Correlated Alleles */}
              <Row className="w-100 mt-4">
                <Col sm="2" />
                {Array.isArray(results.corr_alleles) && results.corr_alleles.length > 0 && (
                  <Col>
                    {results.corr_alleles.map((item: string, idx: number) => (
                      <div key={idx} className="text-center">
                        {item}
                      </div>
                    ))}
                  </Col>
                )}
              </Row>
            </Col>
          </Row>
          <Row>
            <Col>
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
