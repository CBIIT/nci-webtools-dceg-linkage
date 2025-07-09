"use client";
import AppNavbar from "./navbar/navbar";
import { useState } from "react";
import Image from "next/image";
import { Container, Row, Col } from "react-bootstrap";

export type Route = {
  title: string;
  path?: string;
  subRoutes: Array<{
    title: string;
    path: string;
  }>;
};

type HeaderProps = {
  routes: Route[];
};

export function Header({ routes = [] }: HeaderProps) {
  const [search, setSearch] = useState("");

  const newSearch = () =>
    window.open(
      `https://www.google.com/search?q=site:https://ldlink.nih.gov/ ${encodeURIComponent(search)}`,
      "_blank"
    );

  const handleKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") newSearch();
  };

  const handleClick = () => newSearch();

  return (
    <header>
      <Container className="my-2">
        <Row>
          <div className="header">
            <div className="container">
              <header className="usa-banner__header">
                <div className="usa-banner__inner">
                  <div className="container">
                    <div className="usa-banner__header-text">
                      An official website of the United States government
                    </div>
                  </div>
                </div>
              </header>              
            </div>
          </div>
        </Row>

        <Row>
          <Col xl="9" md="8" sm="12">
            <a rel="noopener noreferrer" href="https://dceg.cancer.gov/">
              <Image
                src="/images/NIH-LDlink-Logo.png"
                alt="LDlink Logo"
                className="mw-100 ldlink-logo"
                width={359.078}
                height={90}
                unoptimized
              />
            </a>
          </Col>

          <Col xl="3" md="4" sm="9" xs="9">
            <div className="d-flex" style={{ width: "auto" }}>
              <label htmlFor="doc_search" className="visually-hidden">
                Search:
              </label>
              <input
                id="doc_search"
                type="text"
                name="search"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={handleKey}
                className="form-control"
                placeholder="Document Site Search"
                style={{
                  borderTopLeftRadius: "20px",
                  borderBottomLeftRadius: "20px",
                  borderBottomRightRadius: "0",
                  borderTopRightRadius: "0",
                }}
              />
              <div
                className="input-group-text"
                onClick={handleClick}
                style={{
                  borderTopRightRadius: "20px",
                  borderBottomRightRadius: "20px",
                  borderBottomLeftRadius: "0",
                  borderTopLeftRadius: "0",
                  marginLeft: "-1px",
                  cursor: "pointer",
                }}
              >
                <i className="bi bi-search"></i>
              </div>
            </div>
          </Col>
        </Row>
      </Container>

      <AppNavbar routes={routes} />
    </header>
  );
}
