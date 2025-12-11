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
    window.open(`https://www.google.com/search?q=site:https://ldlink.nih.gov/ ${encodeURIComponent(search)}`, "_blank");

  const handleKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") newSearch();
  };

  const handleClick = () => newSearch();

  return (
    <>
      <header>
        <section className="usa-banner" aria-label="Official government website">
          <Container className="my-0 mx-autousa-banner__header">
            <Row className="usa-banner__inner mx-0 px-0">
              <Col xl="9" md="8" sm="12" className="usa-banner__header-text px-0">
                An official website of the United States government
              </Col>
            </Row>
          </Container>
        </section>
        <Container className="my-0">
          <Row className="align-items-center">
            <Col xl="9" md="8" sm="12">
              <a
                href="https://dceg.cancer.gov/"
                target="_blank"
                aria-label="Go to NCI Division of Cancer Epidemiology and Genetics home page">
                <svg
                  version="1.1"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="22.2 214 340 52.2"
                  className="mw-100"
                  style={{ width: "359.078px", height: "90px" }}
                  role="img"
                  aria-label="LDlink Logo">
                  <defs>
                    <style>
                      {`
                        @font-face {
                          font-family: 'Montserrat';
                          font-weight: bold;
                          font-style: normal;
                          src: url("/nci-logo/fonts/Montserrat-700.eot");
                          src: url("/nci-logo/fonts/Montserrat-700.eot?#iefix") format("embedded-opentype"),
                               url("/nci-logo/fonts/Montserrat-700.woff") format("woff"),
                               url("/nci-logo/fonts/Montserrat-700.ttf") format("truetype"),
                               url("/nci-logo/fonts/Montserrat-700.svg#Montserrat") format("svg");
                        }
                        @font-face {
                          font-family: 'Montserrat';
                          font-weight: normal;
                          font-style: normal;
                          src: url("/nci-logo/fonts/Montserrat-regular.eot");
                          src: url("/nci-logo/fonts/Montserrat-regular.eot?#iefix") format("embedded-opentype"),
                               url("/nci-logo/fonts/Montserrat-regular.woff") format("woff"),
                               url("/nci-logo/fonts/Montserrat-regular.ttf") format("truetype"),
                               url("/nci-logo/fonts/Montserrat-regular.svg#Montserrat") format("svg");
                        }
                        .gray { fill: #606060; }
                        .red { fill: #BB0E3D; }
                        .white { fill: #FFFFFF; }
                      `}
                    </style>
                  </defs>
                  <path
                    className="gray"
                    d="M94.7,240l-14.5-26.1H27.8c-3.1,0-5.6,2.5-5.6,5.6v41c0,3.1,2.5,5.6,5.6,5.6h52.4L94.7,240z"
                  />
                  <path
                    className="red"
                    d="M93.3,216.6c-1-1.7-2.9-2.7-4.8-2.7h-4.3L98.8,240l-14.7,26.1h4.3c2,0,3.8-1,4.8-2.7l13.1-23.4L93.3,216.6z"
                  />
                  <rect className="white" x="53.2" y="228.4" width="3.9" height="23.2" />
                  <polygon
                    className="white"
                    points="45.4,228.4 45.4,245.4 34.8,228.4 30.9,228.4 30.9,251.6 34.8,251.6 34.8,234.6 45.4,251.6 49.3,251.6 49.3,228.4"
                  />
                  <polygon
                    className="white"
                    points="75.4,228.4 75.4,238.1 64.8,238.1 64.8,228.4 60.9,228.4 60.9,251.6 64.8,251.6 64.8,241.9 75.4,241.9 75.4,251.6 79.3,251.6 79.3,228.4"
                  />
                  <text className="red" x="117.5" y="232.5" fontFamily="Montserrat" fontWeight="700" fontSize="15.47">
                    NATIONAL CANCER INSTITUTE
                  </text>
                  <text
                    className="gray"
                    x="117.2"
                    y="258.5"
                    fontFamily="Montserrat"
                    fontWeight="700"
                    fontSize="16"
                    fontStyle="italic">
                    LDlink
                  </text>
                </svg>
              </a>
            </Col>

            <Col xl="3" md="4" sm="9" xs="9">
              <div className="d-flex align-items-center justify-content-center" style={{ width: "auto" }}>
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
                  placeholder="Site Search"
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
                  }}>
                  <i className="bi bi-search"></i>
                </div>
              </div>
            </Col>
          </Row>
        </Container>
        <AppNavbar routes={routes} />
      </header>
    </>
  );
}
