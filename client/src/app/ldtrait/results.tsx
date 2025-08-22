"use client";
import { useState, useMemo, useEffect } from "react";
import { Row, Col, Container, Form, Alert } from "react-bootstrap";
import { useSuspenseQuery, useQueryClient } from "@tanstack/react-query";
import { createColumnHelper } from "@tanstack/react-table";
import { useForm, useWatch } from "react-hook-form";
import Table from "@/components/table";
import { fetchOutput } from "@/services/queries";
import { FormData, ResultsData, LdtraitFormData } from "./types";
import { genomeBuildMap } from "@/store";

interface FormValues {
  selectedSnp: string;
}

export default function LdTraitResults({ ref }: { ref: string }) {
  const [showWarnings, setShowWarnings] = useState(false);
  const { register, reset, control } = useForm<FormValues>();

  const queryClient = useQueryClient();
  const formData = queryClient.getQueryData(["ldtrait-form-data", ref]) as LdtraitFormData | undefined;

  const { data: results } = useSuspenseQuery<ResultsData>({
    queryKey: ["ldtrait_results", ref],
    queryFn: async () => (ref ? fetchOutput(`ldtrait${ref}.json`) : null),
  });

  const selectedSnp = useWatch({ control, name: "selectedSnp" });

  useEffect(() => {
    if (results && !results.error) {
      reset({ selectedSnp: "" });
    }
  }, [results, reset]);

  // Early return if no meaningful data
  const noData = !results || !results.thinned_snps || !results.details;

  // Transform data for the table
  const tableData = useMemo(() => {
    if (!results || !selectedSnp || !results.details[selectedSnp]?.aaData) return [];

    return results.details[selectedSnp].aaData;
  }, [results, selectedSnp]);

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
        const var1 = selectedSnp; // RS number from the selected variant in the left table
        const var2 = info.row.original[2]; // RS number from current row
        // Use the already processed population string from formData
        const popCodes = formData?.pop || "ALL";
        const genomeBuild = formData?.genome_build || "grch37"; // Genome build from form data

        const linkUrl = `/ldpair?var1=${var1}&var2=${var2}&pop=${popCodes}&genome_build=${genomeBuild}&tab=ldpair`;

        const displayValue = typeof value === "number" ? value.toFixed(3) : value;

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
        const var1 = selectedSnp; // RS number from the selected variant in the left table
        const var2 = info.row.original[2]; // RS number from current row
        // Use the already processed population string from formData
        const popCodes = formData?.pop || "ALL";
        const genomeBuild = formData?.genome_build || "grch37"; // Genome build from form data

        const linkUrl = `/ldpair?var1=${var1}&var2=${var2}&pop=${popCodes}&genome_build=${genomeBuild}&tab=ldpair`;

        const displayValue = typeof value === "number" ? value.toFixed(3) : value;

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
        if (typeof value === "number") {
          return value.toFixed(3);
        } else if (typeof value === "string" && !isNaN(parseFloat(value))) {
          return parseFloat(value).toFixed(3);
        }
        return value;
      },
    }),
    columnHelper.accessor((row) => row[9], {
      header: "Beta or OR",
      cell: (info) => {
        const value = info.getValue();
        return typeof value === "number" ? value.toFixed(3) : value;
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
          <a href={`https://www.ebi.ac.uk/gwas/variants/${info.getValue()}`} target="_blank" rel="noopener noreferrer">
            Link
          </a>
        );
      },
    }),
  ];

  // Transform warnings data for the table
  const warningsTableData = useMemo(() => {
    if (!results || !results.details || !results.details.queryWarnings || !results.details.queryWarnings.aaData)
      return [];
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

  if (results?.error) {
    return (
      <>
        <hr />
        <Alert variant="danger">{results.error}</Alert>
      </>
    );
  }

  if (noData) {
    return (
      <>
        <hr />
        <Alert variant="warning">No data available</Alert>
      </>
    );
  }

  return (
    <>
      <hr />
      <Container fluid="md" className="p-3">
        <Row>
          <Col md={2}>
            <h5>Variants in LD with GWAS Catalog</h5>
            <div>RS Number</div>
            <div className="overflow-auto border p-2" style={{ maxHeight: "400px" }}>
              {results.thinned_snps.map((snp: string) => (
                <Form.Check
                  key={snp}
                  type="radio"
                  id={`snp-${snp}`}
                  label={snp}
                  value={snp}
                  {...register("selectedSnp")}
                  disabled={showWarnings}
                  className="mb-2"
                  title="View details"
                />
              ))}
            </div>

            {(results.details.queryWarnings?.aaData?.length ?? 0) > 0 && (
              <Form className="my-3">
                <Form.Check
                  type="switch"
                  id="view-warnings"
                  label="Variants with Warnings"
                  checked={showWarnings}
                  onChange={() => setShowWarnings(!showWarnings)}
                />
              </Form>
            )}
          </Col>

          <Col md={10} className="overflow-auto">
            {showWarnings && warningsTableData.length > 0 ? (
              <Table title="Query Variants with Warnings" data={warningsTableData} columns={warningsColumns} />
            ) : selectedSnp && tableData.length > 0 ? (
              <Table title={`Details for ${selectedSnp}`} data={tableData} columns={columns} />
            ) : (
              !showWarnings && <div className="text-muted p-3">Click a variant on the left to view details.</div>
            )}
          </Col>
        </Row>

        <Row className="mt-3">
          <Col>
            <a href={`/LDlinkRestWeb/tmp/trait_variants_annotated${ref}.txt`} download>
              Download GWAS Catalog annotated variant list
            </a>
          </Col>
        </Row>
      </Container>
    </>
  );
}
