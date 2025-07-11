"use client";
import { Row, Col, Table } from "react-bootstrap";

export interface SnpchipResult {
  snpchip: {
    rs_number: string;
    position: string;
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
                {results.snpchip.map((snp, i) => (
                  <tr key={i}>
                    <td dangerouslySetInnerHTML={{ __html: snp.rs_number }}></td>
                    <td dangerouslySetInnerHTML={{ __html: snp.position }}></td>
                    {snp.map.map((map, j) => (
                      <td key={j} dangerouslySetInnerHTML={{ __html: map }}></td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </Table>
          </Col>
        </Row>
        <div>
              <a
                id="snp_chip_list"
                target="snp_chip_list"
                onClick={downloadResults}
                style={{ cursor: "pointer" }}
              >
                Download Chip Details
              </a>
            </div>
      </div>
    </div>
  );
}
