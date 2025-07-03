"use client";
import React from "react";
import { Container } from "react-bootstrap";
import Image from "next/image";
import { versionHistory } from "../../components/ldLinkData/versionHistory";

export default function VersionHistoryPage() {
  return (
    <Container className="py-4">
      <div className="text-center">
        <h2>
          <Image
            src="/LDlink_logo_small_clear.png"
            alt="LDlink"
            style={{ verticalAlign: "bottom" }}
            width={48}
            height={48}
          />{" "}
          Version History
        </h2>
      </div>
      <div style={{ paddingLeft: 20, paddingRight: 20 }}>
        {versionHistory.map((entry, idx) => (
          <div key={entry.title} style={{ marginBottom: "2rem" }}>
            <h4>{entry.title}</h4>
            <ul>
              {entry.items.map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </Container>
  );
}
