"use client";
import React from "react";
import LDToolCard from "@/components/cards/ldtool-card";

type Tool = {
  id: string;
  title: string;
  desc: string;
};

const tools = [
  { id: "ldassoc", title: "LDassoc", desc: "Interactively visualize association p-value results and linkage disequilibrium patterns for a genomic region of interest." },
  { id: "ldexpress", title: "LDexpress", desc: "Search if a list of variants (or variants in LD with those variants) is associated with gene expression in multiple tissue types." },
  { id: "ldhap", title: "LDhap", desc: "Calculate population specific haplotype frequencies of all haplotypes observed for a list of query variants." },
  { id: "ldmatrix", title: "LDmatrix", desc: "Create an interactive heatmap matrix of pairwise linkage disequilibrium statistics." },
  { id: "ldpair", title: "LDpair", desc: "Investigate correlated alleles for a pair of variants in high LD." },
  { id: "ldpop", title: "LDpop", desc: "Investigate allele frequencies and linkage disequilibrium patterns across 1000G populations." },
  { id: "ldproxy", title: "LDproxy", desc: "Interactively explore proxy and putatively functional variants for a query variant." },
  { id: "ldtrait", title: "LDtrait", desc: "Search if a list of variants (or variants in LD with those variants) have previously been associated with a trait or disease." },
  { id: "ldscore", title: "LDscore", desc: "Calculate LD scores and perform LD score regression." },
  { id: "snpchip", title: "SNPchip", desc: "Find commercial genotyping platforms for variants." },
  { id: "snpclip", title: "SNPclip", desc: "Prune a list of variants by linkage disequilibrium." },
];

const chunkTools = (tools: (Tool | null)[], size: number): (Tool | null)[][] => {
  const chunks: (Tool | null)[][] = [];
  for (let i = 0; i < tools.length; i += size) {
    const chunk = tools.slice(i, i + size);
    while (chunk.length < size) {
      chunk.push(null);
    }
    chunks.push(chunk);
  }
  return chunks;
};


export default function LdToolSection() {
  const rows = chunkTools(tools, 5);

  return (
    <main id="main-container" role="main">
      <div id="content" className="tab-content">
        <div className="tab-pane fade show active" id="home-tab">
          <div style={{ width: "100%", backgroundColor: "#536e84", padding: "40px 0" }}>
            {rows.map((row, rowIndex) => (
              <div className="card-row" key={rowIndex}>
                {row.map((tool, colIndex) =>
                  tool ? (
                    <LDToolCard key={tool.id} {...tool} />
                  ) : (
                    <div
                      key={`placeholder-${rowIndex}-${colIndex}`}
                      className="card-outside"
                      style={{ visibility: "hidden" }}
                    >
                      <div className="card anchor-link border-0">
                        <div className="text-center card-title">
                          <h2 style={{ color: "white", margin: 0, fontSize: "24px" }}></h2>
                        </div>
                        <div className="card-body"><p></p></div>
                      </div>
                    </div>
                  )
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </main>
  );
}
