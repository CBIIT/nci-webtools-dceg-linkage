"use client";
import React from "react";
import { Container } from "react-bootstrap";
import Image from "next/image";

export default function HelpPage() {
  return (
    <Container className="py-4 help-page">
      <div className="text-center">
        <h1 className="h2">
          <Image
            src="/images/LDlink_logo_small_clear.png"
            alt="LDlink"
            style={{ verticalAlign: "bottom" }}
            width={91}
            height={36}
          />{' '}
          Documentation
        </h1>
      </div>
      <div className="pt-2">
        <p>
          LDlink is designed to be an intuitive and simple tool for investigating patterns of linkage disequilibrium across a variety of ancestral population groups. This help documentation page gives detailed description of the metrics calculated by LDlink modules and aids users in understanding all aspects of the required input and returned output. This application&apos;s source code can be viewed on{' '}
          <a href="https://github.com/CBIIT/nci-webtools-dceg-linkage" target="_blank" rel="noopener noreferrer">GitHub</a>.
          The documentation is divided into the following sections:
        </p>
        {/* Navigation section replaced with paragraph-based links for clarity and to match the original HTML style. */}
        <p style={{ marginLeft: 40 }}><a href="#Understanding_Linkage_Disequilibrium"><strong>Understanding Linkage Disequilibrium</strong></a></p>
        <p style={{ marginLeft: 80 }}><a href="#linkage_equilibrium"><strong>Linkage Equilibrium</strong></a></p>
        <p style={{ marginLeft: 80 }}><a href="#linkage_disequilibrium"><strong>Linkage Disequilibrium</strong></a></p>
        <p style={{ marginLeft: 80 }}><a href="#haplotype"><strong>Haplotype</strong></a></p>
        <p style={{ marginLeft: 40 }}><a href="#Data_Sources"><strong>Data Sources</strong></a></p>
        <p style={{ marginLeft: 80 }}><a href="#dbSNP"><strong>dbSNP</strong></a></p>
        <p style={{ marginLeft: 80 }}><a href="#1000_Genomes_Project"><strong>1000 Genomes Project</strong></a></p>
        <p style={{ marginLeft: 80 }}><a href="#ucsc_refgene"><strong>UCSC RefSeq</strong></a></p>
        <p style={{ marginLeft: 80 }}><a href="#regulomedb"><strong>RegulomeDB</strong></a></p>
        <p style={{ marginLeft: 80 }}><a href="#recomb"><strong>Genetic Map</strong></a></p>
        <p style={{ marginLeft: 80 }}><a href="#gtex"><strong>GTEx Portal</strong></a></p>
        <p style={{ marginLeft: 80 }}><a href="#gwas_catalog"><strong>GWAS Catalog</strong></a></p>
        <p style={{ marginLeft: 80 }}><a href="#forgedb"><strong>FORGEdb</strong></a></p>
        <p style={{ marginLeft: 40 }}><a href="#Calculations"><strong>Calculations</strong></a></p>
        <p style={{ marginLeft: 80 }}><a href="#D_prime"><strong>D prime</strong></a></p>
        <p style={{ marginLeft: 80 }}><a href="#R_squared"><strong>R squared</strong></a></p>
        <p style={{ marginLeft: 80 }}><a href="#Goodness_of_Fit"><strong>Goodness of Fit</strong></a></p>
        <p style={{ marginLeft: 40 }}><a href="#Modules"><strong>Modules</strong></a></p>
        <p style={{ marginLeft: 80 }}><a href="#LDassoc"><strong>LDassoc</strong></a></p>
        <p style={{ marginLeft: 80 }}><a href="#LDexpress"><strong>LDexpress</strong></a></p>
        <p style={{ marginLeft: 80 }}><a href="#LDhap"><strong>LDhap</strong></a></p>
        <p style={{ marginLeft: 80 }}><a href="#LDmatrix"><strong>LDmatrix</strong></a></p>
        <p style={{ marginLeft: 80 }}><a href="#LDpair"><strong>LDpair</strong></a></p>
        <p style={{ marginLeft: 80 }}><a href="#LDpop"><strong>LDpop</strong></a></p>
        <p style={{ marginLeft: 80 }}><a href="#LDproxy"><strong>LDproxy</strong></a></p>
        <p style={{ marginLeft: 80 }}><a href="#LDtrait"><strong>LDtrait</strong></a></p>
        <p style={{ marginLeft: 80 }}><a href="#LDscore"><strong>LDscore</strong></a></p>
        <p style={{ marginLeft: 80 }}><a href="#SNPchip"><strong>SNPchip</strong></a></p>
        <p style={{ marginLeft: 80 }}><a href="#SNPclip"><strong>SNPclip</strong></a></p>
        <p style={{ marginLeft: 40 }}><a href="#FAQ"><strong>Frequently Asked Questions</strong></a></p>
        <hr />
        <section id="Understanding_Linkage_Disequilibrium">
          <h2 className="h3">Understanding Linkage Disequilibrium</h2>
          <p><a id="linkage_equilibrium"></a><strong>Linkage Equilibrium</strong> exists when alleles from two different genetic variants occur independently of each other. The inheritance of such variants follows probabilistic patterns governed by population allele frequencies. The vast majority of genetic variants on a chromosome are in linkage equilibrium. Variants in linkage equilibrium are not considered linked.</p>
          <p><a id="linkage_disequilibrium"></a><strong>Linkage Disequilibrium</strong> is present when alleles from two nearby genetic variants commonly occur together in a non-random, linked fashion. This linked mode of inheritance results from genetic variants in close proximity being less likely to be separated by a recombination event and thus alleles of the variants are more commonly inherited together than expected. Alleles of variants in linkage disequilibrium are correlated; with the degree of correlation generally greater in magnitude the closer the variants are in physical distance. Measures of linkage disequilibrium include <a href="#D_prime">D prime (D&apos;)</a> and <a href="#R_squared">R squared (R<sup>2</sup>)</a>.</p>
          <p><a id="haplotype"></a><strong>Haplotype</strong> is a cluster of genetic variants that are inherited together. Humans are diploid; having maternal and paternal copies of each autosomal chromosome. Each chromosomal copy is organized into segments of high linkage disequilibrium, called haplotype &quot;blocks&quot;. Due to unique population histories and differences in variant allele frequencies, haplotype structure tends to be population specific. Although haplotypes are essential for calculating measures of linkage disequilibrium, haplotypes are seldom directly observed. Statistical chromosome phasing techniques are often necessary to infer individual haplotypes.</p>
        </section>
        <hr />
        <section id="Data_Sources">
          <h3>Data Sources</h3>
          <p><a id="dbSNP"></a><strong><a href="https://www.ncbi.nlm.nih.gov/snp/" target="_blank" rel="noopener noreferrer">dbSNP</a></strong> (source: <a href="https://ftp.ncbi.nih.gov/snp/" target="_blank" rel="noopener noreferrer">GRCh37 and GRCh38</a>) - To investigate patterns of linkage disequilibrium, LDlink focuses on two main class of genetic variation: single nucleotide polymorphisms (SNPs) and insertions/deletions (indels). Every module of LDlink requires the entry of at least one variant as identified by a RefSNP number (RS number) or genomic position (chr#:position). RS numbers have been assigned by dbSNP and are well-curated identifiers that follow the format &quot;rs&quot; followed by 1 to 8 numbers. The current implementation of LDlink references dbSNP and only accepts input for bi-allelic variants.</p>
          <p><a id="1000_Genomes_Project"></a><strong><a href="https://www.internationalgenome.org/" target="_blank" rel="noopener noreferrer">1000 Genomes Project</a></strong> (source: <a href="http://ftp.1000genomes.ebi.ac.uk/vol1/ftp/release/20130502/" target="_blank" rel="noopener noreferrer">GRCh37</a>, <a href="http://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1000_genomes_project/release/20190312_biallelic_SNV_and_INDEL/" target="_blank" rel="noopener noreferrer">GRCh38</a>, and <a href="http://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1000G_2504_high_coverage/working/20201028_3202_phased/" target="_blank" rel="noopener noreferrer">GRCh38 High Coverage</a>) - Publicly available reference haplotypes from the 1000 Genomes Project are used by LDlink to calculate population-specific measures of linkage disequilibrium. Haplotypes are available for continental populations (ex: European, African, and Admixed American) and sub-populations (ex: Finnish, Gambian, and Peruvian). All LDlink modules require the selection of at least one 1000 Genomes Project sub-population, but several sub-populations can be selected simultaneously. Available haplotypes vary by sub-population based on sample size.</p>
          <p><a id="ucsc_refgene"></a><strong><a href="https://genome.ucsc.edu/cgi-bin/hgTables" target="_blank" rel="noopener noreferrer">UCSC RefSeq</a></strong> (source: <a href="https://genome.ucsc.edu/cgi-bin/hgTables?hgsid=1196412861_bzHfOz59YBcRs96UaRLkQjHBova0&clade=mammal&org=Human&db=hg19&hgta_group=genes&hgta_track=refSeqComposite&hgta_table=0&hgta_regionType=genome&position=chrX%3A15%2C578%2C261-15%2C621%2C068&hgta_outputType=primaryTable&hgta_outFileName=" target="_blank" rel="noopener noreferrer">GRCh37</a> and <a href="https://genome.ucsc.edu/cgi-bin/hgTables?hgsid=1196412861_bzHfOz59YBcRs96UaRLkQjHBova0&clade=mammal&org=&db=hg38&hgta_group=genes&hgta_track=refSeqComposite&hgta_table=ncbiRefSeq&hgta_regionType=genome&position=&hgta_outputType=primaryTable&hgta_outFileName=" target="_blank" rel="noopener noreferrer">GRCh38</a>) - Publicly available gene transcripts from the UCSC Table Browser are used by LDlink&apos;s <a href="#LDassoc">LDassoc</a>, <a href="#LDmatrix">LDmatrix</a>, and <a href="#LDproxy">LDproxy</a> modules to display genes within the genomic window of interest.</p>
          <p><a id="regulomedb"></a><strong><a href="https://regulomedb.org/" target="_blank" rel="noopener noreferrer">RegulomeDB</a></strong> (source: <a href="https://www.encodeproject.org/files/ENCFF297XMQ/@@download/ENCFF297XMQ.tsv" target="_blank" rel="noopener noreferrer">GRCh37</a>) - Publicly available scores from RegulomeDB are used by LDlink&apos;s <a href="#LDassoc">LDassoc</a> and <a href="#LDproxy">LDproxy</a> modules to rank available datatypes for a single coordinate. GRCh38 support is added via <a href="https://genome.ucsc.edu/cgi-bin/hgLiftOver" target="_blank" rel="noopener noreferrer">liftOver</a>.</p>
          <p><a id="recomb"></a><strong><a href="https://mathgen.stats.ox.ac.uk/impute/1000GP_Phase3.html" target="_blank" rel="noopener noreferrer">Genetic Map</a></strong> (source: <a href="https://mathgen.stats.ox.ac.uk/impute/1000GP_Phase3.html" target="_blank" rel="noopener noreferrer">GRCh37</a>) - Publicly available combined recombination rates (cM/Mb) from the 1000 Genomes Project are used by LDlink&apos;s <a href="#LDassoc">LDassoc</a> and <a href="#LDproxy">LDproxy</a> modules to show recombination at specific coordinates. GRCh38 support is added via <a href="https://genome.ucsc.edu/cgi-bin/hgLiftOver" target="_blank" rel="noopener noreferrer">liftOver</a>.</p>
          <p><a id="gtex"></a><strong><a href="https://www.gtexportal.org/home/" target="_blank" rel="noopener noreferrer">GTEx Portal</a></strong> (source: <a href="https://storage.googleapis.com/gtex_analysis_v8/single_tissue_qtl_data/GTEx_Analysis_v8_eQTL.tar" target="_blank" rel="noopener noreferrer">GRCh38</a>) - Publicly available single-tissue cis-QTL data from the GTEx Portal is used by LDlink&apos;s <a href="#LDexpress">LDexpress</a> module to show significant variant-gene associations in multiple tissue types. GRCh37 support is added via <a href="https://storage.googleapis.com/gtex_analysis_v8/reference/GTEx_Analysis_2017-06-05_v8_WholeGenomeSeq_838Indiv_Analysis_Freeze.lookup_table.txt.gz" target="_blank" rel="noopener noreferrer">GTEx lookup table</a>.</p>
          <p><a id="gwas_catalog"></a><strong><a href="https://www.ebi.ac.uk/gwas/home" target="_blank" rel="noopener noreferrer">GWAS Catalog</a></strong> (source: <a href="https://www.ebi.ac.uk/gwas/api/search/downloads/alternative" target="_blank" rel="noopener noreferrer">GRCh38</a>) - Publicly available NHGRI-EBI Catalog of human genome-wide association studies from GWAS Catalog is used by LDlink&apos;s <a href="#LDtrait">LDtrait</a> module to search if variants have previously been associated with a trait or disease. GRCh37 support is added via <a href="#dbSNP">dbSNP</a>.</p>
          <p><a id="forgedb"></a><strong><a href="https://forgedb.cancer.gov/" target="_blank" rel="noopener noreferrer">FORGEdb</a></strong> (source: <a href="https://forgedb.cancer.gov/" target="_blank" rel="noopener noreferrer">FORGEdb</a>) - Publicly available scores from FORGEdb are used by LDlink&apos;s LDassoc and LDproxy modules to rank putative functionality for a single variant by RSID.</p>
        </section>
        <hr />
        <section id="Calculations">
          <h3>Calculations</h3>
          <p>
            LDlink modules report the following measures of linkage disequilibrium: <a href="#D_prime">D prime</a>, <a href="#R_squared">R squared</a>, and <a href="#Goodness_of_Fit">goodness-of-fit</a> statistics. Below is a brief description of each measure.
          </p>
          <p><a id="D_prime"></a><strong>D prime (D&apos;)</strong> - an indicator of allelic segregation for two genetic variants. D&apos; values range from 0 to 1 with higher values indicating tight linkage of alleles. A D&apos; value of 0 indicates no linkage of alleles. A D&apos; value of 1 indicates at least one expected haplotype combination is not observed.</p>
          <p><a id="R_squared"></a><strong>R squared (R<sup>2</sup>)</strong> - a measure of correlation of alleles for two genetic variants. R<sup>2</sup> values range from 0 to 1 with higher values indicating a higher degree of correlation. An R<sup>2</sup> value of 0 indicates alleles are independent, whereas an R<sup>2</sup> value of 1 indicates an allele of one variant perfectly predicts an allele of another variant. R<sup>2</sup> is sensitive to allele frequency.</p>
          <p><a id="Goodness_of_Fit"></a><strong>Goodness of Fit (&#935;<sup>2</sup> and p-value)</strong> - statistical test testing whether observed haplotype counts follow frequencies expected from variant allele frequencies. High chi-square statistics and low p-values are evidence that haplotype counts deviate from expected values and suggest linkage disequilibrium may be present.</p>
        </section>
        <hr />
        <section id="Modules">
          <h3>Modules</h3>
          <p>LDlink consists of eleven modules: <a href="#LDassoc">LDassoc</a>, <a href="#LDexpress">LDexpress</a>, <a href="#LDhap">LDhap</a>, <a href="#LDmatrix">LDmatrix</a>, <a href="#LDpair">LDpair</a>, <a href="#LDpop">LDpop</a>, <a href="#LDproxy">LDproxy</a>, <a href="#LDtrait">LDtrait</a>, <a href="#LDscore">LDscore</a>, <a href="#SNPchip">SNPchip</a>, and <a href="#SNPclip">SNPclip</a>. Choose between GRCh37 (hg19), GRCh38 (hg38), and GRCh38 High Coverage (hg38) 1000 Genome Project datasets with the Genome Build (1000G) dropdown menu on the top left. Each module can be accessed by clicking on LD Tools dropdown at the top of all LDlink pages. Below is a description of each module, the required user input, and an explanation of the returned output.</p>
          <div style={{ marginLeft: 40 }}>
            <section id="LDassoc">
              <h4 style={{ textDecoration: "underline" }}>LDassoc</h4>
              <p>Interactively visualize association p-value results and linkage disequilibrium patterns for a genomic region of interest. Based on the file size, number of variants and selected query populations, this module may take some time to run.</p>
              <p><strong>Input:</strong></p>
              <ul>
                <li><u>Association data file</u> - upload a space or tab delimited file containing chromosome, position and p-value for each variant. A file header, while not required, will be useful when selecting input columns. Once the file is uploaded the user needs to specify which columns are the respective chromosome, position, and association p-values. Uploaded files will be stored on our secure server for use during LDassoc sessions and will be deleted after 4 hours.</li>
                <li><u>Select region</u> - choices are <i>Gene</i>, <i>Region</i>, or <i>Variant</i>. <i>Gene</i> requires a RefSeq gene name and base pair window and allows for an optional index variant. <i>Region</i> requires genomic start and end coordinates and allows for an optional index variant. <i>Variant</i> requires an index variant and allows for an optional base pair window (500,000bp is the default). The index variant will be plotted in blue and is used to calculate all pairwise LD statistics. If not required, LDassoc will designate the variant with the lowest p-value as the index variant, unless otherwise specified.</li>
                <li><u>Reference population(s)</u> - selected from the drop down menu. At least one 1000 Genomes Project sub-population is required, but more than one may be selected.</li>
                <li><u>LD measure</u> - select if desired output is based on estimated R<sup>2</sup> or D&apos;.</li>
                <li><u>Collapse transcripts</u> - choose to combine gene transcripts with the same name in the gene plot.</li>
                <li><u>RegulomeDB annotation</u> - choose to display RegulomeDB scores in the interactive plot.</li>
              </ul>
              <p><strong>Output:</strong></p>
              <ul>
                <li><u>Interactive plot</u> - interactive plot of index variant and p-values of all bi-allelic variants in the specified plotting region. X axis is the chromosomal coordinates and the Y axis is the -log10 p-value as well as the combined recombination rate. Each point represents a variant and is colored based on D&apos; or R<sup>2</sup>, sized based on minor allele frequency, and labeled based on regulatory potential. Hovering over the point will display detailed information on the index and proxy variants.</li>
                <li><u>UCSC link</u> - external link to the plotted region in the <a href="https://genome.ucsc.edu/cgi-bin/hgGateway" target="_blank" rel="noopener noreferrer">UCSC Genome Browser</a>. This is useful for exploring nearby genes and regulatory elements in the region.</li>
                <li><u>Table of Association Results</u> - by default, the ten variants with the lowest p-values and closest distance to the index variant are displayed. External links lead to the variant RS number in <a href="#dbSNP">dbSNP</a>, coordinates in the UCSC Genome Browser, and regulatory information (if any) in <a href="#regulomedb">RegulomeDB</a>.</li>
                <li><u>Download association data for all variants</u> - download a file with information on all variants within the plotting region.</li>
              </ul>
            </section>
            <section id="LDexpress">
              <h4 style={{ textDecoration: "underline" }}>LDexpress</h4>
              <p>Search if a list of variants (or variants in LD with those variants) is associated with gene expression in tissues of interest. Quantitative trait loci data is downloaded from the <a href="#gtex">GTEx Portal</a> (GTEx v8).</p>
              <p><strong>Input:</strong></p>
              <ul>
                <li><u>List of RS numbers</u> - this can either be entered one per line in the text entry box or uploaded as a file that contains a list of RS numbers in the first column. A maximum of 10 variant RS numbers or chromosomal coordinates (GRCh37) are permitted. All input variants must match a bi-allelic variant. The text entry field is automatically filled if a file of SNPs or genomic coordinates is uploaded.</li>
                <li><u>Reference population(s)</u> - selected from the drop-down menu. At least one 1000 Genomes Project sub-population is required, but more than one may be selected.</li>
                <li><u>R<sup>2</sup>/D&apos; toggle</u> - select if desired output is filtered from a threshold based on estimated R<sup>2</sup> or D&apos;.</li>
                <li><u>R<sup>2</sup>/D&apos; threshold</u> - set threshold for LD filtering. Any variants within -/+ of the specified genomic window and R<sup>2</sup> or D&apos; less than the threshold will be removed. Value needs to be in the range 0 to 1. Default value is 0.1.</li>
                <li><u>Tissue(s)</u> - select the GTEx tissue or tissues of interest for searching for eQTLs.</li>
                <li><u>P-value threshold</u> - define the eQTL significance threshold used for returning query results. Default value is 0.1 which returns all GTEx eQTL associations with P-value less than 0.1. Values can be entered in scientific notation (i.e. &quot;1e-5&quot;).</li>
                <li><u>Window size</u></li>
              </ul>
              <p><strong>Output:</strong></p>
              <ul>
                <li><u>Variants in LD with variants in GTEx QTL</u></li>
                <li><u>Details Tables</u></li>
                <li><u>Variants with Warnings</u></li>
                <li><u>Download GTEx QTL list</u></li>
              </ul>
            </section>
            {/* Repeat for LDhap, LDmatrix, LDpair, LDpop, LDproxy, LDtrait, LDscore, SNPchip, SNPclip as in the HTML */}
          </div>
        </section>
        <hr />
        <section id="FAQ">
          <h3>Frequently Asked Questions</h3>
          <div style={{ marginLeft: 40 }}>
            <p><strong>Why is my variant RS number bringing up an error?</strong></p>
            <p>LDlink modules only accepts...</p>
            <p><strong>What 1000 Genomes population should I select for my LDlink query?</strong></p>
            <p>Choosing the correct...</p>
            <p><strong>What is the estimated running time for an LDproxy query?</strong></p>
            <p>Running time varies greatly...</p>
            <p><strong>How do I save output files?</strong></p>
            <p>Output from a variety of...</p>
            <p><strong>Can I save the plots generated in LDmatrix or LDproxy?</strong></p>
            <p>Yes. Click the Save icon on...</p>
            <p><strong>Does LDproxy display all variants in the window around the query variant?</strong></p>
            <p>For plotting and performance issues, LDproxy plots only include variants with R<sup>2</sup>...</p>
            <p><strong>What is the maximum number of variants LDhap and LDmatrix can accept as input?</strong></p>
            <p>LDhap has a limit of 30 variants...</p>
            <p><strong>Why are the variants in LDhap and LDmatrix output not in the same order as the input?</strong></p>
            <p>Variants in LDhap and LDmatrix...</p>
            <p><strong>Why does my computer seem slow when using LDlink?</strong></p>
            <p>The interactive plots...</p>
            <p><strong>What genome build does LDlink use for genomic coordinates?</strong></p>
            <p>LDlink supports...</p>
            <p><strong>Why do variant coordinates not always match dbSNP or UCSC coordinates?</strong></p>
            <p>All coordinates in LDlink are based on...</p>
            <p><strong>What browsers are supported by LDlink?</strong></p>
            <p>LDlink has been tested to... will not display correctly with Internet Explorer 9 and below or Firefox 35 and below.</p>
          </div>
        </section>
        {/* Continue converting the rest of the help.html content as needed. */}
      </div>
    </Container>
  );
}
