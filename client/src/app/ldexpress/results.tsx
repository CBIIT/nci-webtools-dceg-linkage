"use client";
import { useMemo, useEffect } from "react";
import { Row, Col, Container, Accordion, Form } from "react-bootstrap";
import { useQuery, useSuspenseQuery } from "@tanstack/react-query";
import { createColumnHelper } from "@tanstack/react-table";
import { useForm, useFieldArray } from "react-hook-form";
import Table from "@/components/table";
import { fetchOutput } from "@/services/queries";
import { FormData, LocusData } from "./types";

export default function LdExpressResults({ ref }: { ref: string }) {
  const { register, reset, watch, control } = useForm();

  const { data: formData } = useQuery<FormData>({
    queryKey: ["ldexpress-form-data", ref],
    enabled: !!ref,
  });

  const { data: results } = useSuspenseQuery<LocusData | null>({
    queryKey: ["ldexpress_results", ref],
    queryFn: async () => (ref ? fetchOutput(`ldexpress${ref}.json`) : null),
  });

  const { fields } = useFieldArray({
    control,
    name: "snps",
  });

  useEffect(() => {
    if (results?.query_snps) {
      reset({
        snps: results.query_snps.map((snp) => ({
          value: snp[0],
          checked: false,
        })),
      });
    }
  }, [results, reset]);

  const tableData = useMemo(() => (results ? results.details.results.aaData : []), [results]);

  const genomeBuildMap: any = {
    grch37: "GRCh37",
    grch38: "GRCh38",
    grch38_high_coverage: "GRCh38 High Coverage",
  };

  const columnHelper = createColumnHelper<any>();
  const columns = [
    columnHelper.accessor((row) => row[0], {
      header: "Query",
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor((row) => row[1], {
      header: "RS Number",
      cell: (info) => {
        const value = info.getValue();
        if (value.includes("rs")) {
          return (
            <a href={`https://www.ncbi.nlm.nih.gov/snp/${value}`} target="_blank" rel="noopener noreferrer">
              {value}
            </a>
          );
        }
        return value;
      },
    }),
    columnHelper.accessor((row) => row[2], {
      header: `Position (${genomeBuildMap[formData?.genome_build as string]})`,
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor((row) => row[3], {
      header: "R²",
      cell: (info) => {
        const data = info.getValue();
        if (!isNaN(parseFloat(data))) {
          const floatData = parseFloat(data);
          if (floatData === 1.0) return "1.000";
          if (floatData === 0.0) return "0.000";
          if (floatData < 0.0001) return "<0.0001";
          return floatData.toFixed(3);
        }
        return data;
      },
    }),
    columnHelper.accessor((row) => row[4], {
      header: "D'",
      cell: (info) => {
        const data = info.getValue();
        if (!isNaN(parseFloat(data))) {
          const floatData = parseFloat(data);
          if (floatData === 1.0) return "1.000";
          if (floatData === 0.0) return "0.000";
          if (floatData < 0.0001) return "<0.0001";
          return floatData.toFixed(3);
        }
        return data;
      },
    }),
    columnHelper.accessor((row) => row[5], {
      header: "Gene Symbol",
      cell: (info) => {
        const value = info.getValue();
        const [symbol, id] = value.split("__");
        if (id === "NA") {
          return symbol;
        }
        return (
          <a href={`https://www.ncbi.nlm.nih.gov/gene/${id}`} target="_blank" rel="noopener noreferrer">
            {symbol}
          </a>
        );
      },
    }),
    columnHelper.accessor((row) => row[6], {
      header: "Gencode ID",
      cell: (info) => {
        const value = info.getValue();
        return (
          <a
            href={`https://ensembl.org/Homo_sapiens/Gene/Summary?g=${value.split(".")[0]}`}
            target="_blank"
            rel="noopener noreferrer">
            {value}
          </a>
        );
      },
    }),
    columnHelper.accessor((row) => row[7], {
      header: "Tissue",
      cell: (info) => {
        const value = info.getValue();
        const [tissue, tissueId] = value.split("__");
        return (
          <a
            href={`https://www.gtexportal.org/home/eqtls/tissue?tissueName=${tissueId}`}
            target="_blank"
            rel="noopener noreferrer">
            {tissue}
          </a>
        );
      },
    }),
    columnHelper.accessor((row) => row[8], {
      header: "Non-effect Allele Freq",
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor((row) => row[9], {
      header: "Effect Allele Freq",
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor((row) => row[10], {
      header: "Effect Size",
      cell: (info) => {
        const value = info.getValue();
        const [display, snp] = value.split("__");
        let formattedDisplay = display;
        if (!isNaN(parseFloat(display))) {
          formattedDisplay = parseFloat(display).toFixed(3);
        }
        return (
          <a href={`https://www.gtexportal.org/home/snp/${snp}`} target="_blank" rel="noopener noreferrer">
            {formattedDisplay}
          </a>
        );
      },
    }),
    columnHelper.accessor((row) => row[11], {
      header: "P-value",
      cell: (info) => {
        const value = info.getValue();
        const [display, snp] = value.split("__");
        let formattedDisplay;
        const floatData = parseFloat(display);
        if (display !== "NA" && !isNaN(floatData)) {
          if (floatData === 1.0) {
            formattedDisplay = "1.0";
          } else if (floatData === 0.0) {
            if (display.includes("e") || display.includes("E")) {
              const [mantissa, exponent] = display.split(/e/i);
              formattedDisplay = (
                <>
                  {mantissa}x10<sup>{exponent}</sup>
                </>
              );
            } else {
              formattedDisplay = "0.0";
            }
          } else {
            const [mantissa, exponent] = floatData.toExponential(0).split(/e/i);
            formattedDisplay = (
              <>
                {mantissa}x10<sup>{exponent}</sup>
              </>
            );
          }
        } else {
          formattedDisplay = display;
        }
        return (
          <a href={`https://www.gtexportal.org/home/snp/${snp}`} target="_blank" rel="noopener noreferrer">
            {formattedDisplay}
          </a>
        );
      },
    }),
  ];

  return (
    <Container fluid="md" className="justify-content-center">
      <Row>
        <Col sm="2">
          <Accordion defaultActiveKey={["0", "1", "2"]} alwaysOpen>
            <Accordion.Item eventKey="0">
              <Accordion.Header>Variants in LD with GTEx QTL</Accordion.Header>
              <Accordion.Body>
                {fields.map((field: any, index) => (
                  <Form.Check
                    key={field.id}
                    type="checkbox"
                    id={`snp-${index}`}
                    label={field.value}
                    {...register(`snps.${index}.checked`)}
                  />
                ))}
              </Accordion.Body>
            </Accordion.Item>
            <Accordion.Item eventKey="1">
              <Accordion.Header>Genes with GTEx QTL</Accordion.Header>
              <Accordion.Body></Accordion.Body>
            </Accordion.Item>
            <Accordion.Item eventKey="2">
              <Accordion.Header>Tissues with GTEx QTL</Accordion.Header>
              <Accordion.Body></Accordion.Body>
            </Accordion.Item>
          </Accordion>
        </Col>
        <Col>{tableData && <Table title="Express Results" data={tableData} columns={columns} />}</Col>
      </Row>
      <Row>
        <Col>
          <a href={`/LDlinkRestWeb/tmp/express_variants_annotated${ref}.txt`} download>
            Download GTEx QTL annotated variant list
          </a>
        </Col>
      </Row>
    </Container>
  );
}
