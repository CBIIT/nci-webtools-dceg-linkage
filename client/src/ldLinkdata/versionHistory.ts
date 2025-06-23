export const versionHistory = [
  {
    version: "LDlink 5.7.0 Release (06/11/2025)",
    items: [
      "Added LDscore module",
    ],
  },
  {
    version: "LDlink 5.6.8 Release (06/21/2024)",
    items: [
      "Removed domain change notice",
      "Added USA government official flag banner",
      "Specified numpy version",
    ],
  },
  {
    version: "LDlink 5.6.7 release (02/21/2024)",
    items: [
      "Forge DB Scores update",
    ],
  },
  {
    version: "LDlink 5.6.6 Release (10/20/2023)",
    items: [
      "Updated ForgeDB link to new server",
      "Updated HaploReg link to new version",
      "Added shutdown alert in the header",
      "Fixed the input patterns which should allow only one snp for LDproxy, ldpair and ldpop",
    ],
  },
  {
    version: "LDlink 5.6.5 Release (8/11/2023)",
    items: [
      "Added more citations for LDtrait and LDexpress",
      "Added PUBMEDID(PMID) for LDtrait outputs",
    ],
  },
  {
    version: "LDlink 5.6.4 Release (7/6/2023)",
    items: [
      "Replaced CDN-hosted assets",
    ],
  },
  {
    version: "LDlink 5.6.3 Release (6/1/2023)",
    items: [
      "Fixed LDassoc Upload Issues",
    ],
  },
  {
    version: "LDlink 5.6.2 Release (5/15/2023)",
    items: [
      "Domain URL migrated from ldlink.nci.nih.gov to ldlink.nih.gov",
      "Application logo changed",
    ],
  },
  {
    version: "LDlink 5.6.1 Release (5/3/2023)",
    items: [
      "Fixed download button which can not load file in new tab for Chrome and Firefox",
    ],
  },
  {
    version: "LDlink 5.6.0 Release (4/20/2023)",
    items: [
      "Migrated to serverless architecture for improved performance, reliability, and scalability.",
    ],
  },
  {
    version: "LDlink 5.5.2 Release (3/25/2023)",
    items: [
      "Fix the multiallelic error message for LDpair",
    ],
  },
  {
    version: "LDlink 5.5.1 Release (11/15/2022)",
    items: [
      "Add a link to FORGEdb scoring scheme for LDassoc and LDproxy",
    ],
  },
  {
    version: "LDlink 5.5.0 Release (11/03/2022)",
    items: [
      "Publicly available scores from FORGEdb are used by LDlink's LDassoc and LDproxy and LDMatrix modules.",
      "Added Global Diversity Array_Confluence (I_GDA-C) and Illumina Global Screening version 3_Confluence (I_GSA-v3C) to SNPChip.",
      "Provide a warning when the input on LDtrait can potentially cause a server timeout.",
      "Fixed the broken link for View R2 data in UCGC Genome Browse",
    ],
  },
  {
    version: "LDlink 5.4.2 Release (09/13/2022)",
    items: [
      "Fix the output format for LDpair. It should be text file for api call",
    ],
  },
  {
    version: "LDlink 5.4.1 Release (09/01/2022)",
    items: [
      "Provide more useful error message for LDpair if varient is not in 1000G",
    ],
  },
  {
    version: "LDlink 5.4.0 Release (08/08/2022)",
    items: [
      "Internal code refactoring for performance improvements",
    ],
  },
  {
    version: "LDlink 5.3.3 Release (05/24/2022)",
    items: [
      "Revise SNPclip sort order, use user supplied input format;",
      "Fix LDpair multiallelic query for second SNP input",
    ],
  },
  {
    version: "LDlink 5.3.2 Release (05/06/2022)",
    items: [
      "Fix LDmatrix plotting for unsorted query variants.",
    ],
  },
  {
    version: "LDlink 5.3.1 Release (04/28/2022)",
    items: [
      "Improve ability to catch SNPs missing in 1000G data.",
    ],
  },
  {
    version: "LDlink 5.3 Release (04/05/2022)",
    items: [
      "Add ability to submit batch LDpair inputs to single API requests.",
      "Fix behavior when a SNP's 1000G position does not match dbSNP.",
    ],
  },
  {
    version: "LDlink 5.2 Release (01/03/2022)",
    items: [
      "dbSNP build updated from version 151 to 155.",
      "Add support for GRCh38 genomic coordinates.",
      "Add support for genetic map recombination rates in chromosome X.",
      "Add ability to collapsed gene transcripts in LDmatrix and LDproxy.",
    ],
  },
  {
    version: "LDlink 5.1 Release (05/25/2021)",
    items: [
      "Improved filtering options on LDexpress data table.",
      "Allow scientific notation as input for LDexpress P-value threshold.",
    ],
  },
  {
    version: "LDlink 5.0 Release (11/06/2020)",
    items: [
      "LDexpressreleased for searching variants that are associated with gene expression in multiple tissue types.",
    ],
  },
  {
    version: "LDlink 4.2.0 Release (09/21/2020)",
    items: [
      "Add ability to LDproxy to adjust base pair window size.",
    ],
  },
  {
    version: "LDlink 4.1.0 Release (04/29/2020)",
    items: [
      "Add ability to LDtrait to adjust base pair window size.",
    ],
  },
  {
    version: "LDlink 4.0.3 Release (04/06/2020)",
    items: [
      "Fix population dropdown UI cut short by module container.",
    ],
  },
  {
    version: "LDlink 4.0.2 Release (03/20/2020)",
    items: [
      "Fix P-value and 95% CI columns in LDtrait to reflect GWAS Catalog.",
      "Add timestamp of when LDtrait GWAS Catalog was last updated.",
      "Fix browser forward/back functionality.",
    ],
  },
  {
    version: "LDlink 4.0.1 Release (03/10/2020)",
    items: [
      "Fix SNPchip array labels not displaying correctly.",
    ],
  },
  {
    version: "LDlink 4.0 Release (03/10/2020)",
    items: [
      "LDtraitreleased for searching variants that have been associated with a trait or disease.",
      "Fix correlated allele calculation for LDassoc, LDmatrix, LDpair, and LDproxy.",
      "Combine R2and D' coloring for LDmatrix plots.",
      "Home page redesign.",
    ],
  },
  {
    version: "LDlink 3.9 Release (12/10/2019)",
    items: [
      "Add population details, P-value, and Chi-sq to LDpop export table.",
    ],
  },
  {
    version: "LDlink 3.8 Release (10/31/2019)",
    items: [
      "Upgrade backend from Python 2 to Python 3.",
    ],
  },
  {
    version: "LDlink 3.7.2 Release (08/23/2019)",
    items: [
      "Fix variant inputs by genomic coordinates for chromosomes X and Y.",
    ],
  },
  {
    version: "LDlink 3.7.1 Release (07/30/2019)",
    items: [
      "Fix collapsed gene transcripts in LDassoc.",
    ],
  },
  {
    version: "LDlink 3.7 Release (05/09/2019)",
    items: [
      "Return LDpop API results in tab-delimited format.",
    ],
  },
  {
    version: "LDlink 3.6 Release (04/03/2019)",
    items: [
      "Add ability to make POST requests to LDmatrix with up to 1000 variants.",
      "Restrict concurrent requests to the API.",
    ],
  },
  {
    version: "LDlink 3.5 Release (03/18/2019)",
    items: [
      "LDpopreleased for visualizing LD patterns across 1000G populations.",
    ],
  },
  {
    version: "LDlink 3.4 Release (02/06/2019)",
    items: [
      "Correct dbsnp positions for delins, ins, and del type variants.",
      "Improve query performance from genomic coordinate and rsid inputs.",
    ],
  },
  {
    version: "LDlink 3.3 Release (12/24/2018)",
    items: [
      "LDlink API access now requires registration. Please register using theAPI Accesstab",
      "dbSNP build updated from version 142 to 151.",
      "Genomic coordinates can now be used to query variants for each module.",
      "Improvements have been made to error messages from programmatic access.",
      "Refresh user interface.",
    ],
  },
  {
    version: "LDlink 3.2 Release (08/01/2018)",
    items: [
      "Update Bokeh interactive plotting library to release 0.13.0.",
      "Add ability to export Bokeh plots to high quality images (SVG, PDF, PNG, and JPEG).",
      "Merge gene plot and main plot into one image during export.",
      "Fix errors with SNPclip output when variants are not found in 1000G VCF file.",
    ],
  },
  {
    version: "LDlink 3.0 Release (04/01/2017)",
    items: [
      "LDassocreleased for visualizing association results.",
      "Programmatic Accessof LDlink via terminal commands.",
      "Update Bokeh interactive plotting library to release 0.12.2.",
      "Improve performance of allele matching algorithm.",
      "Better table sorting on absolute value of distance.",
      "Refine exported UCSC data tracks (link at bottom of interactive plots).",
    ],
  },
  {
    version: "LDlink 2.0 Release (03/10/2016)",
    items: [
      "SNPclipreleased for LD pruning a list of variants.",
      "SNPchipreleased for finding variants on commercial genotyping arrays.",
      "Minor tweaks to improve visualization of indel output.",
      "Correct p-value rounding to zero inLDpair.",
      "Fix errors when variants map to the same position in 1000G VCF file",
    ],
  },
  {
    version: "LDlink 1.1 Release (09/30/2015)",
    items: [
      "Indels are now accepted as input in allLDlinkmodules.",
      "LDproxyoutput table now returns all data with options to sort by columns and search output.",
      "LDhaphaplotypes are now color coded by alleles for easier viewing.",
      "LDmatrixnow includes a R2/D' toggle for plotting R2or D' matrices.",
      "Minor tweaks to improve visualization on a variety of device screen sizes.",
    ],
  },
];
