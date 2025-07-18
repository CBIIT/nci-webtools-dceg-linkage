"use client";
import { Row, Col, Container, Alert, Tabs, Tab } from "react-bootstrap";
import { useSuspenseQuery } from "@tanstack/react-query";
import { fetchOutput } from "@/services/queries";
import { submitFormData, ResultsData } from "./types";
import { GoogleMap, Marker, InfoWindow, useJsApiLoader } from "@react-google-maps/api";
import { useState } from "react";
import Image from "next/image";
import { createColumnHelper } from "@tanstack/react-table";
import Table from "@/components/table";

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

  // Create markerIcon only after Google Maps API is loaded
  const markerIcon =
    isLoaded && typeof google !== "undefined"
      ? {
          path: "M0-48c-9.8 0-17.7 7.8-17.7 17.4 0 15.5 17.7 30.6 17.7 30.6s17.7-15.4 17.7-30.6c0-9.6-7.9-17.4-17.7-17.4z",
          strokeColor: "black",
          fillColor: "red",
          fillOpacity: 1,
          scale: 0.85,
          labelOrigin: new google.maps.Point(0, -30),
        }
      : undefined;

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
      header: `${params?.var1} Allele Freq`,
      cell: (info: any) => info.getValue(),
    }),
    columnHelper.accessor((row: any) => row[3], {
      id: "rs2_allele_freq",
      header: `${params?.var2} Allele Freq`,
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
        return <LdpairLink snp1={params?.var1} snp2={params?.var2} pops={pops} genomeBuild={genomeBuild} />;
      },
    }),
  ];

  return (
    <>
      {results && !results?.error ? (
        <Container fluid="md">
          <Row>
            <Col>
              <Tabs defaultActiveKey="1" className="mb-3">
                <Tab eventKey="1" title={`${params?.var1} ${params?.var2} LD`}>
                  {isLoaded && (
                    <GoogleMap mapContainerStyle={{ width: "100%", height: "400px" }} options={mapOptions}>
                      {results.locations?.rs1_rs2_LD_map?.map((loc, i) => (
                        <Marker
                          key={i}
                          position={{ lat: loc[3], lng: loc[4] }}
                          icon={markerIcon}
                          label={{ text: loc[0], fontSize: "12px" }}
                          title={`(${loc[0]}) ${loc[1]}`}
                          onClick={() => setActiveMarker1(i)}
                        />
                      ))}
                      {activeMarker1 !== null && (
                        <InfoWindow
                          position={{
                            lat: results.locations.rs1_rs2_LD_map[activeMarker1][3],
                            lng: results.locations.rs1_rs2_LD_map[activeMarker1][4],
                          }}
                          onCloseClick={() => setActiveMarker1(null)}>
                          <div>
                            <b>
                              ({results.locations.rs1_rs2_LD_map[activeMarker1][0]}) -{" "}
                              {results.locations.rs1_rs2_LD_map[activeMarker1][1]}
                            </b>
                            <hr style={{ marginTop: 5, marginBottom: 5 }} />
                            <b>{params?.var1}</b>: {results.locations.rs1_rs2_LD_map[activeMarker1][5]}
                            <br />
                            <b>{params?.var2}</b>: {results.locations.rs1_rs2_LD_map[activeMarker1][6]}
                            <br />
                            <b>
                              R<sup>2</sup>
                            </b>
                            : {results.locations.rs1_rs2_LD_map[activeMarker1][7]}
                            <br />
                            <b>D&#39;</b>: {results.locations.rs1_rs2_LD_map[activeMarker1][8]}
                          </div>
                        </InfoWindow>
                      )}
                    </GoogleMap>
                  )}
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
                </Tab>
                <Tab eventKey="2" title={`${params?.var1} Allele Frequency`}>
                  {isLoaded && (
                    <GoogleMap mapContainerStyle={{ width: "100%", height: "400px" }} options={mapOptions}>
                      {results.locations?.rs1_map?.map((loc, i) => (
                        <Marker
                          key={i}
                          position={{ lat: loc[3], lng: loc[4] }}
                          icon={markerIcon}
                          label={{ text: loc[0], fontSize: "12px" }}
                          title={`(${loc[0]}) ${loc[1]}`}
                          onClick={() => setActiveMarker2(i)}
                        />
                      ))}
                      {activeMarker2 !== null && (
                        <InfoWindow
                          position={{
                            lat: results.locations.rs1_map[activeMarker2][3],
                            lng: results.locations.rs1_map[activeMarker2][4],
                          }}
                          onCloseClick={() => setActiveMarker2(null)}>
                          <div>
                            <b>
                              ({results.locations.rs1_map[activeMarker2][0]}) -{" "}
                              {results.locations.rs1_map[activeMarker2][1]}
                            </b>
                            <hr style={{ marginTop: 5, marginBottom: 5 }} />
                            {results.locations.rs1_map[activeMarker2][5]}
                          </div>
                        </InfoWindow>
                      )}
                    </GoogleMap>
                  )}
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
                </Tab>
                <Tab eventKey="3" title={`${params?.var2} Allele Frequency`}>
                  {isLoaded && (
                    <GoogleMap mapContainerStyle={{ width: "100%", height: "400px" }} options={mapOptions}>
                      {results.locations?.rs2_map?.map((loc, i) => (
                        <Marker
                          key={i}
                          position={{ lat: loc[3], lng: loc[4] }}
                          icon={markerIcon}
                          label={{ text: loc[0], fontSize: "12px" }}
                          title={`(${loc[0]}) ${loc[1]}`}
                          onClick={() => setActiveMarker3(i)}
                        />
                      ))}
                      {activeMarker3 !== null && (
                        <InfoWindow
                          position={{
                            lat: results.locations.rs2_map[activeMarker3][3],
                            lng: results.locations.rs2_map[activeMarker3][4],
                          }}
                          onCloseClick={() => setActiveMarker3(null)}>
                          <div>
                            <b>
                              ({results.locations.rs2_map[activeMarker3][0]}) -{" "}
                              {results.locations.rs2_map[activeMarker3][1]}
                            </b>
                            <hr style={{ marginTop: 5, marginBottom: 5 }} />
                            {results.locations.rs2_map[activeMarker3][5]}
                          </div>
                        </InfoWindow>
                      )}
                    </GoogleMap>
                  )}
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
                </Tab>
              </Tabs>
            </Col>
          </Row>
          <Row className="mt-3">
            <Col>{results && <Table title="" data={results.aaData} columns={columns} />}</Col>
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
