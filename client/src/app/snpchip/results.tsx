"use client";
import { Row, Col, Table } from "react-bootstrap";

export default function SNPChipResults({ results }: { results: any }) {
  return (
    <div className="jumbotron">
      <Row>
        <Col md={6}>
          <Table striped bordered size="sm">
            <thead>
              <tr>
                <th colSpan={2}>SNP Chip List</th>
              </tr>
              <tr>
                <th>RS Number</th>
                <th>Position</th>
              </tr>
            </thead>
            <tbody>
              {results.snpchip?.map((snp: any, idx: number) => (
                <tr key={idx}>
                  <td>{snp.rs_number}</td>
                  <td>{snp.position}</td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Col>
        <Col md={6}>
          <Table striped bordered size="sm">
            <thead>
              <tr>
                {results.headers?.map((header: any, idx: number) => (
                  <th key={idx} title={header.platform}>{header.code}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {results.snpchip?.map((snp: any, idx: number) => (
                <tr key={idx}>
                  {snp.map?.map((cell: string, cidx: number) => (
                    <td key={cidx}>{cell}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </Table>
        </Col>
      </Row>
    </div>
  );
}
