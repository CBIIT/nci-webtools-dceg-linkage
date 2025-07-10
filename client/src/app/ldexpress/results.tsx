"use client";
import { useMemo, useEffect } from "react";
import { Row, Col, Container, Accordion, Form } from "react-bootstrap";
import { useQuery, useSuspenseQuery } from "@tanstack/react-query";
import { createColumnHelper } from "@tanstack/react-table";
import { useForm, useFieldArray, useWatch } from "react-hook-form";
import Table from "@/components/table";
import { fetchOutput } from "@/services/queries";
import { FormData, LocusData } from "./types";

type FormValues = {
  snps: { value: string; checked: boolean }[];
  genes: { value: string; checked: boolean }[];
  tissues: { value: string; checked: boolean }[];
};

export default function LdExpressResults({ ref }: { ref: string }) {
  const { register, reset, control } = useForm<FormValues>();

  const { data: formData } = useQuery<FormData>({
    queryKey: ["ldexpress-form-data", ref],
    enabled: !!ref,
    queryFn: async () => {
      return {} as FormData;
    },
  });

  const { data: results } = useSuspenseQuery<LocusData | null>({
    queryKey: ["ldexpress_results", ref],
    queryFn: async () => (ref ? fetchOutput(`ldexpress${ref}.json`) : null),
  });

  const { fields: snpsFields, append: appendSnp } = useFieldArray({
    control,
    name: "snps",
  });
  const { fields: genesFields, append: appendGene } = useFieldArray({
    control,
    name: "genes",
  });
  const { fields: tissuesFields, append: appendTissue } = useFieldArray({
    control,
    name: "tissues",
  });
  const snps = useWatch({ control, name: "snps" });
  const genes = useWatch({ control, name: "genes" });
  const tissues = useWatch({ control, name: "tissues" });

  useEffect(() => {
    if (results) {
      reset();
      results.thinned_snps.forEach((snp) => {
        appendSnp({ value: snp, checked: false });
      });
      results.thinned_genes.forEach((gene) => {
        appendGene({ value: gene.split("__")[0], checked: false });
      });
      results.thinned_tissues.forEach((tissue) => {
        appendTissue({ value: tissue.split("__")[0], checked: false });
      });
    }
  }, [results, appendSnp, appendGene, appendTissue]);

  const tableData = useMemo(() => {
    if (!results) return [];
    const selectedSnps = snps?.filter((snp) => snp.checked).map((snp) => snp.value) || [];
    const selectedGenes = genes?.filter((gene) => gene.checked).map((gene) => gene.value) || [];
    const selectedTissues = tissues?.filter((tissue) => tissue.checked).map((tissue) => tissue.value) || [];

    return results.details.results.aaData.filter((row: any) => {
      const snp = row[0];
      const gene = row[5].split("__")[0];
      const tissue = row[7].split("__")[0];
      const snpMatch = selectedSnps.length > 0 ? selectedSnps.includes(snp) : true;
      const geneMatch = selectedGenes.length > 0 ? selectedGenes.includes(gene) : true;
      const tissueMatch = selectedTissues.length > 0 ? selectedTissues.includes(tissue) : true;

      return snpMatch && geneMatch && tissueMatch;
    });
  }, [results, snps, genes, tissues]);

  const genomeBuildMap: Record<string, string> = {
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
                {snpsFields.map((field: any, index) => (
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
              <Accordion.Body>
                {genesFields.map((field: any, index) => (
                  <Form.Check
                    key={field.id}
                    type="checkbox"
                    id={`gene-${index}`}
                    label={field.value}
                    {...register(`genes.${index}.checked`)}
                  />
                ))}
              </Accordion.Body>
            </Accordion.Item>
            <Accordion.Item eventKey="2">
              <Accordion.Header>Tissues with GTEx QTL</Accordion.Header>
              <Accordion.Body className="overflow-auto">
                {tissuesFields.map((field: any, index) => (
                  <Form.Check
                    key={field.id}
                    type="checkbox"
                    id={`tissue-${index}`}
                    label={field.value}
                    {...register(`tissues.${index}.checked`)}
                  />
                ))}
              </Accordion.Body>
            </Accordion.Item>
          </Accordion>
        </Col>
        <Col>
          <div>
            {tableData && <Table title="" data={tableData} columns={columns} />}
            <a href={`/LDlinkRestWeb/tmp/express_variants_annotated${ref}.txt`} download>
              Download GTEx QTL annotated variant list
            </a>
          </div>
        </Col>
      </Row>
    </Container>
  );
}
