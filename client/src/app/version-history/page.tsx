// app/version-history/page.tsx
"use client";


import { versionHistory } from "@/ldLinkdata/versionHistory";

export default function VersionHistoryPage() {
  return (
    <>

      <div className="container py-4">
        <h1 className="text-center mb-4">Version History</h1>
        {versionHistory.map((release, idx) => (
          <div key={idx} className="mb-4">
            <p>
              <b>{release.version}</b>
            </p>
            <ul style={{ paddingLeft: "20px" }}>
              {release.items.map((item, itemIdx) => (
                <li key={itemIdx}>{item}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>

    </>
  );
}
