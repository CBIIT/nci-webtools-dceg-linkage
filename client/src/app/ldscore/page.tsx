"use client";
import { useState } from "react";
import { Container, Row, Col, Nav, Tab } from "react-bootstrap";
import ToolBanner from "@/components/toolBanner";
import Heritability from "./heritability";
import Correlation from "./correlation";
import LDScore from "./ldscore";
import "./style.css";

export default function LdScore() {
  const [activeTab, setActiveTab] = useState("heritability");

  return (
    <>
      <ToolBanner
        name="LDscore Tool"
        href="/help/#LDscore"
        description="Calculate LD scores and perform LD score regression"
        showGenomeSelect={false}
      />
      <Container fluid="md">
        <Row className="border rounded bg-white my-3 p-3 shadow-sm">
          <Col>
            <Tab.Container activeKey={activeTab} onSelect={(key) => setActiveTab(key || "heritability")}>
              <Row>
                <Col sm={12}>
                  <Nav variant="tabs" className="mb-3">
                    <Nav.Item>
                      <Nav.Link eventKey="heritability">Heritability Analysis</Nav.Link>
                    </Nav.Item>
                    <Nav.Item>
                      <Nav.Link eventKey="genetic_correlation">Genetic Correlation</Nav.Link>
                    </Nav.Item>
                    <Nav.Item>
                      <Nav.Link eventKey="ld_calculation">LD Score Calculation</Nav.Link>
                    </Nav.Item>
                  </Nav>
                </Col>
              </Row>

              <Tab.Content>
                <Tab.Pane eventKey="heritability">
                  <Heritability />
                </Tab.Pane>

                <Tab.Pane eventKey="genetic_correlation">
                  <Correlation />
                </Tab.Pane>

                <Tab.Pane eventKey="ld_calculation">
                  <LDScore />
                </Tab.Pane>
              </Tab.Content>
            </Tab.Container>
          </Col>
        </Row>
      </Container>
    </>
  );
}
