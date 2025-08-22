"use client";
import { useState, useMemo, useEffect } from "react";
import { Row, Col, Container, Form, Alert } from "react-bootstrap";
import { useSuspenseQuery, useQueryClient } from "@tanstack/react-query";
import { createColumnHelper } from "@tanstack/react-table";
import { useForm, useWatch } from "react-hook-form";
import Table from "@/components/table";
import { fetchOutput } from "@/services/queries";
import { FormData, ResultsData, VariantDetails } from "./types";
import { genomeBuildMap } from "@/store";
import "./styles.scss";

interface FormValues {
  selectedSnp: string;
}

export default function SNPClipResults({ ref }: { ref: string }) {
  const [showWarnings, setShowWarnings] = useState(false);
  const { register, reset, control } = useForm<FormValues>();

  const queryClient = useQueryClient();
  const formData = queryClient.getQueryData(["snpclip-form-data", ref]) as FormData | undefined;

  const { data: results } = useSuspenseQuery<ResultsData>({
    queryKey: ["snpclip_results", ref],
    queryFn: async () => (ref ? fetchOutput(`snpclip${ref}.json`) : null),
  });

  const selectedSnp = useWatch({ control, name: "selectedSnp" });

  useEffect(() => {
    if (results && !results.error) {
      reset({ selectedSnp: "" });
    }
  }, [results, reset]);

  const { warnings, thinnedSnps, detailsToShow } = useMemo(() => {
    if (!results?.details) {
      return {
        warnings: [] as VariantDetails[],
        thinnedSnps: results?.snp_list || [],
        detailsToShow: [] as VariantDetails[],
      };
    }

    const snpList = [...(results.snp_list || [])];
    const warnings: VariantDetails[] = [];
    const details = Object.entries(results.details);

    // Process warnings and filter out from snp list
    details.forEach(([rsNumber, [position, alleles, comment]]) => {
      if (!comment || (!comment.includes("Variant kept.") && !comment.includes("Variant in LD"))) {
        const index = snpList.indexOf(rsNumber);
        if (index > -1) snpList.splice(index, 1);
        warnings.push({
          rs_number: rsNumber,
          position: position || "",
          alleles: alleles || "",
          comment: comment || "",
        });
      }
    });

    // Process details for selected SNP
    const detailsToShow: VariantDetails[] = selectedSnp
      ? details
          .filter(([rs_number, [, , comment]]) => {
            // Include the selected SNP itself if it's kept
            if (rs_number === selectedSnp && comment?.includes("Variant kept.")) {
              return true;
            }
            // Include variants in LD with the selected SNP
            return comment?.includes(`Variant in LD with ${selectedSnp}`);
          })
          .map(([rs_number, [position, alleles, comment]]) => ({
            rs_number,
            position: position || "",
            alleles: alleles || "",
            comment: comment || "",
          }))
      : [];

    return { warnings, thinnedSnps: snpList, detailsToShow };
  }, [results, selectedSnp]);

  const getUCSCUrl = (rsNumber: string, position: string) => {
    if (!position) return "#";
    const [chr, pos] = position.split(":");
    const start = Math.max(0, parseInt(pos) - 250);
    const end = parseInt(pos) + 250;
    const newPosition = `${chr}:${start}-${end}`;
    const db = formData?.genome_build === "grch37" ? "hg19" : "hg38";
    return `https://genome.ucsc.edu/cgi-bin/hgTracks?db=${db}&position=${newPosition}&hgFind.matches=${rsNumber}`;
  };

  const columnHelper = createColumnHelper<VariantDetails>();
  const columns = [
    columnHelper.accessor("rs_number", {
      header: "RS Number",
      cell: (info) => (
        <a href={`http://www.ncbi.nlm.nih.gov/snp/${info.getValue()}`} target="_blank" rel="noopener noreferrer">
          {info.getValue()}
        </a>
      ),
    }),
    columnHelper.accessor("position", {
      header: `Position (${genomeBuildMap[formData?.genome_build || "grch37"]})`,
      cell: (info) => (
        <a href={getUCSCUrl(info.row.original.rs_number, info.getValue())} target="_blank" rel="noopener noreferrer">
          {info.getValue()}
        </a>
      ),
    }),
    columnHelper.accessor("alleles", {
      header: "Alleles",
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor("comment", {
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

  return (
    <>
      <hr />
      <Container fluid="md" className="p-3">
        {results?.warning && (
          <Alert variant="warning" dismissible>
            {results.warning}
          </Alert>
        )}

        <Row>
          <Col md={2}>
            <h5>LD Thinned Variant List</h5>
            <div>RS Number</div>
            <div className="overflow-auto border p-2" style={{ maxHeight: "400px" }}>
              {thinnedSnps.map((snp: string) => (
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

            {warnings.length > 0 && (
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
            {showWarnings && warnings.length > 0 ? (
              <Table title="Variants With Warnings" data={warnings} columns={columns} />
            ) : detailsToShow.length > 0 ? (
              <Table title={`Details for ${selectedSnp}`} data={detailsToShow} columns={columns} />
            ) : (
              !showWarnings && <div className="text-muted p-3">Click a variant on the left to view details.</div>
            )}
          </Col>
        </Row>

        <Row className="mt-3">
          <Col>
            <a href={`/LDlinkRestWeb/tmp/snp_list${ref}.txt`} download className="me-4">
              Download Thinned Variant List
            </a>
            <a href={`/LDlinkRestWeb/tmp/details${ref}.txt`} download>
              Download Thinned Variant List with Details
            </a>
          </Col>
        </Row>
      </Container>
    </>
  );
}
