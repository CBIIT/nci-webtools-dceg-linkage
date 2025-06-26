"use client";
import { useEffect, useRef } from "react";
import { useSearchParams } from "next/navigation";
import { Row, Col, Container, Form, Button } from "react-bootstrap";
import { useQuery, useSuspenseQuery, useQueryClient } from "@tanstack/react-query";
import { createColumnHelper } from "@tanstack/react-table";
import Table from "@/components/table";
import { fetchOutput, ldassoc } from "@/services/queries";
// import { embed } from "@bokeh/bokehjs";

export default function LdAssocResults() {
  const queryClient = useQueryClient();
  const searchParams = useSearchParams();
  const ref = searchParams.get("ref");

  const { data: plot } = useSuspenseQuery({
    queryKey: ["ldassoc-submit", ref],
    queryFn: async () => {
      if (!ref) return null;
      const formData = queryClient.getQueryData(["ldassoc-form", ref]);
      if (!formData) throw new Error("No form data found for this reference.");
      return ldassoc(formData);
    },
  });
  const { data: results } = useSuspenseQuery({
    queryKey: ["ldassoc", ref],
    queryFn: async () => (ref ? fetchOutput(`assoc${ref}.json`) : null),
    refetchInterval: (data) => (!data ? 10 * 1000 : false),
    // retry: 6,
  });

  // const plotRef = useRef<HTMLDivElement>(null);
  console.log(results);
  console.log(plot);

  // useEffect(() => {
  //   if (plot && plotRef.current) {
  //     // Clear previous plot if any
  //     plotRef.current.innerHTML = "";
  //     // Embed the Bokeh plot
  //     embed.embed_item(plot, plotRef.current);
  //   }
  // }, [plot]);

  const columnHelper = createColumnHelper<any>();

  const columns = [
    columnHelper.accessor((row) => row[0], {
      header: "RS Number",
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor((row) => row[1], {
      header: "Chr",
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor((row) => row[2], {
      header: "Position ([genome])",
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor((row) => row[3], {
      header: "Alleles",
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor((row) => row[4], {
      header: "MAF",
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor((row) => row[5], {
      header: "Distance",
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor((row) => row[6], {
      header: "D&#39;",
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor((row) => row[7], {
      header: "R²",
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor((row) => row[8], {
      header: "Correlated Alleles",
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor((row) => row[9], {
      header: "Association P-value",
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor((row) => row[10], {
      header: "FORGEdb",
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor((row) => row[11], {
      header: "RegulomeDB",
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor((row) => row[12], {
      header: "HaploReg",
      cell: (info) => {
        const rs = info.row.original[0];
        if (!rs || rs === ".") return "";
        const url = `http://pubs.broadinstitute.org/mammals/haploreg/detail_v4.2.php?id=${rs}`;
        return (
          <a href={url} target="_blank" rel="noopener noreferrer">
            Link <i className="bi bi-box-arrow-up-right"></i>
          </a>
        );
      },
    }),
    columnHelper.accessor((row) => row[13], {
      header: "Functional Class",
      cell: (info) => info.getValue(),
    }),
  ];

  return (
    <Container fluid="md">
      {/* <pre>{JSON.stringify(results, null, 2)}</pre> */}

      {results && (
        <>
          {/* <div ref={plotRef} /> */}
          {plot && (
            <div
              // This will render the HTML returned by your backend
              dangerouslySetInnerHTML={{ __html: plot }}
            />
          )}
          <Table title="Association Results" data={results.aaData} columns={columns} />
        </>
      )}
    </Container>
  );
}
