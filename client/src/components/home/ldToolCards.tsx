"use client";
import Link from "next/link";
import { Container, Row, Col, Card } from "react-bootstrap";

type Tool = {
  id: string;
  title: string;
  desc: string;
};

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
  { id: "ldpair", title: "LDpair", desc: "Investigate correlated alleles for a pair of variants in high LD." },
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
  { id: "ldscore", title: "LDscore", desc: "Calculate LD scores and perform LD score regression." },
  { id: "snpchip", title: "SNPchip", desc: "Find commercial genotyping platforms for variants." },
  { id: "snpclip", title: "SNPclip", desc: "Prune a list of variants by linkage disequilibrium." },
];

function CardLink(tool: Tool) {
  return (
    <Link key={tool.id} href={`/${tool.id}`} className="card border-0 card-outside">
      <Card.Title className="text-center text-white align-items-center fw-normal fs-4 m-0">{tool.title}</Card.Title>
      <Card.Body className="border-0 m-0 p-0">
        <Card.Text className="p-3">{tool.desc}</Card.Text>
      </Card.Body>
    </Link>
  );
}

export default function LdToolSection() {
  return (
    <div className="py-4" style={{ backgroundColor: "#536e84", width: "100vw", marginLeft: "calc(-50vw + 50%)" }}>
      <Container fluid="lg">
        <Row>
          {tools.map((tool, i) => {
            return (
              <Col key={i} xs={6} sm={4} md={3} className="mb-3">
                <CardLink {...tool} />
              </Col>
            );
          })}
        </Row>
      </Container>
    </div>
  );
}
