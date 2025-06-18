import React from "react";

export default function CitationsPage() {
  return (
    <div className="container py-4">
      <div className="text-center">
        <h2>
          <img
            src="/LDlink_logo_small_clear.png"
            alt="LDlink"
            style={{ verticalAlign: "bottom" }}
          />{" "}
          Citations
        </h2>
        <p>
          Thank you for using LDlink! If you use LDlink in any publication,
          please cite the LDlink manuscript and any relevant module publications:
        </p>
      </div>

      <div style={{ paddingLeft: "20px", paddingRight: "20px" }}>
        <p>
          Machiela MJ, Chanock SJ.{" "}
          <a
            href="http://www.ncbi.nlm.nih.gov/pubmed/?term=26139635"
            title="LDlink PubMed link"
            target="_blank"
            rel="noopener noreferrer"
          >
            LDlink: a web-based application for exploring population-specific
            haplotype structure and linking correlated alleles of possible
            functional variants.
          </a>{" "}
          <i>Bioinformatics</i>. 2015 Jul 2.
        </p>

        <p>
          Machiela MJ, Chanock SJ.{" "}
          <a
            href="http://www.ncbi.nlm.nih.gov/pubmed/?term=28968746"
            title="LDassoc PubMed link"
            target="_blank"
            rel="noopener noreferrer"
          >
            LDassoc: an online tool for interactively exploring genome-wide
            association study results and prioritizing variants for functional
            investigation.
          </a>{" "}
          <i>Bioinformatics</i>. 2017 Sept 12.
        </p>

        <p>
          Alexander TA, Machiela MJ.{" "}
          <a
            href="https://www.ncbi.nlm.nih.gov/pubmed/?term=31924160"
            title="LDpop PubMed link"
            target="_blank"
            rel="noopener noreferrer"
          >
            LDpop: an interactive online tool to calculate and visualize geographic LD patterns.
          </a>{" "}
          <i>BMC Bioinformatics</i>. 2020 Jan 10.
        </p>

        <p>
          Myers TA, Chanock SJ, Machiela MJ.{" "}
          <a
            href="https://www.ncbi.nlm.nih.gov/pubmed/32180801"
            title="LDlinkR PubMed link"
            target="_blank"
            rel="noopener noreferrer"
          >
            LDlinkR: An R Package for Rapidly Calculating Linkage Disequilibrium Statistics in Diverse Populations.
          </a>{" "}
          <i>Front. Genet</i>. 2020 Feb 28.
        </p>

        <p>
          Shu-Hong Lin, Derek W. Brown, Mitchell J. Machiela{" "}
          <a
            href="https://doi.org/10.1158/0008-5472.can-20-0985"
            title="LDtrait"
            target="_blank"
            rel="noopener noreferrer"
          >
            LDtrait: An Online Tool for Identifying Published Phenotype Associations in Linkage Disequilibrium
          </a>{" "}
          <i>Cancer Research</i>. 2020 Aug 14.
        </p>

        <p>
          Shu-Hong Lin, Rohit Thakur, Mitchell J. Machiela{" "}
          <a
            href="https://doi.org/10.1186/s12859-021-04531-8"
            title="LDexpress"
            target="_blank"
            rel="noopener noreferrer"
          >
            LDexpress: an online tool for integrating population-specific linkage disequilibrium patterns with tissue-specific expression data
          </a>{" "}
          <i>BMC Bioinformatics</i>. 2021 Dec 20.
        </p>
      </div>
    </div>
  );
}
