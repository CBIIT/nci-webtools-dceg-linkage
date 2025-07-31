"use client";
import { Row, Col, Container, Alert, Tabs, Tab } from "react-bootstrap";
import { useSuspenseQuery } from "@tanstack/react-query";
import { fetchOutput } from "@/services/queries";
import { submitFormData, ResultsData, Rs1MapLocation, Rs2MapLocation, Rs1Rs2LDMapLocation, AaDataRow } from "./types";
import { useJsApiLoader } from "@react-google-maps/api";
import { useState, useRef } from "react";
import Image from "next/image";
import { createColumnHelper } from "@tanstack/react-table";
import Table from "@/components/table";
import PopMap, { colorMarkerLD, colorMarkerMAF, getMinorAllele } from "@/app/ldpop/PopMap";
import html2canvas from "html2canvas";
import { Dropdown } from "react-bootstrap";

export default function LdPopResults({ reference, ...params }: { reference: string } & submitFormData) {
  const { data: results } = useSuspenseQuery<ResultsData>({
    queryKey: ["ldpop_results", reference],
    queryFn: async () => (reference ? fetchOutput(`ldpop${reference}.json`) : null),
  });

  const { isLoaded } = useJsApiLoader({
    googleMapsApiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || "", // Ensure your API key is set
  });

  const mapOptions = {
    zoom: 2,
    center: { lat: 30, lng: 0 },
    controlSize: 24,
  };

  const [activeMarker1, setActiveMarker1] = useState<number | null>(null);
  const [activeMarker2, setActiveMarker2] = useState<number | null>(null);
  const [activeMarker3, setActiveMarker3] = useState<number | null>(null);

  // Add refs for each map
  const mapRef1 = useRef<HTMLDivElement>(null);
  const mapRef2 = useRef<HTMLDivElement>(null);
  const mapRef3 = useRef<HTMLDivElement>(null);

  // Download handler (fix type to accept any ref)
  const handleDownload = async (ref: React.RefObject<HTMLDivElement>, type: "png" | "jpeg", name: string = "map") => {
    if (ref.current) {
      const canvas = await html2canvas(ref.current, { useCORS: true });
      const link = document.createElement("a");
      link.download = `${name}.${type}`;
      link.href = canvas.toDataURL(`image/${type}`);
      link.click();
    }
  };

  const LD_COLORS = [
    "#FFFFFF", // 0.0
    "#FBE6E6", // 0.1
    "#F8D3D2", // 0.2
    "#F4B5B4", // 0.3
    "#F19E9C", // 0.4
    "#EF8683", // 0.5
    "#EC706B", // 0.6
    "#EB5A54", // 0.7
    "#EB483F", // 0.8
    "#E9392D", // 0.9
    "#E9392D", // 1.0
  ];

  const MAF_COLORS = [
    "#FFFFFF", // 0.0
    "#E5E7FD", // 0.1
    "#D0D4FB", // 0.2
    "#B3BAFA", // 0.3
    "#9AA3F8", // 0.4
    "#828EF7", // 0.5
    "#6877F6", // 0.6
    "#4E60F5", // 0.7
    "#354CF5", // 0.8
    "#1B37F3", // 0.9
    "#1B37F3", // 1.0
  ];

  function LdpairLink({
    snp1,
    snp2,
    pops,
    genomeBuild,
  }: {
    snp1: string;
    snp2: string;
    pops: string;
    genomeBuild: string;
  }) {
    const href = `/ldpair?var1=${snp1}&var2=${snp2}&pop=${pops}&genome_build=${genomeBuild}`;
    return (
      <a style={{ color: "#318fe2" }} href={href} target="_blank" rel="noopener noreferrer">
        link
      </a>
    );
  }

  const columnHelper = createColumnHelper<any>();
  const columns = [
    columnHelper.accessor((row: any) => row[0], {
      id: "population",
      header: "Population",
      cell: (info: any) => info.getValue(),
    }),
    columnHelper.accessor((row: any) => row[1], {
      id: "n",
      header: "N",
      cell: (info: any) => info.getValue(),
    }),
    columnHelper.accessor((row: any) => row[2], {
      id: "rs1_allele_freq",
      header: `${results.inputs.rs1} Allele Freq`,
      cell: (info: any) => info.getValue(),
    }),
    columnHelper.accessor((row: any) => row[3], {
      id: "rs2_allele_freq",
      header: `${results.inputs.rs2} Allele Freq`,
      cell: (info: any) => info.getValue(),
    }),
    columnHelper.accessor((row: any) => row[4], {
      id: "r2",
      header: "R²",
      cell: (info: any) => info.getValue(),
    }),
    columnHelper.accessor((row: any) => row[5], {
      id: "d_prime",
      header: "D'",
      cell: (info: any) => info.getValue(),
    }),
    columnHelper.accessor((row: any) => row[6], {
      id: "ldpair",
      header: "LDpair",
      cell: (info: any) => {
        const row = info.row.original;
        const pops = row[0]; // Population
        const genomeBuild = params?.genome_build || "grch38";
        return <LdpairLink snp1={results.inputs.rs1} snp2={results.inputs.rs2} pops={pops} genomeBuild={genomeBuild} />;
      },
    }),
  ];

  function ExportDropdown({
    mapRef,
    handleDownload,
    dropdownId,
    mapName,
  }: {
    mapRef: React.RefObject<HTMLDivElement>;
    handleDownload: (ref: React.RefObject<HTMLDivElement>, type: "png" | "jpeg", name: string) => void;
    dropdownId: string;
    mapName: string;
  }) {
    return (
      <Dropdown>
        <Dropdown.Toggle split variant="outline-primary" id={dropdownId}>
          Export {mapName}
        </Dropdown.Toggle>
        <Dropdown.Menu>
          <Dropdown.Item onClick={() => handleDownload(mapRef, "png", mapName.replace(/\s/g, "-").toLowerCase())}>
            Download PNG
          </Dropdown.Item>
          <Dropdown.Item onClick={() => handleDownload(mapRef, "jpeg", mapName.replace(/\s/g, "-").toLowerCase())}>
            Download JPEG
          </Dropdown.Item>
        </Dropdown.Menu>
      </Dropdown>
    );
  }

  return (
    <>
      <hr />
      {results && !results?.error ? (
        <Container fluid="md">
          <Row>
            <Col>
              <Tabs defaultActiveKey="1" className="mb-3">
                <Tab eventKey="1" title={`${results.inputs.rs1} ${results.inputs.rs2} LD`}>
                  <Row className="mb-1">
                    <Col md={4} />
                    <Col md={4} className="text-center">
                      <h3>{`${results.inputs.rs1} ${results.inputs.rs1} LD`}</h3>
                    </Col>
                    <Col md={4} className="d-flex justify-content-end">
                      <ExportDropdown
                        mapRef={mapRef1 as React.RefObject<HTMLDivElement>}
                        handleDownload={handleDownload}
                        dropdownId="dropdown-split-basic"
                        mapName="LD Map"
                      />
                    </Col>
                  </Row>
                  {isLoaded && (
                    <div ref={mapRef1}>
                      <PopMap
                        mapOptions={mapOptions}
                        markers={results.locations?.rs1_rs2_LD_map?.map((loc: Rs1Rs2LDMapLocation, i: number) => ({
                          position: { lat: loc[3], lng: loc[4] },
                          icon:
                            isLoaded && typeof google !== "undefined"
                              ? {
                                  path: "M0-48c-9.8 0-17.7 7.8-17.7 17.4 0 15.5 17.7 30.6 17.7 30.6s17.7-15.4 17.7-30.6c0-9.6-7.9-17.4-17.7-17.4z",
                                  strokeColor: "black",
                                  fillColor: colorMarkerLD("r2", loc, LD_COLORS, MAF_COLORS),
                                  fillOpacity: 1,
                                  scale: 0.85,
                                  labelOrigin: new google.maps.Point(0, -30),
                                }
                              : undefined,
                          label: { text: loc[0], fontSize: "12px" },
                          title: `(${loc[0]}) ${loc[1]}`,
                          onClick: () => setActiveMarker1(i),
                          infoWindowOpen: activeMarker1 === i,
                          infoWindowContent: (
                            <div>
                              <b>
                                ({loc[0]}) - {loc[1]}
                              </b>
                              <hr style={{ marginTop: 5, marginBottom: 5 }} />
                              <b>{results.inputs.rs1}</b>: {loc[5]}
                              <br />
                              <b>{results.inputs.rs2}</b>: {loc[6]}
                              <br />
                              <b>
                                R<sup>2</sup>
                              </b>
                              : {loc[7]}
                              <br />
                              <b>D&#39;</b>: {loc[8]}
                            </div>
                          ),
                        }))}>
                        <div style={{ display: "flex", justifyContent: "center", marginTop: 16 }}>
                          <Image
                            src="/images/LDpop_legend_R2.png"
                            alt="LDpop LD legend"
                            title="LDpop LD Legend"
                            width={300}
                            height={120}
                            style={{ width: 300, height: "auto" }}
                            priority
                          />
                        </div>
                      </PopMap>
                    </div>
                  )}
                </Tab>
                <Tab eventKey="2" title={`${results.inputs.rs1} Allele Frequency`}>
                  <Row className="mb-1">
                    <Col md={4} />
                    <Col md={4} className="text-center">
                      <h3>{`${results.inputs.rs1} Allele Frequency`}</h3>
                    </Col>
                    <Col md={4} className="d-flex justify-content-end">
                      <ExportDropdown
                        mapRef={mapRef2 as React.RefObject<HTMLDivElement>}
                        handleDownload={handleDownload}
                        dropdownId="dropdown-split-basic2"
                        mapName="AF Map"
                      />
                    </Col>
                  </Row>
                  {isLoaded && (
                    <div ref={mapRef2}>
                      <PopMap
                        mapOptions={mapOptions}
                        markers={results.locations?.rs1_map?.map((loc: Rs1MapLocation, i: number) => ({
                          position: { lat: loc[3], lng: loc[4] },
                          icon:
                            isLoaded && typeof google !== "undefined"
                              ? {
                                  path: "M0-48c-9.8 0-17.7 7.8-17.7 17.4 0 15.5 17.7 30.6 17.7 30.6s17.7-15.4 17.7-30.6c0-9.6-7.9-17.4-17.7-17.4z",
                                  strokeColor: "black",
                                  fillColor: colorMarkerMAF(
                                    getMinorAllele(2, results.aaData),
                                    loc,
                                    LD_COLORS,
                                    MAF_COLORS
                                  ),
                                  fillOpacity: 1,
                                  scale: 0.85,
                                  labelOrigin: new google.maps.Point(0, -30),
                                }
                              : undefined,
                          label: { text: loc[0], fontSize: "12px" },
                          title: `(${loc[0]}) ${loc[1]}`,
                          onClick: () => setActiveMarker2(i),
                          infoWindowOpen: activeMarker2 === i,
                          infoWindowContent: (
                            <div>
                              <b>
                                ({loc[0]}) - {loc[1]}
                              </b>
                              <hr style={{ marginTop: 5, marginBottom: 5 }} />
                              {loc[5]}
                            </div>
                          ),
                        }))}>
                        <div style={{ display: "flex", justifyContent: "center", marginTop: 16 }}>
                          <Image
                            src="/images/LDpop_legend_MAF.png"
                            alt="LDpop MAF legend"
                            title="LDpop MAF Legend"
                            width={200}
                            height={120}
                            style={{ width: 200, height: "auto" }}
                            priority
                          />
                        </div>
                      </PopMap>
                    </div>
                  )}
                </Tab>
                <Tab eventKey="3" title={`${results.inputs.rs2} Allele Frequency`}>
                  <Row className="mb-1">
                    <Col md={4} />
                    <Col md={4} className="text-center">
                      <h3>{`${results.inputs.rs2} Allele Frequency`}</h3>
                    </Col>
                    <Col md={4} className="d-flex justify-content-end">
                      <ExportDropdown
                        mapRef={mapRef3 as React.RefObject<HTMLDivElement>}
                        handleDownload={handleDownload}
                        dropdownId="dropdown-split-basic3"
                        mapName="AF Map"
                      />
                    </Col>
                  </Row>
                  {isLoaded && (
                    <div ref={mapRef3}>
                      <PopMap
                        mapOptions={mapOptions}
                        markers={results.locations?.rs2_map?.map((loc: Rs2MapLocation, i: number) => ({
                          position: { lat: loc[3], lng: loc[4] },
                          icon:
                            isLoaded && typeof google !== "undefined"
                              ? {
                                  path: "M0-48c-9.8 0-17.7 7.8-17.7 17.4 0 15.5 17.7 30.6 17.7 30.6s17.7-15.4 17.7-30.6c0-9.6-7.9-17.4-17.7-17.4z",
                                  strokeColor: "black",
                                  fillColor: colorMarkerMAF(
                                    getMinorAllele(3, results.aaData),
                                    loc,
                                    LD_COLORS,
                                    MAF_COLORS
                                  ),
                                  fillOpacity: 1,
                                  scale: 0.85,
                                  labelOrigin: new google.maps.Point(0, -30),
                                }
                              : undefined,
                          label: { text: loc[0], fontSize: "12px" },
                          title: `(${loc[0]}) ${loc[1]}`,
                          onClick: () => setActiveMarker3(i),
                          infoWindowOpen: activeMarker3 === i,
                          infoWindowContent: (
                            <div>
                              <b>
                                ({loc[0]}) - {loc[1]}
                              </b>
                              <hr style={{ marginTop: 5, marginBottom: 5 }} />
                              {loc[5]}
                            </div>
                          ),
                        }))}>
                        <div style={{ display: "flex", justifyContent: "center", marginTop: 16 }}>
                          <Image
                            src="/images/LDpop_legend_MAF.png"
                            alt="LDpop MAF legend"
                            title="LDpop MAF Legend"
                            width={200}
                            height={120}
                            style={{ width: 200, height: "auto" }}
                            priority
                          />
                        </div>
                      </PopMap>
                    </div>
                  )}
                </Tab>
              </Tabs>
            </Col>
          </Row>
          <Row className="mt-3">
            <Col>{results && <Table title="" data={results.aaData as AaDataRow[]} columns={columns} />}</Col>
          </Row>
          <Row>
            <Col>
              <a href={`/LDlinkRestWeb/tmp/LDpop_ref${reference}.txt`} download>
                Download Table
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
