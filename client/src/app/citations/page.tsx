"use client";
import React from "react";
import { Container } from "react-bootstrap";
import Image from "next/image";

export default function CitationPage() {
  return (
    <Container className="py-4 tab-content mb-0">
        <div className="not-home">
            <div className="text-center">
        <h1>
          <Image
            src="/images/LDlink_logo_small_clear.png"
            alt="LDlink"
            style={{ verticalAlign: "bottom" }}
            width={91}
            height={36}
          />{" "}
          Citations
        </h1>
        <p>
          Thank you for using LDlink! If you use LDlink in any publication please cite the LDlink manuscript and any relevant module publications:
        </p>
      </div>
      <div style={{ paddingLeft: 20, paddingRight: 20 }}>
        <p>
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
        </p>
        <p>
          Machiela MJ, Chanock SJ.{" "}
          <a
            href="http://www.ncbi.nlm.nih.gov/pubmed/?term=28968746"
            title="LDassoc PubMed link"
            target="_blank"
            rel="noopener noreferrer"
            aria-label="LDassoc PubMed article link"
          >
            LDassoc: an online tool for interactively exploring genome-wide association study results and prioritizing variants for functional investigation.
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
            aria-label="LDpop PubMed article link"
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
            aria-label="LDlinkR PubMed article link"
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
            aria-label="LDtrait"
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
            aria-label="LDexpress"
          >
            LDexpress: an online tool for integrating population-specific linkage disequilibrium patterns with tissue-specific expression data
          </a>{" "}
          <i>BMC Bioinformatics</i>. 2021 Dec 20.
        </p>
         <p>
          Breeze C.E., Yao, X., Park, B., Kanigicherla, M., Lan, Q., Rothman, N., Teschendorff, A.E., Franceschini, N., Berndt, S.I., and Machiela, M.J.{" "}
          <a
            href="https://doi.org/10.64898/2025.12.19.695639"
            title="LDscore"
            target="_blank"
            rel="noopener noreferrer"
            aria-label="LDscore"
          >
            LDscore: a scalable, Python 3-powered web platform for LD score regression analysis. 2025.12.19.695639.
          </a>{" "}
          <i>bioRxiv</i>. 2025 Dec 19.
        </p>
        <p>
          Breeze, C.E., Haugen, E., Gutierrez-Arcelus, M., Yao, X., Teschendorff, A., Beck, S., Dunham, I., Stamatoyannopoulos, J., Franceschini, N., Machiela, M.J., Berndt, S.I.{" "}
          <a
            href="https://doi.org/10.1186/s13059-023-03126-1"
            title="FORGEdb article link"
            target="_blank"
            rel="noopener noreferrer"
            aria-label="FORGEdb article link"
          >
            FORGEdb: a tool for identifying candidate functional variants and uncovering target genes and mechanisms for complex diseases.
          </a>{" "}
          <i>Genome Biology</i>. 2024 Jan 2.
        </p>

      </div>
    </div>
      
    </Container>
  );
}