"use client";
import { Row, Col, Table } from "react-bootstrap";

export interface SnpchipResult {
  snpchip: {
    map: string[];
    rs_number_raw: string;
    position_raw: string;
  }[];
  headers: {
    platform: string;
    code: string;
  }[];
  details: string;
}

export interface ResultsProps {
  results: SnpchipResult;
  genome_build: string;
}

const rotateStyle: React.CSSProperties = {
  height: "140px",  
  verticalAlign: "bottom",
  textAlign: "center", // aligns the cell itself
  whiteSpace: "nowrap",
};

const rotateDivStyle: React.CSSProperties = {
  transform: "rotate(270deg)",
  transformOrigin: "left",
  textAlign: "left", // aligns the rotated text
  width: "5px", // control line break
  marginLeft: "5px", // optional tweak for alignment
};
export default function Results({ results, genome_build }: ResultsProps) {
  console.log("SNPchip results >>>> :", results);
  function downloadResults() {
    const blob = new Blob([results.details], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "snpchip_results.txt";
    a.click();
    URL.revokeObjectURL(url);
  }

  const genomeBuildTitle = {
    grch37: "GRCh37",
    grch38: "GRCh38",
    grch38_high_coverage: "GRCh38 High Coverage",
  }[genome_build];

  return (
    <div className="jumbotron">
      <div className="container-fluid" id="snpchip-results-container">
        <Row>
          <Col md={12} style={{ overflowX: "scroll" }}>
            <Table striped bordered hover size="sm">
              <thead>
                <tr>
                  <th colSpan={2}>SNP Chip List</th>
                  {results.headers.map((header, i) => (
                    <th rowSpan={2} style={rotateStyle} key={i} title={header.platform}>
                      <div style={rotateDivStyle}>
                        {header.code}
                      </div>
                    </th>
                  ))}
                </tr>
                <tr>
                  <th>RS Number</th>
                  <th>Position ({genomeBuildTitle})</th>
                </tr>
              </thead>
              <tbody>
                {results.snpchip.map((snp, i) => {
                  const [chr, pos_str] = snp.position_raw.split(':');
                  const pos = parseInt(pos_str, 10);
                  const start = pos - 250;
                  const end = pos + 250;
                  const db = genome_build === 'grch37' ? 'hg19' : 'hg38';
                  const ucscLink = `https://genome.ucsc.edu/cgi-bin/hgTracks?db=${db}&position=chr${chr}%3A${start}-${end}&hgFind.matches=${snp.rs_number_raw}`;
                  const ncbiLink = `http://www.ncbi.nlm.nih.gov/projects/SNP/snp_ref.cgi?rs=${snp.rs_number_raw}`;

                  return (
                    <tr key={i}>
                      <td><a href={ncbiLink} target="_blank" rel="noopener noreferrer">{snp.rs_number_raw}</a></td>
                      <td><a href={ucscLink} target="_blank" rel="noopener noreferrer">chr{snp.position_raw}</a></td>
                      {snp.map.map((map, j) => (
                        <td key={j}>{map}</td>
                      ))}
                    </tr>
                  );
                })}
              </tbody>
            </Table>
          </Col>
        </Row>
        <div>
              <a
                id="snp_chip_list"
                target="snp_chip_list"
                onClick={downloadResults}                
              >
                Download Chip Details
              </a>
            </div>
      </div>
    </div>
  );
}
