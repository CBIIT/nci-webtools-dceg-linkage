import { Row } from "react-bootstrap";

export default function CitationBox() {
  return (
      <div style={{ wordBreak: 'normal', overflowWrap: 'break-word' }}>
          Machiela MJ, Chanock SJ.{" "}
          <a
            href="http://www.ncbi.nlm.nih.gov/pubmed/?term=26139635"
            title="LDlink PubMed link"
            target="_blank"
            rel="noopener noreferrer"
            aria-label="LDlink PubMed article link"
          >
            LDlink: a web-based application for exploring population-specific haplotype structure and linking correlated alleles of possible functional variants.
          </a>{" "}
          <i>Bioinformatics</i>. 2015 Jul 2.
      </div>
  );
}
