"use client";
import { Row, Col, Table } from "react-bootstrap";

export interface SnpchipResult {
  snpchip: {
    rs_number: string;
    position: string;
    map: string[];
  }[];
  headers: {
    platform: string;
    code: string;
  }[];
  details: string;
}

export interface ResultsProps {
  results: SnpchipResult;
}

const rotateStyle: React.CSSProperties = {
  height: "140px",
  whiteSpace: "nowrap",
  textAlign: "center",
};

const rotateDivStyle: React.CSSProperties = {
  transform: "translate(0, 50px) rotate(315deg)",
  width: "30px",
};

const rotateSpanStyle: React.CSSProperties = {
  borderBottom: "1px solid #ccc",
  padding: "5px 10px",
};

export default function Results({ results }: ResultsProps) {
  function downloadResults() {
    const blob = new Blob([results.details], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "snpchip_results.txt";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="jumbotron">
      <div className="container-fluid" id="snpchip-results-container">
        <Row>
          <Col md={3} style={{ paddingRight: "5px" }}>
            <Table striped bordered hover size="sm">
              <thead>
                <tr>
                  <th colSpan={2}>SNP Chip List</th>
                </tr>
                <tr>
                  <th>RS Number</th>
                  <th>Position (GRCh37)</th>
                </tr>
              </thead>
              <tbody>
                {results.snpchip.map((snp, i) => {
                  if (!snp) return null;
                  return (
                    <tr key={i}>
                      <td
                        dangerouslySetInnerHTML={{ __html: snp.rs_number }}
                      ></td>
                      <td
                        dangerouslySetInnerHTML={{ __html: snp.position }}
                      ></td>
                    </tr>
                  );
                })}
              </tbody>
            </Table>
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
          </Col>
          <Col md={9} style={{ overflowX: "scroll" }}>
            <Table striped bordered hover size="sm">
              <thead>
                <tr>
                  {results.headers.map((header, i) => (
                    <th style={rotateStyle} key={i}>
                      <div style={rotateDivStyle} title={header.platform}>
                        <span style={rotateSpanStyle}>{header.code}</span>
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {results.snpchip.map((snp, i) => {
                  if (!snp) return null;
                  return (
                    <tr key={i}>
                      {snp.map &&
                        snp.map.map((map, j) => (
                          <td
                            key={j}
                            dangerouslySetInnerHTML={{ __html: map }}
                          ></td>
                        ))}
                    </tr>
                  );
                })}
              </tbody>
            </Table>
          </Col>
        </Row>
      </div>
    </div>
  );
}
