"use client";
import { Row, Col, Container, Alert } from "react-bootstrap";
import { useSuspenseQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo } from "react";
import { fetchOutput } from "@/services/queries";
import { FormData, ResultsData, SNP, Haplotype } from "./types";
import { genomeBuildMap } from "@/store";
import "./styles.scss";

export default function LdHapResults({ ref }: { ref: string }) {
  const queryClient = useQueryClient();
  const formData = queryClient.getQueryData(["ldhap-form-data", ref]) as FormData | undefined;

  const { data: results } = useSuspenseQuery<ResultsData>({
    queryKey: ["ldhap_results", ref],
    queryFn: async () => (ref ? fetchOutput(`ldhap${ref}.json`) : null),
  });

  // filter out haplotypes with frequency less than 1%
  const haplotypes = useMemo(() => {
    return Object.values(results?.haplotypes || {}).filter((h) => h.Frequency > 0.01);
  }, [results]);

  return (
    <>
      <hr />
      {results && !results?.error ? (
        <Container fluid="md" className="justify-content-center">
          <Row>
            <Col sm="auto">
              <table className="table table-condensed w-auto">
                <thead>
                  <tr>
                    <th>RS Number</th>
                    <th>Position ({genomeBuildMap[formData?.genome_build || "grch37"]})</th>
                    <th style={{ whiteSpace: "nowrap" }}>Allele Frequencies</th>
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
                  {Object.values(results.snps)?.map((snp: SNP, i: number) => (
                    <tr key={i}>
                      <td>
                        <a title="Cluster Report" target="_blank" href={`http://www.ncbi.nlm.nih.gov/snp/${snp.RS}`}>
                          <span>{snp.RS}</span>
                          <span className="visually-hidden">Cluster Report</span>
                        </a>
                      </td>
                      <td>
                        {snp.Coord && (
                          <a
                            title="Genome Browser"
                            target="_blank"
                            href={(() => {
                              const positions = snp.Coord.split(":");
                              const chr = positions[0];
                              const mid_value = parseInt(positions[1]);
                              const offset = 250;
                              const range = `${mid_value - offset}-${mid_value + offset}`;
                              const position = `${chr}:${range}`;
                              const params = {
                                "db": formData?.genome_build == "grch37" ? "hg19" : "hg38",
                                "position": position,
                                "snp151": "pack",
                                "hgFind.matches": snp.RS,
                              };
                              return `https://genome.ucsc.edu/cgi-bin/hgTracks?${new URLSearchParams(params)}`;
                            })()}>
                            <span>{snp.Coord}</span>
                            <span className="visually-hidden">Genome Browser</span>
                          </a>
                        )}
                      </td>
                      <td>{snp.Alleles}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Col>
            <Col sm="6">
              <table id="ldhap-table-right" className="table table-condensed text-center">
                <thead>
                  <tr>
                    <th colSpan={5}>Haplotypes</th>
                  </tr>
                </thead>
                <tfoot>
                  <tr>
                    {Object.values(haplotypes)?.map((h: Haplotype, i: number) => (
                      <td key={i}>{h.Count}</td>
                    ))}
                  </tr>
                  <tr>
                    {Object.values(haplotypes)?.map((h: Haplotype, i: number) => (
                      <td key={i}>{h.Frequency}</td>
                    ))}
                  </tr>
                </tfoot>
                <tbody>
                  {(() => {
                    const splitHaps = haplotypes.map((h) => h.Haplotype?.split("_") || []);
                    const maxRows = Math.max(...splitHaps.map((h) => h.length));
                    return Array.from({ length: maxRows }).map((_, rowIdx) => (
                      <tr key={rowIdx}>
                        {splitHaps.map((hap, colIdx) => (
                          <td
                            key={colIdx}
                            className={`haplotype ${
                              hap[rowIdx] === "-" ? "haplotype_dash" : `haplotype_${hap[rowIdx]?.toLowerCase()}`
                            }`}>
                            <span>{hap[rowIdx]}</span>
                          </td>
                        ))}
                      </tr>
                    ));
                  })()}
                </tbody>
              </table>
            </Col>
          </Row>
          <Row>
            <Col sm="auto">
              <a href={`/LDlinkRestWeb/tmp/snps_${ref}.txt`} download>
                Download Variant File
              </a>
            </Col>
            <Col>
              <a href={`/LDlinkRestWeb/tmp/haplotypes_${ref}.txt`} download>
                Download Haplotype File
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
