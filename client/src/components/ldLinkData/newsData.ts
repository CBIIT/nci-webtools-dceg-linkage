export const newsData = [
      { title: "LDlink 7.3.0 Release (07/31/2026)",
      items: [
      "Fixed atomic token lock acquisition to prevent concurrent race conditions",
      "Fixed stale-lock cleanup, reliably releasing locks older than timeout",
      "Closed bypass to prevent unauthorized access",
      "Added runtime-based quota with auto-block/unblock to manage usage",
      "Added Redis caching for lock-status checks and runtime counters to reduce database load",  
     ],
    },
      { title: "LDlink 7.1.0 Release (05/08/2026)",
      items: [
      "Added Liability Scale to LDscore's Heritability Analysis and Genetic Correlation",
      "Updated LDpop to support automatic submission",
      "Credit references added to all modules",
      "Python updated to 3.13",
      ],
    },
    { title: "LDlink 7.0.0 Release (03/19/2026)",
      items: [
      "Credit reference added to LDscore",
      "Removed filename restrictions for LDScore input files",
      "Fixed heritability and correlation concurrency issue",
      "Fixed genome build mismatches for LDassoc, LDexpress, LDhap, LDproxy, SNPclip",
      "Added file input validation for LDscore (heritability, correlation and ldscore) module",
      "Updated urllib3 to address security vulnerabilities and boto3 dependency issues",
      "Mongo DB migrated to a new AWS account",
      "Python updated to 3.11",
      ],
    },
    {
    title: "LDlink 6.0.0 Release (12/10/2025)",
    items: [
      `Modernized UI Technology with update from jQuery to Next.js and React's component-based architecture`,
      `Improved site's UI responsiveness, layouts and error/warning messaging`
    ]
  },
  {
    title: "LDlinkR",
    items: [
      `Interested in accessing LDlink's API using R? <br>Check out the new LDlinkR package now available on <a href="https://cran.r-project.org/web/packages/LDlinkR/index.html" title="LDlinkR CRAN" target="_blank">CRAN</a>.`,
    ],
  },
  {
    title: "GWAS Explorer",
    items: [
      `Visualize and interact with genome-wide association study results from PLCO Atlas.<br>Check out <a href="https://exploregwas.cancer.gov/plco-atlas/" title="GWAS Explorer" target="_blank">GWAS Explorer</a>.`,
    ],
  },
  {
    title: "AuthorArranger",
    items: [
      `Bogged down organizing authors and affiliations on journal title pages for large studies?<br>Check out <a href="https://authorarranger.nih.gov/" title="Author Arranger" target="_blank">AuthorArranger</a> and conquer title pages in seconds!`,
    ],
  },
];
