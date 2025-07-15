"use client";
import React from "react";
import { Container } from "react-bootstrap";
import Image from "next/image";
import { versionHistory } from "../../components/ldLinkData/versionHistory";

export default function VersionHistoryPage() {
  return (
    <Container className="py-4 tab-content mb-0">
        <div className="not-home">
            <div className="text-center">
                <h1 className="h2">
                <Image
                    src="/images/LDlink_logo_small_clear.png"
                    alt="LDlink"
                    style={{ verticalAlign: "bottom" }}
                    width={91}
                    height={36}
                />{" "}
                Version History
                </h1>
            </div>
            <div id="news-container" style={{ paddingLeft: 20, paddingRight: 20 }}>
                {versionHistory.map((entry, idx) => (
                <div className="" key={entry.title} style={{ marginBottom: "2rem" }}>
                    <p><b>{entry.title}</b></p>
                    <ul>
                    {entry.items.map((item, i) => (
                        <li key={i} dangerouslySetInnerHTML={{ __html: item }} />
                    ))}
                    </ul>
                </div>
                ))}
            </div>
        </div>
    </Container>
  );
}
