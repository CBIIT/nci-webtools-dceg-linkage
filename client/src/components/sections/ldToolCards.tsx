"use client";
import React, { useEffect, useState } from "react";
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

// Helper to chunk for mobile: always 3 cards, then 2 cards (centered), repeat
const chunkToolsMobile = (tools: Tool[]): Array<Array<Tool | null>> => {
  const mobileRows: Array<Array<Tool | null>> = [];
  let i = 0;
  while (i < tools.length) {
    // First row: up to 3 cards
    const firstRow = tools.slice(i, i + 3);
    mobileRows.push(firstRow);
    i += 3;
    // Second row: up to 2 cards, left-aligned if 1, no nulls for 2 cards
    const secondRow = tools.slice(i, i + 2);
    if (secondRow.length === 1) {
      mobileRows.push([secondRow[0]]);
    } else if (secondRow.length === 2) {
      mobileRows.push(secondRow);
    }
    i += 2;
  }
  return mobileRows;
};

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
  const [isMobile, setIsMobile] = useState(false);
  const [isExtraSmall, setIsExtraSmall] = useState(false);

  useEffect(() => {
    const checkWidth = () => {
      setIsMobile(window.innerWidth <= 930);
      setIsExtraSmall(window.innerWidth <= 384);
    };
    checkWidth();
    window.addEventListener("resize", checkWidth);
    return () => window.removeEventListener("resize", checkWidth);
  }, []);

  // Helper for 2 cards per row
  const chunkTools2 = (tools: Tool[]): Array<Array<Tool | null>> => {
    const rows: Array<Array<Tool | null>> = [];
    for (let i = 0; i < tools.length; i += 2) {
      rows.push(tools.slice(i, i + 2));
    }
    return rows;
  };

  let rows;
  if (isExtraSmall) {
    rows = chunkTools2(tools);
  } else if (isMobile) {
    rows = chunkToolsMobile(tools);
  } else {
    rows = chunkTools(tools, 5);
  }

  return (
    <div id="ldtool-card-container" >
     
      <div id="content" className="tab-content">
        <div className="tab-pane fade show active" id="home-tab">
          <div style={{ margin: "auto", width: "100%", backgroundColor: "#536e84", padding: "40px 0" }}>
            {rows.map((row, rowIndex) => {
              const cardCount = row.filter(Boolean).length;
              const isTwoCards = (isMobile && cardCount === 2) || (isExtraSmall && cardCount === 2);
              const isOneCard = (isMobile && cardCount === 1) || (isExtraSmall && cardCount === 1);
              return (
                <div className={`card-row${isTwoCards ? ' two-cards' : ''}${isOneCard ? ' one-card' : ''}`} key={rowIndex}>
                  {isOneCard && <div className="card-spacer" />}
                  {row.map((tool, colIndex) =>
                    tool ? (
                      <LDToolCard key={tool.id} {...tool} />
                    ) : null
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
