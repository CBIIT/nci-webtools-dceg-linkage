// src/app/documentation/page.tsx
"use client";
import React from "react";

export default function DocumentationPage() {
  return (
    <div className="container mt-4">
      <div style={{ textAlign: "center" }}>
        <h2>
          <img
            src="/images/LDlink_logo_small_clear.png"
            alt="LDlink"
            style={{ verticalAlign: "bottom" }}
          />{" "}
          Documentation
        </h2>
      </div>

      <p>
        LDlink is designed to be an intuitive and simple tool for investigating patterns of linkage disequilibrium across a variety of ancestral population groups...
        <a
          href="https://github.com/CBIIT/nci-webtools-dceg-linkage"
          target="_blank"
          rel="noopener noreferrer"
        >
          GitHub
        </a>
        .
      </p>

      <ul>
        <li><a href="#Understanding_Linkage_Disequilibrium">Understanding Linkage Disequilibrium</a></li>
        <ul>
          <li><a href="#linkage_equilibrium">Linkage Equilibrium</a></li>
          <li><a href="#linkage_disequilibrium">Linkage Disequilibrium</a></li>
          <li><a href="#haplotype">Haplotype</a></li>
        </ul>
        <li><a href="#Data_Sources">Data Sources</a></li>
        <ul>
          <li><a href="#dbSNP">dbSNP</a></li>
          <li><a href="#1000_Genomes_Project">1000 Genomes Project</a></li>
          <li><a href="#ucsc_refgene">UCSC RefSeq</a></li>
          <li><a href="#regulomedb">RegulomeDB</a></li>
          <li><a href="#recomb">Genetic Map</a></li>
          <li><a href="#gtex">GTEx Portal</a></li>
          <li><a href="#gwas_catalog">GWAS Catalog</a></li>
          <li><a href="#forgedb">FORGEdb</a></li>
        </ul>
        <li><a href="#Calculations">Calculations</a></li>
        <ul>
          <li><a href="#D_prime">D prime</a></li>
          <li><a href="#R_squared">R squared</a></li>
          <li><a href="#Goodness_of_Fit">Goodness of Fit</a></li>
        </ul>
        <li><a href="#Modules">Modules</a></li>
        <ul>
          <li><a href="#LDassoc">LDassoc</a></li>
          <li><a href="#LDexpress">LDexpress</a></li>
          <li><a href="#LDhap">LDhap</a></li>
          <li><a href="#LDmatrix">LDmatrix</a></li>
          <li><a href="#LDpair">LDpair</a></li>
          <li><a href="#LDpop">LDpop</a></li>
          <li><a href="#LDproxy">LDproxy</a></li>
          <li><a href="#LDtrait">LDtrait</a></li>
          <li><a href="#LDscore">LDscore</a></li>
          <li><a href="#SNPchip">SNPchip</a></li>
          <li><a href="#SNPclip">SNPclip</a></li>
        </ul>
        <li><a href="#FAQ">Frequently Asked Questions</a></li>
      </ul>

      <div>
        <p> <strong><a id="Understanding_Linkage_Disequilibrium"></a>Understanding
			Linkage Disequilibrium</strong></p>
        <p><a id="linkage_equilibrium"></a>What is
            linkage disequilibrium? Perhaps it is best to start
            with linkage equilibrium. Linkage equilibrium exists when alleles from
            two different genetic variants occur independently of each
            other. The inheritance of such variants follows
            probabilistic patterns governed by population allele frequencies. The
            vast majority of genetic variants on a chromosome are in linkage
            equilibrium. Variants in linkage equilibrium are not considered
            linked.</p>
        <p><a id="linkage_disequilibrium"></a>Linkage
		disequilibrium is present when alleles from two nearby
		genetic variants commonly occur together in a non-random, linked fashion. This
		linked mode of inheritance results from genetic variants in close
		proximity being less likely to be separated by a recombination event
		and thus alleles of the variants are more commonly inherited together
		than expected. Alleles of variants in linkage disequilibrium are
		correlated; with the degree of correlation generally greater in
		magnitude the closer the variants are in physical distance. Measures of
		linkage disequilibrium include <a href="#D_prime">D prime
			(D&apos;)</a> and <a href="#R_squared">R squared (R<sup>2</sup>)</a>.</p>
        <p><a id="haplotype"></a>A haplotype is a
            cluster of genetic variants that are
            inherited together. Humans are diploid; having maternal and paternal
            copies of each autosomal chromosome. Each chromosomal copy is organized
            into segments of high linkage disequilibrium, called haplotype
            &quot;blocks&quot;. Due to unique population histories and differences in variant
            allele frequencies, haplotype structure tends to be population
            specific. Although haplotypes are essential for calculating measures of
            linkage disequilibrium, haplotypes are seldom directly observed.
            Statistical chromosome phasing techniques are often necessary to infer
            individual haplotypes.<strong> </strong>
        </p>       

      </div>
      <div>
        <p> <strong><a name="Data_Sources"></a>Data
			Sources</strong>
	</p>
	<p>
		<strong><a name="dbSNP"></a><a href="https://www.ncbi.nlm.nih.gov/snp/" target="_blank">dbSNP</a></strong> (source: <a href="https://ftp.ncbi.nih.gov/snp/" target="_blank">GRCh37 and GRCh38</a>) - 
		To investigate patterns of linkage disequilibrium, LDlink
		focuses on two main class of genetic variation: single
		nucleotide polymorphisms (SNPs) and insertions/deletions (indels). Every module of LDlink requires the
		entry of at least one variant as identified by a RefSNP number (RS
		number) or genomic position (chr#:position). RS numbers have been assigned by dbSNP
		and are well-curated identifiers that follow the format "rs" followed by 1 to 8 numbers. The
		current implementation of LDlink references dbSNP and only
		accepts input for bi-allelic variants.
	</p>
	<p>
		<strong><a name="1000_Genomes_Project"></a><a href="https://www.internationalgenome.org/" target="_blank">1000 Genomes Project</a></strong> (source: <a href="http://ftp.1000genomes.ebi.ac.uk/vol1/ftp/release/20130502/" target="_blank">GRCh37</a>, <a href="http://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1000_genomes_project/release/20190312_biallelic_SNV_and_INDEL/" target="_blank">GRCh38</a>, and <a href="http://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1000G_2504_high_coverage/working/20201028_3202_phased/" target="_blank">GRCh38 High Coverage</a>) - 
		Publicly available reference haplotypes from the 1000 Genomes Project are used by LDlink to calculate
		population-specific measures of linkage disequilibrium. Haplotypes are
		available for continental populations (ex: European, African, and
		Admixed American) and sub-populations (ex: Finnish, Gambian, and
		Peruvian). All LDlink modules require the selection of at least one
		1000 Genomes Project sub-population, but several sub-populations can be
		selected simultaneously. Available haplotypes vary by sub-population
		based on sample size.
	</p>
    <p>
		<strong><a name="ucsc_refgene"></a><a href="https://genome.ucsc.edu/cgi-bin/hgTables" target="_blank">UCSC RefSeq</a></strong> (source: <a href="https://genome.ucsc.edu/cgi-bin/hgTables?hgsid=1196412861_bzHfOz59YBcRs96UaRLkQjHBova0&clade=mammal&org=Human&db=hg19&hgta_group=genes&hgta_track=refSeqComposite&hgta_table=0&hgta_regionType=genome&position=chrX%3A15%2C578%2C261-15%2C621%2C068&hgta_outputType=primaryTable&hgta_outFileName=" target="_blank">GRCh37</a> and <a href="https://genome.ucsc.edu/cgi-bin/hgTables?hgsid=1196412861_bzHfOz59YBcRs96UaRLkQjHBova0&clade=mammal&org=&db=hg38&hgta_group=genes&hgta_track=refSeqComposite&hgta_table=ncbiRefSeq&hgta_regionType=genome&position=&hgta_outputType=primaryTable&hgta_outFileName=" target="_blank">GRCh38</a>) - 
		Publicly available gene transcripts from the UCSC Table Browser are used by LDlink's <a href="#LDassoc">LDassoc</a>, <a href="#LDmatrix">LDmatrix</a>, and <a href="#LDproxy">LDproxy</a> modules to display genes within the genomic window of interest.
	</p>
	<p>
		<strong><a name="regulomedb"></a><a href="https://regulomedb.org/" target="_blank">RegulomeDB</a></strong> (source: <a href="https://www.encodeproject.org/files/ENCFF297XMQ/@@download/ENCFF297XMQ.tsv" target="_blank">GRCh37</a>) - 
		Publicly available scores from RegulomeDB are used by LDlink's <a href="#LDassoc">LDassoc</a> and <a href="#LDproxy">LDproxy</a> modules to rank available datatypes for a single coordinate.
		GRCh38 support is added via <a href="https://genome.ucsc.edu/cgi-bin/hgLiftOver" target="_blank">liftOver</a>.
	</p>
    <p>
		<strong><a name="recomb"></a><a href="https://mathgen.stats.ox.ac.uk/impute/1000GP_Phase3.html" target="_blank">Genetic Map</a></strong> (source: <a href="https://mathgen.stats.ox.ac.uk/impute/1000GP_Phase3.html" target="_blank">GRCh37</a>) - 
		Publicly available combined recombination rates (cM/Mb) from the 1000 Genomes Project are used by LDlink's <a href="#LDassoc">LDassoc</a> and <a href="#LDproxy">LDproxy</a> modules to show recombination at specific coordinates.
		GRCh38 support is added via <a href="https://genome.ucsc.edu/cgi-bin/hgLiftOver" target="_blank">liftOver</a>.
	</p>
	<p>
		<strong><a name="gtex"></a><a href="https://www.gtexportal.org/home/" target="_blank">GTEx Portal</a></strong> (source: <a href="https://storage.googleapis.com/gtex_analysis_v8/single_tissue_qtl_data/GTEx_Analysis_v8_eQTL.tar" target="_blank">GRCh38</a>) - 
		Publicly available single-tissue cis-QTL data from the GTEx Portal is used by LDlink's <a href="#LDexpress">LDexpress</a> module to show significant variant-gene associations in multiple tissue types.
		GRCh37 support is added via <a href="https://storage.googleapis.com/gtex_analysis_v8/reference/GTEx_Analysis_2017-06-05_v8_WholeGenomeSeq_838Indiv_Analysis_Freeze.lookup_table.txt.gz" target="_blank">GTEx lookup table</a>.
	</p>
    <p>
		<strong><a name="gwas_catalog"></a><a href="https://www.ebi.ac.uk/gwas/home" target="_blank">GWAS Catalog</a></strong> (source: <a href="https://www.ebi.ac.uk/gwas/api/search/downloads/alternative" target="_blank">GRCh38</a>) - 
		Publicly available NHGRI-EBI Catalog of human genome-wide association studies from GWAS Catalog is used by LDlink's <a href="#LDtrait">LDtrait</a> module to search if variants have previously been associated with a trait or disease.
		GRCh37 support is added via <a href="#dbSNP">dbSNP</a>.
    </p>
	<p>
		<strong><a name="forgedb"></a><a href="https://forgedb.cancer.gov/" target="_blank">FORGEdb</a></strong> (source: <a href="https://forgedb.cancer.gov/"
			target="_blank">FORGEdb</a>) -
		Publicly available scores from FORGEdb are used by LDlink's LDassoc and LDproxy modules to rank putative functionality
		for a single variant by RSID.
	</p>
      </div>
      <div>
        <p> <strong><a name="Calculations"></a>Calculations</strong>
	</p>
	<p>
		LDlink modules report the following measures of linkage
		disequilibrium: <a href="#D_prime">D prime</a>, <a href="#R_squared">R squared</a>, and <a href="#Goodness_of_Fit">goodness-of-fit</a>
		statistics. Below is a brief description of each measure.
	</p>
	<p> <strong><a name="D_prime"></a>D
			prime (D')</strong> - an indicator of
		allelic segregation for two genetic variants. D' values range from 0 to
		1 with higher values indicating tight linkage of alleles. A D' value of
		0 indicates no linkage of alleles. A D' value of 1 indicates at least
		one expected haplotype combination is not observed.
	</p>
	<p> <strong><a name="R_squared"></a>R
			squared (R<sup>2</sup>) </strong>
		- a measure of correlation of alleles for two genetic variants. R<sup>2</sup>
		values range from 0 to 1 with higher values indicating a higher degree
		of correlation. An R<sup>2</sup> value of 0 indicates
		alleles are independent, whereas an R<sup>2</sup> value of
		1 indicates an allele of one variant perfectly predicts an allele of
		another variant. R<sup>2</sup> is sensitive to allele
		frequency.
	</p>
    <p> <strong><a name="Goodness_of_Fit"></a>Goodness
			of Fit (&#935;<sup>2</sup> and
			p-value) </strong> - statistical test testing whether observed
		haplotype counts follow frequencies expected from variant allele
		frequencies. High chi-square statistics and low p-values are evidence
		that haplotype counts deviate from expected values and suggest linkage
		disequilibrium may be present.
	</p>
      </div>

      <div>
        <p> <strong><a name="Modules"></a>Modules</strong>
	</p>
	<p>LDlink consists of eleven modules: <a href="#LDassoc">LDassoc</a>, <a href="#LDexpress">LDexpress</a>, <a href="#LDhap">LDhap</a>,
		<a href="#LDmatrix">LDmatrix</a>, <a href="#LDpair">LDpair</a>, <a href="#LDpop">LDpop</a>, 
		<a href="#LDproxy">LDproxy</a>, <a href="#LDtrait">LDtrait</a>, <a href="#LDscore">LDscore</a>, <a href="#SNPchip">SNPchip</a>,
		and <a href="#SNPclip">SNPclip</a>. 
		Choose between GRCh37 (hg19), GRCh38 (hg38), and GRCh38 High Coverage (hg38) 1000 Genome Project datasets with the Genome Build (1000G) dropdown menu on the top left.
		Each module can be accessed by clicking on LD Tools dropdown at
		the top of all LDlink pages. Below is a description of each module, the
		required user input, and an explanation of the returned output.</p>
      </div>

      <div>
        <p style={{ marginLeft: "40px" }} id="LDassoc">
            <strong>
            <span style={{ textDecoration: "underline" }}>LDassoc</span>
            </strong>{" "}
            - Interactively visualize association p-value results and linkage disequilibrium patterns for a genomic region of
            interest. Based on the file size, number of variants and selected query populations, this module may take some time
            to run.
        </p>
        <p style={{ marginLeft: "80px" }}>
            <strong>Input:</strong>
        </p>
        <p style={{ marginLeft: "120px" }}>
            <u>Association data file</u> - upload a space or tab delimited file containing chromosome, position and p-value for
            each variant. A file header, while not required, will be useful when selecting input columns. Once the file is
            uploaded the user needs to specify which columns are the respective chromosome, position, and association p-values.
            Uploaded files will be stored on our secure server for use during LDassoc sessions and will be deleted after 4
            hours.
        </p>
        <p style={{ marginLeft: "120px" }}>
            <u>Select region</u> - choices are <i>Gene</i>, <i>Region</i>, or <i>Variant</i>. <i>Gene</i>
            requires a RefSeq gene name and base pair window and allows for an optional index variant. <i>Region</i> requires
            genomic start and end coordinates and allows for an optional index variant. <i>Variant</i> requires an index variant and
            allows for an optional base pair window (500,000bp is the default). The index variant will be plotted in blue and is used to calculate all
            pairwise LD statistics. If not required, LDassoc will designate the variant with the lowest p-value as the index variant,
            unless otherwise specified.
	</p>
        </div>


      {/* Add the rest of the document content here similarly with <h3>, <p>, etc. */}
    </div>
  );
}
