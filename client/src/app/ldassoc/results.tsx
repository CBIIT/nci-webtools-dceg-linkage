"use client";
import { useEffect, useRef } from "react";
import { useSearchParams } from "next/navigation";
import { Row, Col, Container, Form, Button } from "react-bootstrap";
import { useSuspenseQuery, useQueryClient } from "@tanstack/react-query";
import { createColumnHelper } from "@tanstack/react-table";
import Table from "@/components/table";
import { fetchOutput, fetchHtmlOutput } from "@/services/queries";

export default function LdAssocResults() {
  const queryClient = useQueryClient();
  const searchParams = useSearchParams();
  const ref = searchParams.get("ref");

  const { data: tableData } = useSuspenseQuery({
    queryKey: ["ldassoc_table", ref],
    queryFn: async () => (ref ? fetchOutput(`assoc${ref}.json`) : null),
  });
  const { data: plotHtml } = useSuspenseQuery({
    queryKey: ["ldassoc_plot", ref],
    queryFn: async () => (ref ? fetchHtmlOutput(`ldassoc_plot_${ref}.html`) : null),
  });

  console.log("table", tableData);

  const plotRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (plotHtml && plotRef.current) {
      // Find and execute scripts
      const scripts = plotRef.current.querySelectorAll("script");
      scripts.forEach((oldScript) => {
        const newScript = document.createElement("script");
        Array.from(oldScript.attributes).forEach((attr) => newScript.setAttribute(attr.name, attr.value));
        newScript.text = oldScript.text;
        oldScript.parentNode?.replaceChild(newScript, oldScript);
      });
    }
  }, [plotHtml]);

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
      {/* <pre>{JSON.stringify(tableData, null, 2)}</pre> */}

      {tableData && (
        <>
          {plotHtml && <div className="mt-4" ref={plotRef} dangerouslySetInnerHTML={{ __html: plotHtml }} />}
          <Table title="Association Results" data={tableData.aaData} columns={columns} />
        </>
      )}
    </Container>
  );
}
