"use client";
import { Row, Col, Container, Alert } from "react-bootstrap";
import { useSuspenseQuery, useQueryClient } from "@tanstack/react-query";
import { createColumnHelper } from "@tanstack/react-table";
import { fetchOutput } from "@/services/queries";
import { FormData, ResultsData, LdtraitFormData } from "./types";
import { genomeBuildMap } from "@/store";
import { useState, useMemo } from "react";
import Table from "@/components/table";
import "./styles.scss";

export default function LdTraitResults({ ref }: { ref: string }) {
  const [activeKey, setActiveKey] = useState<string | null>(null);
  const [showWarnings, setShowWarnings] = useState(false);

  const queryClient = useQueryClient();
  let formData = queryClient.getQueryData(["ldtrait-form-data", ref]) as LdtraitFormData | undefined;
  if (!formData && typeof window !== "undefined") {
    const local = localStorage.getItem(`ldtrait-form-data-${ref}`);
    if (local) formData = JSON.parse(local);
  }
  //const formData = queryClient.getQueryData(["ldtrait-form-data", ref]) as LdtraitFormData | undefined;

  console.log("formData---", formData);
  const { data: results } = useSuspenseQuery<ResultsData>({
    queryKey: ["ldtrait_results", ref],
    queryFn: async () => (ref ? fetchOutput(`ldtrait${ref}.json`) : null),
  });

  // Fetch GWAS Catalog timestamp
  const { data: timestampData } = useSuspenseQuery({
    queryKey: ["ldtrait_timestamp"],
    queryFn: async () => {
      try {
        const response = await fetch("/LDlinkRestWeb/ldtrait_timestamp");
        const data = await response.json();
        return data;
      } catch (error) {
        console.error("Failed to fetch timestamp:", error);
        return null;
      }
    },
  });

  // Early return if no meaningful data
  if (!results || !results.thinned_snps || !results.details) {
    return <Alert variant="warning">No data available</Alert>;
  }

  console.log("Debug: Results data", results);

  // Format timestamp similar to the original JavaScript implementation
  const formatTimestamp = (timestampData: any) => {
    if (!timestampData || !timestampData.$date) return "...";
    
    try {
      const datetime = new Date(timestampData.$date);
      const date = datetime.toLocaleDateString("en-US");
      const time = datetime.toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
      });
      const timezone = datetime.toString().match(/([A-Z]+[\+-][0-9]+)/)?.[1] || "";
      return `${date}, ${time} (${timezone})`;
    } catch (error) {
      console.error("Error formatting timestamp:", error);
      return "...";
    }
  };

  // Transform data for the table
  const tableData = useMemo(() => {
    if (!results || !activeKey || !results.details[activeKey]?.aaData) return [];
    
    return results.details[activeKey].aaData;
  }, [results, activeKey]);

  // Create table columns
  const columnHelper = createColumnHelper<any>();
  const columns = [
    columnHelper.accessor((row) => row[0], {
      header: "GWAS Trait",
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor((row) => row[1], {
      header: "PMID",
      cell: (info) => {
        const value = info.getValue();
        return (
          <a href={`https://pubmed.ncbi.nlm.nih.gov/${value}`} target="_blank" rel="noopener noreferrer">
            {value}
          </a>
        );
      },
    }),
    columnHelper.accessor((row) => row[2], {
      header: "RS Number",
      cell: (info) => {
        const value = info.getValue();
        return value;
      },
    }),
    columnHelper.accessor((row) => row[3], {
      header: `Position (${genomeBuildMap[formData?.genome_build || "grch37"]})`,
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor((row) => row[4], {
      header: "Alleles",
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor((row) => row[5], {
      header: "R²",
      cell: (info) => {
        const value = info.getValue();
        const var1 = activeKey; // RS number from the selected variant in the left table
        const var2 = info.row.original[2]; // RS number from current row
        // Use the already processed population string from formData
        const popCodes = formData?.pop || 'ALL';
        const genomeBuild = formData?.genome_build || 'grch37'; // Genome build from form data
        
        console.log("R² Link - var1:", var1, "var2:", var2, "popCodes:", popCodes, "genomeBuild:", genomeBuild);
        const linkUrl = `/ldpair?var1=${var1}&var2=${var2}&pop=${popCodes}&genome_build=${genomeBuild}&tab=ldpair`;
        
        const displayValue = typeof value === 'number' ? value.toFixed(3) : value;
        
        return (
          <a href={linkUrl} target="_blank" rel="noopener noreferrer">
            {displayValue}
          </a>
        );
      },
    }),
    columnHelper.accessor((row) => row[6], {
      header: "D'",
      cell: (info) => {
        const value = info.getValue();
        const var1 = activeKey; // RS number from the selected variant in the left table
        const var2 = info.row.original[2]; // RS number from current row
        // Use the already processed population string from formData
        const popCodes = formData?.pop || 'ALL';
        const genomeBuild = formData?.genome_build || 'grch37'; // Genome build from form data
        
        console.log("D' Link - var1:", var1, "var2:", var2, "popCodes:", popCodes, "genomeBuild:", genomeBuild);
        const linkUrl = `/ldpair?var1=${var1}&var2=${var2}&pop=${popCodes}&genome_build=${genomeBuild}&tab=ldpair`;
        
        const displayValue = typeof value === 'number' ? value.toFixed(3) : value;
        
        return (
          <a href={linkUrl} target="_blank" rel="noopener noreferrer">
            {displayValue}
          </a>
        );
      },
    }),
    columnHelper.accessor((row) => row[8], {
      header: "Risk Allele Frequency", 
      cell: (info) => {
        const value = info.getValue();
        if (typeof value === 'number') {
          return value.toFixed(3);
        } else if (typeof value === 'string' && !isNaN(parseFloat(value))) {
          return parseFloat(value).toFixed(3);
        }
        return value;
      },
    }),
    columnHelper.accessor((row) => row[9], {
      header: "Beta or OR",
      cell: (info) => {
        const value = info.getValue();
        return typeof value === 'number' ? value.toFixed(3) : value;
      },
    }),
    columnHelper.accessor((row) => row[10], {
      header: "Effect Size (95% CI)",
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor((row) => row[11], {
      header: "P-value",
      cell: (info) => {
        const value = info.getValue();
        if (value !== "NA" && !isNaN(parseFloat(value))) {
          const floatData = parseFloat(value);
          if (floatData === 1.0) {
            return "1.0";
          } else if (floatData === 0.0) {
            if (value.includes("e") || value.includes("E")) {
              const [mantissa, exponent] = value.split(/e/i);
              return (
                <>
                  {mantissa}x10<sup>{exponent}</sup>
                </>
              );
            } else {
              return "0.0";
            }
          } else {
            const [mantissa, exponent] = floatData.toExponential(0).split(/e/i);
            return (
              <>
                {mantissa}x10<sup>{exponent}</sup>
              </>
            );
          }
        }
        return value;
      },
    }),
    columnHelper.accessor((row) => row[12], {
      header: "GWAS Catalog",
      cell: (info) => {
        //const rsNumber = info.row.original[2]; // Get RS number from column 2
        return (
          <a 
            href={`https://www.ebi.ac.uk/gwas/variants/${info.getValue()}`} 
            target="_blank" 
            rel="noopener noreferrer"
          >
            Link
          </a>
        );
      },
    }),
  ];

  // Transform warnings data for the table
  const warningsTableData = useMemo(() => {
    if (!results || !results.details.queryWarnings?.aaData) return [];
    return results.details.queryWarnings.aaData;
  }, [results]);

  // Create warnings table columns
  const warningsColumns = [
    columnHelper.accessor((row) => row[0], {
      header: "Variant",
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor((row) => row[1], {
      header: `Position (${genomeBuildMap[formData?.genome_build || "grch37"]})`,
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor((row) => row[2], {
      header: "Details",
      cell: (info) => info.getValue(),
    }),
  ];

  return (
    <>
      {!results.error ? (
        <Container fluid="fluid" className="p-3" id="ldtrait-results-container">
          <Row id="ldtrait-table-container">
            <Col md={2} className="ldtrait-table-scroller">
              <div>Variants in LD with GWAS Catalog</div>
              <table id="ldtrait-table-thin" className="table table-striped">
                <thead>
                  <tr>
                    <th className="rs-number">RS Number</th>
                  </tr>
                </thead>
                <tbody id="ldtrait-snp-list">
                  {results.thinned_snps.map((snp: string) => (
                    <tr key={snp} onClick={() => setActiveKey(snp)} className={activeKey === snp ? "active" : ""}>
                      <td>
                        <a className="ldtrait-link">{snp}</a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {results.details.queryWarnings?.aaData?.length > 0 && (
                <a
                  id="ldtrait-warnings-button"
                  title="View details."
                  onClick={() => setShowWarnings(!showWarnings)}
                  style={{ cursor: "pointer" }}>
                  {showWarnings ? "Hide" : "Show"} Variants with Warnings
                </a>
              )}
            </Col>

            <Col md={10} className="ldtrait-table-scroller" id="ldtrait-detail">
              {activeKey && (
                <>
                  <Row>
                    <Col>
                      <div id="ldtrait-detail-title">Details for {activeKey}</div>
                    </Col>
                  </Row>
                  {tableData.length > 0 && <Table title="" data={tableData} columns={columns} />}
                </>
              )}

              {showWarnings && warningsTableData.length > 0 && (
                <Table title="Query Variants with Warnings" data={warningsTableData} columns={warningsColumns} />
              )}

              {!activeKey && !showWarnings && (
                <div id="ldtrait-initial-message">Click a variant on the left to view details.</div>
              )}
            </Col>
          </Row>

          <Row className="mt-3">
            <Col>
              <a href={`/LDlinkRestWeb/tmp/trait_variants_annotated_${ref}.txt`} download>
                Download GWAS Catalog annotated variant list
              </a>
            </Col>
          </Row>
          <Row className="mt-2">
            <Col>
              <i>GWAS Catalog last updated on <span id="ldtrait-timestamp">{formatTimestamp(timestampData)}</span></i>
            </Col>
          </Row>
        </Container>
      ) : (
        <Alert variant="danger">{results?.error || "An error has occurred"}</Alert>
      )}
    </>
  );
}
