"use client";
import React from "react";
import Image from "next/image";

export default function LdToolCard() {
  const tools = [
    {
      id: "ldassoc",
      title: "LDassoc",
      desc: "Interactively visualize association p-value results and linkage disequilibrium patterns for a genomic region of interest.",
    },
    {
      id: "ldexpress",
      title: "LDexpress",
      desc: "Search if a list of variants (or variants in LD with those variants) is associated with gene expression in multiple tissue types.",
    },
    {
      id: "ldhap",
      title: "LDhap",
      desc: "Calculate population specific haplotype frequencies of all haplotypes observed for a list of query variants.",
    },
    {
      id: "ldmatrix",
      title: "LDmatrix",
      desc: "Create an interactive heatmap matrix of pairwise linkage disequilibrium statistics.",
    },
    {
      id: "ldpair",
      title: "LDpair",
      desc: "Investigate correlated alleles for a pair of variants in high LD.",
    },
    {
      id: "ldpop",
      title: "LDpop",
      desc: "Investigate allele frequencies and linkage disequilibrium patterns across 1000G populations.",
    },
    {
      id: "ldproxy",
      title: "LDproxy",
      desc: "Interactively explore proxy and putatively functional variants for a query variant.",
    },
    {
      id: "ldtrait",
      title: "LDtrait",
      desc: "Search if a list of variants (or variants in LD with those variants) have previously been associated with a trait or disease.",
    },
    {
      id: "ldscore",
      title: "LDscore",
      desc: "Calculate LD scores and perform LD score regression.",
    },
    {
      id: "snpchip",
      title: "SNPchip",
      desc: "Find commercial genotyping platforms for variants.",
    }
    
  ];

  const toolRows: ({ id: string; title: string; desc: string } | null)[][] = [];

  const toolsPerRow = 5;
  for (let i = 0; i < tools.length; i += toolsPerRow) {
    const rowTools: ({ id: string; title: string; desc: string } | null)[] = tools.slice(i, i + toolsPerRow);
    // Pad with empty placeholders if needed
    while (rowTools.length < toolsPerRow) {
      rowTools.push(null);
    }
    toolRows.push(rowTools);
  }

  return (
    <div id="main-container" role="main">
      <div id="content" className="tab-content">
        <div className="tab-pane fade show active" id="home-tab">
          

          <div style={{ width: "100%", backgroundColor: "#536e84", padding: "40px 0" }}>
            {toolRows.map((row, rowIndex) => (
              <div className="card-row" key={rowIndex}>
                {row.map((tool, colIndex) =>
                  tool ? (
                    <div className="card-outside" key={tool.id}>
                      <a className="card anchor-link" href="#" data-dest={tool.id}>
                        <div className="text-center card-title">
                          <h2 style={{ color: "white", margin: 0, fontSize: "24px" }}>{tool.title}</h2>
                        </div>
                        <div className="card-body">
                          <p>{tool.desc}</p>
                        </div>
                      </a>
                    </div>
                  ) : (
                    <div
                      className="card-outside"
                      key={`placeholder-${rowIndex}-${colIndex}`}
                      style={{ visibility: "hidden" }}
                    >
                      <a className="card anchor-link" href="#">
                        <div className="text-center card-title">
                          <h2 style={{ color: "white", margin: 0, fontSize: "24px" }}></h2>
                        </div>
                        <div className="card-body">
                          <p></p>
                        </div>
                      </a>
                    </div>
                  )
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}