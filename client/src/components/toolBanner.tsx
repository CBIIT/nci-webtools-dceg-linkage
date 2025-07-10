"use client";
import { Container, Row, Col } from "react-bootstrap";
import GenomeSelect from "@/components/select/genome-select";

export default function ToolBanner({ name, description, href }: { name: string; description: string; href: string }) {
  return (
    <Container fluid="md">
      <Row className="border rounded bg-white my-3 p-3 shadow-sm">
        <Col sm="2">
          <GenomeSelect />
        </Col>
        <Col>
          <h2 className="text-center ">
            {name}
            <sup>
              <a
                href={href}
                target="_blank"
                style={{ fontSize: 20, textDecoration: "none", marginLeft: 5 }}
                title="Click here for documentation">
                <i className="bi bi-info-circle-fill text-primary"></i>
              </a>
            </sup>
          </h2>
          <p className="text-center">{description}</p>
        </Col>
        <Col sm="2" />
      </Row>
    </Container>
  );
}
