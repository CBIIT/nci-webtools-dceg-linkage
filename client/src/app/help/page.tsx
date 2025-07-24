"use client";
import React from "react";
import { Container } from "react-bootstrap";
import Image from "next/image";

export default function HelpPage() {
  return (
    <Container className="py-4 help-page tab-content mb-0">
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
            Documentation
          </h1>
        </div>
        <div className="pt-2">
          <p>
            LDlink is designed to be an intuitive and simple tool for investigating patterns of linkage disequilibrium
            across a variety of ancestral population groups. This help documentation page gives detailed description of
            the metrics calculated by LDlink modules and aids users in understanding all aspects of the required input
            and returned output. This application&apos;s source code can be viewed on{" "}
            <a href="https://github.com/CBIIT/nci-webtools-dceg-linkage" target="_blank" rel="noopener noreferrer">
              GitHub
            </a>
            . The documentation is divided into the following sections:
          </p>
          <p style={{ marginLeft: 40 }}>
            <a href="#Understanding_Linkage_Disequilibrium">
              <strong>Understanding Linkage Disequilibrium</strong>
            </a>
          </p>
          <p style={{ marginLeft: 80 }}>
            <a href="#linkage_equilibrium">
              <strong>Linkage Equilibrium</strong>
            </a>
          </p>
          <p style={{ marginLeft: 80 }}>
            <a href="#linkage_disequilibrium">
              <strong>Linkage Disequilibrium</strong>
            </a>
          </p>
          <p style={{ marginLeft: 80 }}>
            <a href="#haplotype">
              <strong>Haplotype</strong>
            </a>
          </p>
          <p style={{ marginLeft: 40 }}>
            <a href="#Data_Sources">
              <strong>Data Sources</strong>
            </a>
          </p>
          <p style={{ marginLeft: 80 }}>
            <a href="#dbSNP">
              <strong>dbSNP</strong>
            </a>
          </p>
          <p style={{ marginLeft: 80 }}>
            <a href="#1000_Genomes_Project">
              <strong>1000 Genomes Project</strong>
            </a>
          </p>
          <p style={{ marginLeft: 80 }}>
            <a href="#ucsc_refgene">
              <strong>UCSC RefSeq</strong>
            </a>
          </p>
          <p style={{ marginLeft: 80 }}>
            <a href="#regulomedb">
              <strong>RegulomeDB</strong>
            </a>
          </p>
          <p style={{ marginLeft: 80 }}>
            <a href="#recomb">
              <strong>Genetic Map</strong>
            </a>
          </p>
          <p style={{ marginLeft: 80 }}>
            <a href="#gtex">
              <strong>GTEx Portal</strong>
            </a>
          </p>
          <p style={{ marginLeft: 80 }}>
            <a href="#gwas_catalog">
              <strong>GWAS Catalog</strong>
            </a>
          </p>
          <p style={{ marginLeft: 80 }}>
            <a href="#forgedb">
              <strong>FORGEdb</strong>
            </a>
          </p>
          <p style={{ marginLeft: 40 }}>
            <a href="#Calculations">
              <strong>Calculations</strong>
            </a>
          </p>
          <p style={{ marginLeft: 80 }}>
            <a href="#D_prime">
              <strong>D prime</strong>
            </a>
          </p>
          <p style={{ marginLeft: 80 }}>
            <a href="#R_squared">
              <strong>R squared</strong>
            </a>
          </p>
          <p style={{ marginLeft: 80 }}>
            <a href="#Goodness_of_Fit">
              <strong>Goodness of Fit</strong>
            </a>
          </p>
          <p style={{ marginLeft: 40 }}>
            <a href="#Modules">
              <strong>Modules</strong>
            </a>
          </p>
          <p style={{ marginLeft: 80 }}>
            <a href="#LDassoc">
              <strong>LDassoc</strong>
            </a>
          </p>
          <p style={{ marginLeft: 80 }}>
            <a href="#LDexpress">
              <strong>LDexpress</strong>
            </a>
          </p>
          <p style={{ marginLeft: 80 }}>
            <a href="#LDhap">
              <strong>LDhap</strong>
            </a>
          </p>
          <p style={{ marginLeft: 80 }}>
            <a href="#LDmatrix">
              <strong>LDmatrix</strong>
            </a>
          </p>
          <p style={{ marginLeft: 80 }}>
            <a href="#LDpair">
              <strong>LDpair</strong>
            </a>
          </p>
          <p style={{ marginLeft: 80 }}>
            <a href="#LDpop">
              <strong>LDpop</strong>
            </a>
          </p>
          <p style={{ marginLeft: 80 }}>
            <a href="#LDproxy">
              <strong>LDproxy</strong>
            </a>
          </p>
          <p style={{ marginLeft: 80 }}>
            <a href="#LDtrait">
              <strong>LDtrait</strong>
            </a>
          </p>
          <p style={{ marginLeft: 80 }}>
            <a href="#LDscore">
              <strong>LDscore</strong>
            </a>
          </p>
          <p style={{ marginLeft: 80 }}>
            <a href="#SNPchip">
              <strong>SNPchip</strong>
            </a>
          </p>
          <p style={{ marginLeft: 80 }}>
            <a href="#SNPclip">
              <strong>SNPclip</strong>
            </a>
          </p>
          <p style={{ marginLeft: 40 }}>
            <a href="#FAQ">
              <strong>Frequently Asked Questions</strong>
            </a>
          </p>
          <hr />
          <section id="Understanding_Linkage_Disequilibrium">
            <h2 className="h3">Understanding Linkage Disequilibrium</h2>
            <p>
              <a id="linkage_equilibrium"></a>
              <strong>Linkage Equilibrium</strong> exists when alleles from two different genetic variants occur
              independently of each other. The inheritance of such variants follows probabilistic patterns governed by
              population allele frequencies. The vast majority of genetic variants on a chromosome are in linkage
              equilibrium. Variants in linkage equilibrium are not considered linked.
            </p>
            <p>
              <a id="linkage_disequilibrium"></a>
              <strong>Linkage Disequilibrium</strong> is present when alleles from two nearby genetic variants commonly
              occur together in a non-random, linked fashion. This linked mode of inheritance results from genetic
              variants in close proximity being less likely to be separated by a recombination event and thus alleles of
              the variants are more commonly inherited together than expected. Alleles of variants in linkage
              disequilibrium are correlated; with the degree of correlation generally greater in magnitude the closer
              the variants are in physical distance. Measures of linkage disequilibrium include{" "}
              <a href="#D_prime">D prime (D&apos;)</a> and{" "}
              <a href="#R_squared">
                R squared (R<sup>2</sup>)
              </a>
              .
            </p>
            <p>
              <a id="haplotype"></a>
              <strong>Haplotype</strong> is a cluster of genetic variants that are inherited together. Humans are
              diploid; having maternal and paternal copies of each autosomal chromosome. Each chromosomal copy is
              organized into segments of high linkage disequilibrium, called haplotype &quot;blocks&quot;. Due to unique
              population histories and differences in variant allele frequencies, haplotype structure tends to be
              population specific. Although haplotypes are essential for calculating measures of linkage disequilibrium,
              haplotypes are seldom directly observed. Statistical chromosome phasing techniques are often necessary to
              infer individual haplotypes.
            </p>
          </section>
          <hr />
          <section id="Data_Sources">
            <h3>Data Sources</h3>
            <p>
              <a id="dbSNP"></a>
              <strong>
                <a href="https://www.ncbi.nlm.nih.gov/snp/" target="_blank" rel="noopener noreferrer">
                  dbSNP
                </a>
              </strong>{" "}
              (source:{" "}
              <a href="https://ftp.ncbi.nih.gov/snp/" target="_blank" rel="noopener noreferrer">
                GRCh37 and GRCh38
              </a>
              ) - To investigate patterns of linkage disequilibrium, LDlink focuses on two main class of genetic
              variation: single nucleotide polymorphisms (SNPs) and insertions/deletions (indels). Every module of
              LDlink requires the entry of at least one variant as identified by a RefSNP number (RS number) or genomic
              position (chr#:position). RS numbers have been assigned by dbSNP and are well-curated identifiers that
              follow the format &quot;rs&quot; followed by 1 to 8 numbers. The current implementation of LDlink
              references dbSNP and only accepts input for bi-allelic variants.
            </p>
            <p>
              <a id="1000_Genomes_Project"></a>
              <strong>
                <a href="https://www.internationalgenome.org/" target="_blank" rel="noopener noreferrer">
                  1000 Genomes Project
                </a>
              </strong>{" "}
              (source:{" "}
              <a
                href="http://ftp.1000genomes.ebi.ac.uk/vol1/ftp/release/20130502/"
                target="_blank"
                rel="noopener noreferrer">
                GRCh37
              </a>
              ,{" "}
              <a
                href="http://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1000_genomes_project/release/20190312_biallelic_SNV_and_INDEL/"
                target="_blank"
                rel="noopener noreferrer">
                GRCh38
              </a>
              , and{" "}
              <a
                href="http://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1000G_2504_high_coverage/working/20201028_3202_phased/"
                target="_blank"
                rel="noopener noreferrer">
                GRCh38 High Coverage
              </a>
              ) - Publicly available reference haplotypes from the 1000 Genomes Project are used by LDlink to calculate
              population-specific measures of linkage disequilibrium. Haplotypes are available for continental
              populations (ex: European, African, and Admixed American) and sub-populations (ex: Finnish, Gambian, and
              Peruvian). All LDlink modules require the selection of at least one 1000 Genomes Project sub-population,
              but several sub-populations can be selected simultaneously. Available haplotypes vary by sub-population
              based on sample size.
            </p>
            <p>
              <a id="ucsc_refgene"></a>
              <strong>
                <a href="https://genome.ucsc.edu/cgi-bin/hgTables" target="_blank" rel="noopener noreferrer">
                  UCSC RefSeq
                </a>
              </strong>{" "}
              (source:{" "}
              <a
                href="https://genome.ucsc.edu/cgi-bin/hgTables?hgsid=1196412861_bzHfOz59YBcRs96UaRLkQjHBova0&clade=mammal&org=Human&db=hg19&hgta_group=genes&hgta_track=refSeqComposite&hgta_table=0&hgta_regionType=genome&position=chrX%3A15%2C578%2C261-15%2C621%2C068&hgta_outputType=primaryTable&hgta_outFileName="
                target="_blank"
                rel="noopener noreferrer">
                GRCh37
              </a>{" "}
              and{" "}
              <a
                href="https://genome.ucsc.edu/cgi-bin/hgTables?hgsid=1196412861_bzHfOz59YBcRs96UaRLkQjHBova0&clade=mammal&org=&db=hg38&hgta_group=genes&hgta_track=refSeqComposite&hgta_table=ncbiRefSeq&hgta_regionType=genome&position=&hgta_outputType=primaryTable&hgta_outFileName="
                target="_blank"
                rel="noopener noreferrer">
                GRCh38
              </a>
              ) - Publicly available gene transcripts from the UCSC Table Browser are used by LDlink&apos;s{" "}
              <a href="#LDassoc">LDassoc</a>, <a href="#LDmatrix">LDmatrix</a>, and <a href="#LDproxy">LDproxy</a>{" "}
              modules to display genes within the genomic window of interest.
            </p>
            <p>
              <a id="regulomedb"></a>
              <strong>
                <a href="https://regulomedb.org/" target="_blank" rel="noopener noreferrer">
                  RegulomeDB
                </a>
              </strong>{" "}
              (source:{" "}
              <a
                href="https://www.encodeproject.org/files/ENCFF297XMQ/@@download/ENCFF297XMQ.tsv"
                target="_blank"
                rel="noopener noreferrer">
                GRCh37
              </a>
              ) - Publicly available scores from RegulomeDB are used by LDlink&apos;s <a href="#LDassoc">LDassoc</a> and{" "}
              <a href="#LDproxy">LDproxy</a> modules to rank available datatypes for a single coordinate. GRCh38 support
              is added via{" "}
              <a href="https://genome.ucsc.edu/cgi-bin/hgLiftOver" target="_blank" rel="noopener noreferrer">
                liftOver
              </a>
              .
            </p>
            <p>
              <a id="recomb"></a>
              <strong>
                <a
                  href="https://mathgen.stats.ox.ac.uk/impute/1000GP_Phase3.html"
                  target="_blank"
                  rel="noopener noreferrer">
                  Genetic Map
                </a>
              </strong>{" "}
              (source:{" "}
              <a
                href="https://mathgen.stats.ox.ac.uk/impute/1000GP_Phase3.html"
                target="_blank"
                rel="noopener noreferrer">
                GRCh37
              </a>
              ) - Publicly available combined recombination rates (cM/Mb) from the 1000 Genomes Project are used by
              LDlink&apos;s <a href="#LDassoc">LDassoc</a> and <a href="#LDproxy">LDproxy</a> modules to show
              recombination at specific coordinates. GRCh38 support is added via{" "}
              <a href="https://genome.ucsc.edu/cgi-bin/hgLiftOver" target="_blank" rel="noopener noreferrer">
                liftOver
              </a>
              .
            </p>
            <p>
              <a id="gtex"></a>
              <strong>
                <a href="https://www.gtexportal.org/home/" target="_blank" rel="noopener noreferrer">
                  GTEx Portal
                </a>
              </strong>{" "}
              (source:{" "}
              <a
                href="https://storage.googleapis.com/gtex_analysis_v8/single_tissue_qtl_data/GTEx_Analysis_v8_eQTL.tar"
                target="_blank"
                rel="noopener noreferrer">
                GRCh38
              </a>
              ) - Publicly available single-tissue cis-QTL data from the GTEx Portal is used by LDlink&apos;s{" "}
              <a href="#LDexpress">LDexpress</a> module to show significant variant-gene associations in multiple tissue
              types. GRCh37 support is added via{" "}
              <a
                href="https://storage.googleapis.com/gtex_analysis_v8/reference/GTEx_Analysis_2017-06-05_v8_WholeGenomeSeq_838Indiv_Analysis_Freeze.lookup_table.txt.gz"
                target="_blank"
                rel="noopener noreferrer">
                GTEx lookup table
              </a>
              .
            </p>
            <p>
              <a id="gwas_catalog"></a>
              <strong>
                <a href="https://www.ebi.ac.uk/gwas/home" target="_blank" rel="noopener noreferrer">
                  GWAS Catalog
                </a>
              </strong>{" "}
              (source:{" "}
              <a
                href="https://www.ebi.ac.uk/gwas/api/search/downloads/alternative"
                target="_blank"
                rel="noopener noreferrer">
                GRCh38
              </a>
              ) - Publicly available NHGRI-EBI Catalog of human genome-wide association studies from GWAS Catalog is
              used by LDlink&apos;s <a href="#LDtrait">LDtrait</a> module to search if variants have previously been
              associated with a trait or disease. GRCh37 support is added via <a href="#dbSNP">dbSNP</a>.
            </p>
            <p>
              <a id="forgedb"></a>
              <strong>
                <a href="https://forgedb.cancer.gov/" target="_blank" rel="noopener noreferrer">
                  FORGEdb
                </a>
              </strong>{" "}
              (source:{" "}
              <a href="https://forgedb.cancer.gov/" target="_blank" rel="noopener noreferrer">
                FORGEdb
              </a>
              ) - Publicly available scores from FORGEdb are used by LDlink&apos;s LDassoc and LDproxy modules to rank
              putative functionality for a single variant by RSID.
            </p>
          </section>
          <hr />
          <section id="Calculations">
            <h3>Calculations</h3>
            <p>
              LDlink modules report the following measures of linkage disequilibrium: <a href="#D_prime">D prime</a>,{" "}
              <a href="#R_squared">R squared</a>, and <a href="#Goodness_of_Fit">goodness-of-fit</a> statistics. Below
              is a brief description of each measure.
            </p>
            <p>
              <a id="D_prime"></a>
              <strong>D prime (D&apos;)</strong> - an indicator of allelic segregation for two genetic variants. D&apos;
              values range from 0 to 1 with higher values indicating tight linkage of alleles. A D&apos; value of 0
              indicates no linkage of alleles. A D&apos; value of 1 indicates at least one expected haplotype
              combination is not observed.
            </p>
            <p>
              <a id="R_squared"></a>
              <strong>
                R squared (R<sup>2</sup>)
              </strong>{" "}
              - a measure of correlation of alleles for two genetic variants. R<sup>2</sup> values range from 0 to 1
              with higher values indicating a higher degree of correlation. An R<sup>2</sup> value of 0 indicates
              alleles are independent, whereas an R<sup>2</sup> value of 1 indicates an allele of one variant perfectly
              predicts an allele of another variant. R<sup>2</sup> is sensitive to allele frequency.
            </p>
            <p>
              <a id="Goodness_of_Fit"></a>
              <strong>
                Goodness of Fit (&#935;<sup>2</sup> and p-value)
              </strong>{" "}
              - statistical test testing whether observed haplotype counts follow frequencies expected from variant
              allele frequencies. High chi-square statistics and low p-values are evidence that haplotype counts deviate
              from expected values and suggest linkage disequilibrium may be present.
            </p>
          </section>
          <hr />
          <section id="Modules">
            <h3>Modules</h3>
            <p>
              LDlink consists of eleven modules:{" "}
              {modules.map((mod, idx) => (
                <span key={mod.id}>
                  <a href={`#${mod.id}`}>{mod.name}</a>
                  {idx < modules.length - 1 ? ", " : "."}
                </span>
              ))}
              Choose between GRCh37 (hg19), GRCh38 (hg38), and GRCh38 High Coverage (hg38) 1000 Genome Project datasets
              with the Genome Build (1000G) dropdown menu on the top left. Each module can be accessed by clicking on LD
              Tools dropdown at the top of all LDlink pages. Below is a description of each module, the required user
              input, and an explanation of the returned output.
            </p>
            <div style={{ marginLeft: 40 }}>
              {modules.map((mod) => (
                <section id={mod.id} key={mod.id}>
                  <div style={{ display: "flex", gap: "8px" }}>
                    <h4 style={{ textDecoration: "underline", margin: 0 }}>{mod.name}</h4>
                    <span dangerouslySetInnerHTML={{ __html: `- ${mod.description}` }} />
                  </div>
                  <div className="pt-3" style={{ marginLeft: 24 }}>
                    <p>
                      <strong>Input:</strong>
                    </p>
                    <ul>
                      {mod.input.map((item, idx) => (
                        <li key={idx} dangerouslySetInnerHTML={{ __html: item }} />
                      ))}
                    </ul>

                    <p>
                      <strong>Output:</strong>
                    </p>
                    <ul>
                      {mod.output.map((item, idx) => (
                        <li key={idx} dangerouslySetInnerHTML={{ __html: item }} />
                      ))}
                    </ul>
                  </div>
                </section>
              ))}
            </div>
          </section>
          <hr />
          <section id="FAQ">
            <h3>Frequently Asked Questions</h3>
            <div style={{ marginLeft: 40 }}>
              {faqList.map((faq, idx) => (
                <div key={idx} style={{ marginBottom: 16 }}>
                  <p>
                    <strong>{faq.question}</strong>
                  </p>
                  <p dangerouslySetInnerHTML={{ __html: faq.answer }} />
                </div>
              ))}
            </div>
          </section>
          {/* Continue converting the rest of the help.html content as needed. */}
        </div>
      </div>
    </Container>
  );
}

// FAQ data array
const faqList = [
  {
    question: "Why is my variant RS number bringing up an error?",
    answer: `LDlink modules only accepts input for variant RS numbers that are
      bi-allelic. Ensure your query SNP has A/C, A/G, A/T, C/G,
      C/T, or G/T alleles. RS numbers for insertions or deletions (i.e.
      "indels") are also now accepted as input. If a variant you believe is
      bi-allelic is not accepted, check dbSNP to ensure there are only two
      alleles for the variant. Even if there is only one reports of a
      variant being tri- or multi-allelic in dbSNP, the variant is not considered
      valid input under the current implementation of LDlink.`,
  },
  {
    question: "What 1000 Genomes population should I select for my LDlink query?",
    answer: `Choosing the correct
      reference 1000 Genomes Project population
      is essential for comparability of results from LDlink to your
      population of interest. In general, try to select the sub-population
      that best matches the ancestry of your study population. While LDlink
      allows for multiple 1000 Genomes sub-populations to be selected
      simultaneously, it is recommended to first investigate the patterns of
      linkage disequilibrium in the query region of each sub-population
      before considering whether to combine sub-populations in a query.`,
  },
  {
    question: "What is the estimated running time for an LDproxy query?",
    answer: `Running time varies greatly
      for LDproxy ranging from a few
      seconds to approximately one minute. For each query, LDproxy actively
      calculates all LD metrics based on user input. A variety of factors
      affect overall running time including: (1) the number of haplotypes
      available for the sub-population(s), (2) the number of dbSNP variants in
      the region queried, (3) the current utilization of the LDlink server,
      and (4) the download speed of your internet connection. In general, the
      best way to speed up an LDlink query is to only select one
      sub-population per query. Queries that include multiple sub-populations
      or ancestral groups take much longer to complete than single
      sub-population queries and tie up limited system resources.`,
  },
  {
    question: "How do I save output files?",
    answer: `Output from a variety of
      LDlink modules (LDhap, LDmatrix, and
      LDproxy) is available for download. To save output either (1) right
      click or long press on the link and select the "Save Link As…" option
      or (2) open the link in a new browser window and copy and paste the
      contents to a new file.`,
  },
  {
    question: "Can I save the plots generated in LDmatrix or LDproxy?",
    answer: `Yes. Click the Save icon on
      the top right of the plot. A
      preview window will appear. Right click or long press on the preview
      image, select "Save As…", and choose a filename for the plot image.`,
  },
  {
    question: "Does LDproxy display all variants in the window around the query variant?",
    answer: `For plotting and performance issues, LDproxy plots only include variants with R<sup>2</sup>
      values greater than 0.01.
      Additionally, the LDproxy download also only includes variants with R<sup>2</sup> values greater than 0.01.`,
  },
  {
    question: "What is the maximum number of variants LDhap and LDmatrix can accept as input?",
    answer: `LDhap has a limit of 30 variants
      and LDmatrix has a limit of 300 variants. LDmatrix supports up to 1,000 variants via API call. These limits were selected to optimize query speed and
      visualization of results.`,
  },
  {
    question: "Why are the variants in LDhap and LDmatrix output not in the same order as the input?",
    answer: `Variants in LDhap and LDmatrix
      output are not ordered based on user
      input. Rather, results are ordered based on chromosomal order.`,
  },
  {
    question: "Why does my computer seem slow when using LDlink?",
    answer: `The interactive plots
      produced by LDmatrix and LDproxy require
      a sizeable amount of data and java script to be loaded into the web
      browser. On some computers this results in a notable lag in
      performance. To improve performance, simply
      refresh the LDlink webpage to clear the temporary data from memory.
      Refreshing the LDlink webpage will remove all interactive plots.`,
  },
  {
    question: "What genome build does LDlink use for genomic coordinates?",
    answer: `LDlink supports
      GRCh37 (hg19) and GRCh38 (hg38). Choose between GRCh37 (hg19), GRCh38 (hg38), and GRCh38 High Coverage (hg38) 1000 Genome Project datasets with the Genome Build (1000G) dropdown menu on the top left.`,
  },
  {
    question: "Why do variant coordinates not always match dbSNP or UCSC coordinates?",
    answer: `All coordinates in LDlink are based on
      variant positions in the 1000 Genomes VCF files. Slight difference in
      positions may be observed due to updates in mapping and alignment. Please
      refer to <a href="#dbSNP">dbSNP</a>
      for the most up-to-date information on variant coordinates.`,
  },
  {
    question: "What browsers are supported by LDlink?",
    answer: `LDlink has been tested to
      work with Internet Explorer 10+, Chrome, Firefox 36+ and Safari. LDlink
      will not display correctly with Internet Explorer 9 and below or Firefox 35 and below.`,
  },
];

const modules = [
  {
    id: "LDassoc",
    name: "LDassoc",
    description:
      "Interactively visualize association p-value results and linkage disequilibrium patterns for a genomic region of interest. Based on the file size, number of variants and selected query populations, this module may take some time to run.",
    input: [
      "<u>Association data file</u> - upload a space or tab delimited file containing chromosome, position and p-value for each variant. A file header, while not required, will be useful when selecting input columns. Once the file is uploaded the user needs to specify which columns are the respective chromosome, position, and association p-values. Uploaded files will be stored on our secure server for use during LDassoc sessions and will be deleted after 4 hours.",
      "<u>Select region</u> - choices are <i>Gene</i>, <i>Region</i>, or <i>Variant</i>. <i>Gene</i> requires a RefSeq gene name and base pair window and allows for an optional index variant. <i>Region</i> requires genomic start and end coordinates and allows for an optional index variant. <i>Variant</i> requires an index variant and allows for an optional base pair window (500,000bp is the default). The index variant will be plotted in blue and is used to calculate all pairwise LD statistics. If not required, LDassoc will designate the variant with the lowest p-value as the index variant, unless otherwise specified.",
      "<u>Reference population(s)</u> - selected from the drop down menu. At least one 1000 Genomes Project sub-population is required, but more than one may be selected.",
      "<u>LD measure</u> - select if desired output is based on estimated R<sup>2</sup> or D&apos;.",
      "<u>Collapse transcripts</u> - choose to combine gene transcripts with the same name in the gene plot.",
      "<u>RegulomeDB annotation</u> - choose to display RegulomeDB scores in the interactive plot.",
    ],
    output: [
      "<u>Interactive plot</u> - interactive plot of index variant and p-values of all bi-allelic variants in the specified plotting region. X axis is the chromosomal coordinates and the Y axis is the -log10 p-value as well as the combined recombination rate. Each point represents a variant and is colored based on D&apos; or R<sup>2</sup>, sized based on minor allele frequency, and labeled based on regulatory potential. Hovering over the point will display detailed information on the index and proxy variants.",
      '<u>UCSC link</u> - external link to the plotted region in the <a href="https://genome.ucsc.edu/cgi-bin/hgGateway" target="_blank" rel="noopener noreferrer">UCSC Genome Browser</a>. This is useful for exploring nearby genes and regulatory elements in the region.',
      '<u>Table of Association Results</u> - by default, the ten variants with the lowest p-values and closest distance to the index variant are displayed. External links lead to the variant RS number in <a href="#dbSNP">dbSNP</a>, coordinates in the UCSC Genome Browser, and regulatory information (if any) in <a href="#regulomedb">RegulomeDB</a>.',
      "<u>Download association data for all variants</u> - download a file with information on all variants within the plotting region.",
    ],
  },
  {
    id: "LDexpress",
    name: "LDexpress",
    description:
      'Search if a list of variants (or variants in LD with those variants) is associated with gene expression in tissues of interest. Quantitative trait loci data is downloaded from the <a href="#gtex">GTEx Portal</a> (GTEx v8).',
    input: [
      "<u>List of RS numbers</u> - this can either be entered one per line in the text entry box or uploaded as a file that contains a list of RS numbers in the first column. A maximum of 10 variant RS numbers or chromosomal coordinates (GRCh37) are permitted. All input variants must match a bi-allelic variant. The text entry field is automatically filled if a file of SNPs or genomic coordinates is uploaded.",
      "<u>Reference population(s)</u> - selected from the drop-down menu. At least one 1000 Genomes Project sub-population is required, but more than one may be selected.",
      "<u>R<sup>2</sup>/D&apos; toggle</u> - select if desired output is filtered from a threshold based on estimated R<sup>2</sup> or D&apos;.",
      "<u>R<sup>2</sup>/D&apos; threshold</u> - set threshold for LD filtering. Any variants within -/+ of the specified genomic window and R<sup>2</sup> or D&apos; less than the threshold will be removed. Value needs to be in the range 0 to 1. Default value is 0.1.",
      "<u>Tissue(s)</u> - select the GTEx tissue or tissues of interest for searching for eQTLs.",
      '<u>P-value threshold</u> - define the eQTL significance threshold used for returning query results. Default value is 0.1 which returns all GTEx eQTL associations with P-value less than 0.1. Values can be entered in scientific notation (i.e. "1e-5").',
      "<u>Window size</u> - set genomic window size for LD calculation. Specify a value greater than or equal to zero and less than or equal to 1,000,000bp. Default value is -/+ 500,000bp.",
    ],
    output: [
      "<u>Variants in LD with variants in GTEx QTL</u> - a list of queried variants in LD with a variant reported in the GTEx QTL data. Each variant in the list is a clickable link that brings up a detailed table showing genes with expression associated variants that are in linkage disequilibrium with the input variant(s).",
      "<u>Details Tables</u> - output table that appears when a variant in the variant list is clicked. Details are provided on SNP rsID, genomic position, R2, D', Gene Symbol of associated gene expression, Gencode ID of the expressed gene, tissue where the association was observed, Effect Size, and P-value. External links lead to the QTL page in the GTEx portal.",
      "<u>Variants with Warnings</u> - output table that appears when a variant produces a warning in LDexpress. Common reasons for a variant to be on the warning list are if the variant is not found in dbSNP/GTEx or if no variants in LD are found within window of the 1000G reference VCF file. Details are provided on genomic position and why the variant was excluded from the variant list.",
      "<u>Download GTEx QTL list</u> - clickable link to download a text file in tab-delimited format that lists all query variant RS numbers, respective QTL which are in LD with query variant, and associated gene expression.",
    ],
  },
  {
    id: "LDhap",
    name: "LDhap",
    description:
      "Calculate haplotype frequencies for a list of up to 30 bi-allelic variants in a selected population. Results include a table of haplotype frequencies and a downloadable file.",
    input: [
      "<u>List of RS numbers</u> - this can either be entered one per line in the text entry box or uploaded as a file that contains a list of RS numbers in the first column. A maximum of 30 variant RS numbers are permitted. All input variants must be on the same chromosome and match a bi-allelic variant. The text entry field is automatically filled with the contents of the uploaded file.",
      "<u>Reference population(s)</u> - selected from the drop down menu. At least one 1000 Genomes Project sub-population is required, but more than one may be selected.",
    ],
    output: [
      '<u>Table of observed haplotypes</u>  - haplotypes with frequencies greater than 1 percent are displayed vertically and ordered by observed frequency in the selected query sub-population. Variant genotypes are reported in rows and and are sorted by genomic position. Queries should be limited to nearby variants, since haplotype switch rate errors become more common as genomic distance increases. Links are available to <a href="#dbSNP">dbSNP</a> RS numbers and coordinates in the<a href="https://genome.ucsc.edu/cgi-bin/hgGateway" target="_blank">UCSC Genome Browser</a>.',
      "<u>Variant file download</u> - download a file listing the order of the queried variants. Variants are ordered by genomic location. This file is used as a key for the order of genotypes in the haplotype file. Only bi-allelic variants with matching dbSNP RS numbers are included. All others are filtered out.",
      "<u>Haplotype file download</u> - download a file of all observed haplotypes. Haplotype genotypes are in the order of the above variant file.",
    ],
  },
  {
    id: "LDmatrix",
    name: "LDmatrix",
    description: "Create an interactive heatmap matrix of pairwise linkage disequilibrium statistics.",
    input: [
      "<u>List of RS numbers</u> - this can either be entered one per line in the text entry box or uploaded as a file that contains a list of RS numbers in the first column. A maximum of 300 variant RS numbers are permitted. All input variants must be on the same chromosome and match a bi-allelic variant. The text entry field is automatically filled with the contents of the uploaded file.",
      "<u>Reference population(s)</u> - selected from the drop down menu. At least one 1000 Genomes Project sub-population is required, but more than one may be selected.",
      "<u>Genome build</u> - choose to combine gene transcripts with the same name in the gene plot.",
    ],
    output: [
      "<u>Interactive heat map</u> - a square plot with dimensions equal to the number of query variants that match a dbSNP RS number. Hovering over the plot with the mouse will display pairwise LD metrics for the respective row and column variants. Variants are ordered by genomic coordinates.",
      "<u>D prime download </u> - download a file of all pairwise D' statistics.",
      "<u>R squared download</u> - - download a file of all pairwise R2 statistics.",
    ],
  },
  {
    id: "LDpair",
    name: "LDpair",
    description: "Investigate correlated alleles for a pair of variants in high LD.",
    input: [
      "<u>Pair of RS numbers</u> - RS number for query variant 1. RS number must match a bi-allelic variant.",
      "<u>Reference population(s)</u> - RS number for query variant 2. RS number must match a bi-allelic variant.",
      "<u>Genome build</u>  selected from the drop down menu. At least one 1000 Genomes Project sub-population is required, but more than one may be selected.",
    ],
    output: [
      '<u>Two-by-two table</u> - contingency table displaying haplotype counts and allele frequencies for the two query variants. External links are available to dbSNP RS numbers and coordinates in the <a href="https://genome.ucsc.edu/cgi-bin/hgGateway" target="_blank" rel="noopener noreferrer">UCSC Genome Browser</a>.',
      "<u>Haplotypes</u> - haplotype genotypes, counts, and frequencies.",
      "<u>Statistics</u> - calculated metrics of linkage disequilibrium including: D prime (D'), R square (R<sup>2</sup>), and goodness-of-fit (Chi-square and p-value). Goodness-of-fit tests for deviations of expected haplotype frequencies based on allele frequencies.",
      "<u>Correlated Alleles </u> - alleles that are correlated if linkage disequilibrium is present (R<sup>2</sup> > 0.1). If linkage equilibrium, no alleles are reported.",
    ],
  },
  {
    id: "LDpop",
    name: "LDpop",
    description: "Investigate allele frequencies and linkage disequilibrium patterns across 1000G populations.",
    input: [
      "<u>Variant1 RS number</u> -  RS number for query variant 1. RS number must match a bi-allelic variant.",
      "<u>Variant2 RS number</u> - RS number for query variant 2. RS number must match a bi-allelic variant.",
      "<u>Reference population(s)</u>  selected from the drop down menu. At least one 1000 Genomes Project sub-population is required, but more than one may be selected.",
      "<u>R<sup>2</sup>/D' toggle </u> - select if desired output is based on estimated R<sup>2</sup> or D'.",
    ],
    output: [
      "<u>Interactive maps</u> - three interactive maps will be returned as tabbed output. The first tab displays a map with the chosen linkage disequilibrium measure between query variants 1 and 2 for the selected 1000G populations. The second and third tabs will display maps of allele frequency distribution for query variants 1 and 2, respectively, for the selected 1000G populations. Map pins are color coded based on LD/allele frequency and when clicked display additional information for the population.",
      "<u>Table of populations</u> - a searchable and sortable table is generated showing allele frequency and LD values for the query variants and selected 1000G populations.",
      "<u>Download table</u> - link to download data in the table of populations.",
    ],
  },
  {
    id: "LDproxy",
    name: "LDproxy",
    description:
      "Interactively explore proxy and putatively functional variants for a query variant. Based on the selected query populations, this module may take some time to run.",
    input: [
      "<u>Variant RS number</u> - RS number for query variant. RS number must match a bi-allelic variant.",
      "<u>Reference population(s)</u> - selected from the drop down menu. At least one 1000 Genomes Project sub-population is required, but more than one may be selected.",
      "<u>LD measure</u> - select if desired output is based on estimated R<sup>2</sup> or D'.",
      "<u>Collapse transcripts</u> - choose to combine gene transcripts with the same name in the gene plot.",
    ],
    output: [
      "<u>Interactive plot </u> - interactive plot of query variant and all bi-allelic dbSNP variants plus or minus 500 kilobases(Kb) of the query variant. X axis is the chromosomal coordinates and the Y axis is the pairwise R2 value with the query variant as well as the combined recombination rate. Each point represents a proxy variant and is colored based on function, sized based on minor allele frequency, and labeled based on regulatory potential. Hovering over the point will display detailed information on the query and proxy variants.",
      "<u>UCSC link</u> - external link to the plotted region (query variant -/+ 500 Kb) in the UCSC Genome Browser. This is useful for exploring nearby genes and regulatory elements in the region.",
      '<u>Table of proxy variants</u> - by default, the ten variants with the highest R2 values and closest distance to the query variant are displayed. External links lead to the variant RS number in <a href="#dbSNP">dbSNP</a>, coordinates in the <a href="https://genome.ucsc.edu/cgi-bin/hgGateway"  target="_blank">UCSC Genome Browser</a>, and regulatory information (if any) in <a href="#regulomedb">RegulomeDB</a>.',
      "<u>Download all proxy variants </u> - download a file with information on all variants -/+ 500 Kb of the query variant with a pairwise R<sup>2</sup> value greater than 0.01.",
    ],
  },
  {
    id: "LDtrait",
    name: "LDtrait",
    description:
      'Search if a list of variants (or variants in LD with those variants) that have previously been associated with a trait or disease. Trait and disease data is updated nightly from the <a href="#gwas_catalog">GWAS Catalog</a>. Problematic data entries in the GWAS Catalog can be browsed <a href="./LDlinkRestWeb/tmp/ldtrait_error_snps.json" target="_blank">here</a>.',
    input: [
      "<u>List of RS numbers</u> - this can either be entered one per line in the text entry box or uploaded as a file that contains a list of RS numbers in the first column. A maximum of 50 variant RS numbers or chromosomal coordinates (GRCh37) are permitted. All input variants must match a bi-allelic variant. The text entry field is automatically filled with the contents of the uploaded file.",
      "<u>Reference population(s)</u>  selected from the drop-down menu. At least one 1000 Genomes Project sub-population is required, but more than one may be selected.",
      "<u>R<sup>2</sup>/D' toggle</u> - select if desired output is filtered from a threshold based on estimated R<sup>2</sup> or D'.",
      "<u>R<sup>2</sup>/D' threshold</u> - set threshold for LD filtering. Any variants within -/+ of the specified genomic window and R<sup>2</sup> or D' less than the threshold will be removed. Value needs to be in the range 0 to 1. Default value is 0.1.",
      "<u>Window size</u> - set genomic window size for LD calculation. Specify a value greater than or equal to zero and less than or equal to 1,000,000bp. Default value is -/+ 500,000bp.",
    ],
    output: [
      "<u>Variants in LD with GWAS Catalog</u> -  a list of queried variants in LD with a variant reported in the GWAS Catalog. Each variant in the list is a clickable link that brings up a detailed table showing disease-associated variants that are in linkage disequilibrium with the variant.",
      '<u>Details Tables</u> - output table that appears when a variant in the variant list is clicked. Details are provided on GWAS trait, genomic position, alleles, R2, D\', Effect Size (95% CI), Beta or OR, and P-value. External links lead to the result variant in the <a href="#gwas_catalog">GWAS Catalog</a>.',
      "<u>Variants with Warnings</u> - - output table that appears when a variant produces a warning in LDtrait. Common reasons for a variant to be on the warning list are if the variant is not found in dbSNP or if no variants in LD are found within window of the GWAS Catalog. Details are provided on genomic position and why the variant was excluded from the variant list.",
      "<u>Download GWAS Catalog annotated variant list</u> - clickable link to download a text file in tab-delimited format that lists all query variant RS numbers and their respective GWAS Catalog results.",
    ],
  },
  {
    id: "LDscore",
    name: "LDscore",
    description:
      'Perform LD score regression analysis online utilizing the ldsc tool developed in <a href=https://github.com/bulik/ldsc target="_blank">https://github.com/bulik/ldsc</a>.',
    input: [
      "<u>For LD score calculation </u> - genotype information as .bim/.bed/.fam files, as well as window in centiMorgan (cM) or kilobasepairs (kb) selected from the drop-down menu.",
      '<u>For heritability analysis</u> GWAS summary statistics (format: tab-separated files with columns accepted by <a href="https://github.com/bulik/ldsc/blob/master/munge_sumstats.py" target="_blank"> https://github.com/bulik/ldsc/blob/master/munge_sumstats.py</a>, e.g. with effect size, p-value, SNP identifiers, and allelic information, note header naming format is important). For example: SNP (Variant ID e.g., rs number), A1 (Allele 1, interpreted as reference allele for signed sumstat), A2 (Allele 2, interpreted as non-reference allele for signed sumstat), Frq (Allele frequency), BETA or [linear/logistic] regression coefficient (0 --> no effect; above 0 --> A1 is trait/risk increasing), P (p-Value), N (Sample size). In addition, a reference population needs to be selected from the drop down menu.',
      '<u>For genetic correlation</u> - GWAS summary statistics (format: tab-separated files with columns accepted by <a href="https://github.com/bulik/ldsc/blob/master/munge_sumstats.py" target="_blank"> https://github.com/bulik/ldsc/blob/master/munge_sumstats.py</a>, e.g. with effect size, p-value, SNP identifiers, and allelic information, note header naming format is important). For example: SNP (Variant ID e.g., rs number), A1 (Allele 1, interpreted as reference allele for signed sumstat), A2 (Allele 2, interpreted as non-reference allele for signed sumstat), Frq (Allele frequency), BETA or [linear/logistic] regression coefficient (0 --> no effect; above 0 --> A1 is trait/risk increasing), P (p-Value), N (Sample size). In addition, a reference population needs to be selected from the drop down menu.',
      "<u>Reference population</u> - One 1000 Genomes Project/Genome Aggregation Database (gnomAD) sub-population is required for heritability analysis or genetic correlation.",
    ],
    output: [
      "<u>For LD Score calculation</u> - A summary of LD Scores, the MAF/LD Score Correlation Matrix, full LD Scores file, as well as the option to download input data, in addition to a code prompt output summary.",
      "<u>For heritability analysis</u> - Total Observed scale heritability, Lambda GC, Mean Chi^2, Intercept and LDSC Ratio, as well as a code prompt output summary.",
      "<u>For genetic correlation</u> - tables with heritability of phenotype 1, heritability of phenotype 2, Genetic Covariance, Genetic Correlation and a Summary of Genetic Correlation Results, as well as a code prompt output summary.",
    ],
  },
  {
    id: "SNPchip",
    name: "SNPchip",
    description: "Find commercial genotyping platforms for variants.",
    input: [
      "<u>List of RS numbers</u> - this can either be entered one per line in the text entry box or uploaded as a file that contains a list of RS numbers in the first column. A maximum of 5,000 variant RS numbers are permitted. All input variants do not need to be on the same chromosome. The text entry field is automatically filled with the contents of the uploaded file.",
      "<u>Genotyping Arrays </u> - selected commercial genotyping arrays from the drop down list. At least one array must be selected, but more than one may be selected as input.",
    ],
    output: [
      '<u>Array Table</u> - output table of variant rows and array columns. The presence of an "X" designates the variant is present on the respective commercial genotyping array. Variants are ordered by genomic location. External links lead to the variant RS number in <a href="#dbSNP">dbSNP</a> and coordinates in the <a href="https://genome.ucsc.edu/cgi-bin/hgGateway" target="_blank">UCSC Genome Browser</a>',
      "<u>Download Chip Details</u> - download a file with information on all variants and commercial genotyping array membership.",
    ],
  },
  {
    id: "SNPclip",
    name: "SNPclip",
    description: "Prune a list of variants for linkage disequilibirum.",
    input: [
      "<u>List of RS numbers</u> - this can either be entered one per line in the text entry box or uploaded as a file that contains a list of RS numbers in the first column. A maximum of 5,000 variant RS numbers are permitted. All input variants must be on the same chromosome and match a bi-allelic variant. The text entry field is automatically filled with the contents of the uploaded file.",
      "<u>Reference population(s)</u> - selected from the drop down menu. At least one 1000 Genomes Project sub-population is required, but more than one may be selected.",
      "<u>R<sup>2</sup> threshold </u> - set R<sup>2</sup> threshold for LD pruning. One of each pair of variants with a R<sup>2</sup> greater than the threshold is removed. Value needs to be in the range 0 to 1. Default value is 0.1.",
      "<u>MAF threshold</u> - set MAF threshold for LD pruning. Variants with a MAF less than or equal to the threshold are removed. Value needs to be in the range 0 to 1. Default value is 0.01.",
    ],
    output: [
      "<u>LD Thinned Variant List</u> - a list of LD pruned variants based on the specified SNPclip parameters. Each variant in the list is a clickable link that brings up a detailed table showing other variants that are in linkage disequilibirum with the variant. Variants are ordered by input order, so to force a variant to be in the LD thinned list it should be at the top of the input list.",
      '<u>Details Tables</u> - output table that appears when a variant in the thinned variant list is clicked. Details are provided on genomic position, alleles, and why the variant was included or excluded from the thinned variant list. External links lead to the variant RS number in <a href="#dbSNP">dbSNP</a> and coordinates in the <a href="https://genome.ucsc.edu/cgi-bin/hgGateway" target="_blank">UCSC Genome Browser</a>',
      '<u>Variants with Warnings</u> - output table that appears when a variant produces a warning in SNPclip. Common reasons for a variant to be on the warning list include a variant with an MAF below the MAF threshold, a query that is not a RS number, and a RS number not found in the 1000G reference VCF file. Details are provided on genomic position, alleles, and why the variant was included or excluded from the thinned variant list. External links lead to the variant RS number in <a href="#dbSNP">dbSNP</a> and coordinates in the <a href="https://genome.ucsc.edu/cgi-bin/hgGateway" target="_blank">UCSC Genome Browser</a>',
      "<u>Download Thinned Variant List</u> - download a text file that lists all thinned variant RS numbers, one per line.",
      "<u>Download Thinned Variant List with Details</u> - download a text file that lists all query variant RS numbers, genomic locations, alleles and details of whether the variant was kept or removed.",
    ],
  },
];
