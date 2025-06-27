"use client";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { Row, Col, Form, Button, ButtonGroup, ToggleButton } from "react-bootstrap";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter, usePathname } from "next/navigation";
import { upload, ldassoc, ldassocExample } from "@/services/queries";
import PopSelect, { PopOption } from "@/components/select/pop-select";
import CalculateLoading from "@/components/calculateLoading";

export interface FormData {
  "pop": PopOption[];
  "filename": string;
  "reference": string;
  "columns[chromosome]": string;
  "columns[position]": string;
  "columns[pvalue]": string;
  "calculateRegion": "region" | "gene" | "variant";
  "gene[name]": string;
  "gene[basepair]": string;
  "gene[index]": string;
  "region[start]": string;
  "region[end]": string;
  "region[index]": string;
  "variant[index]": string;
  "variant[basepair]": string;
  "genome_build": "grch37" | "grch38" | "grch38_high_coverage";
  "dprime": boolean;
  "transcript": boolean;
  "annotate": "forge" | "regulome" | "no";
  "useEx": boolean;
}

export default function LDAssocForm() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const pathname = usePathname();

  const defaultForm: FormData = {
    "pop": [],
    "filename": "",
    "reference": "",
    "columns[chromosome]": "",
    "columns[position]": "",
    "columns[pvalue]": "",
    "calculateRegion": "region",
    "gene[name]": "",
    "gene[basepair]": "100000",
    "gene[index]": "",
    "region[start]": "",
    "region[end]": "",
    "region[index]": "",
    "variant[index]": "",
    "variant[basepair]": "500000",
    "genome_build": "grch37",
    "dprime": false,
    "transcript": false,
    "annotate": "forge",
    "useEx": false,
  };
  const { control, register, handleSubmit, reset, watch, setValue } = useForm({
    defaultValues: defaultForm,
  });
  const columnOptions = ["chr", "pos", "rsid", "p"];

  const filename = watch("filename") as string | FileList;
  const genome_build = watch("genome_build");
  const useEx = watch("useEx");
  const calculateRegion = watch("calculateRegion");

  const { data: exampleData, isFetching } = useQuery({
    queryKey: ["ldassoc", genome_build, useEx],
    queryFn: () => ldassocExample(genome_build),
    enabled: useEx,
  });

  useEffect(() => {
    if (exampleData) {
      setValue("filename", exampleData.filename);
      setValue("columns[chromosome]", exampleData.headers[0]);
      setValue("columns[position]", exampleData.headers[1]);
      setValue("columns[pvalue]", exampleData.headers[3]);
      setValue("calculateRegion", "region");
      setValue("region[index]", "rs7837688");
      setValue("pop", [{ value: "CEU", label: "(CEU) Utah Residents from North and West Europe" }]);
      switch (genome_build) {
        case "grch37":
          setValue("region[start]", "chr8:128289591");
          setValue("region[end]", "chr8:128784397");
          break;
        case "grch38":
        case "grch38_high_coverage":
          setValue("region[start]", "chr8:127277115");
          setValue("region[end]", "chr8:127777115");
          break;
      }
    } else {
      setValue("filename", "");
    }
  }, [exampleData, genome_build, setValue]);

  const submitForm = useMutation<any, unknown, any>({
    mutationFn: (params: any) => ldassoc(params),
    onSuccess: (_data, variables) => {
      // variables contains the submitted data
      if (variables && variables.reference) {
        router.push(`${pathname}?ref=${variables.reference}`);
      }
    },
  });

  async function handleUpload(data: any) {
    try {
      const fileData = new FormData();
      fileData.append("ldassocFile", data.filename[0]);

      await upload(fileData);
    } catch (error) {
      console.error("Error uploading file:", error);
      return;
    }
  }

  async function onSubmit(data: any) {
    if (!data.useEx) await handleUpload(data);
    const reference = Math.floor(Math.random() * (99999 - 10000 + 1)).toString();
    const formData = {
      ...data,
      reference,
      pop: data.pop.map((e: PopOption) => e.value).join("+"),
      filename: typeof filename === "string" ? filename : (filename && filename[0] && (filename[0] as File).name) || "",
    };
    queryClient.setQueryData(["ldassoc-form-data", reference], formData);
    submitForm.mutate(formData);
  }

  function onReset(event: any): void {
    event.preventDefault();
    router.push("/ldassoc");
    reset(defaultForm);
    queryClient.invalidateQueries();
  }

  return (
    <Form id="ldassoc-form" onSubmit={handleSubmit(onSubmit)} onReset={onReset}>
      <Row>
        <Col sm="auto">
          <Form.Group controlId="genome_build" className="mb-3">
            <Form.Label>Genome Build (1000G)</Form.Label>
            <Form.Select {...register("genome_build")}>
              <option value="grch37">GRCh37</option>
              <option value="grch38">GRCh38</option>
              <option value="grch38_high_coverage">GRCh38 High Coverage</option>
            </Form.Select>
          </Form.Group>
        </Col>
      </Row>
      <Row>
        <Col sm={3}>
          <Form.Group controlId="filename" className="mb-3">
            <Form.Label>File</Form.Label>
            {typeof filename === "string" && filename !== "" ? (
              <div className="form-control bg-light">{filename}</div>
            ) : (
              <Form.Control type="file" {...register("filename")} />
            )}
          </Form.Group>
          <Form.Group controlId="useEx">
            <Form.Check type="switch" id="useEx" label="Use example GWAS data" {...register("useEx")} />
          </Form.Group>

          {filename && (
            <div>
              <Form.Group controlId="columns[chromosome]" className="mb-3">
                <Form.Label>Chromosome Column</Form.Label>
                <Form.Select {...register("columns[chromosome]", { required: true })}>
                  {columnOptions.map((e, i) => (
                    <option key={e + i + "chr"} value={e}>
                      {e}
                    </option>
                  ))}
                </Form.Select>
              </Form.Group>
              <Form.Group controlId="columns[position]" className="mb-3">
                <Form.Label>Position Column</Form.Label>
                <Form.Select {...register("columns[position]", { required: true })}>
                  {columnOptions.map((e, i) => (
                    <option key={e + i + "pos"} value={e}>
                      {e}
                    </option>
                  ))}
                </Form.Select>
              </Form.Group>
              <Form.Group controlId="columns[pvalue]" className="mb-3">
                <Form.Label>P-Value</Form.Label>
                <Form.Select {...register("columns[pvalue]", { required: true })}>
                  {columnOptions.map((e, i) => (
                    <option key={e + i + "pval"} value={e}>
                      {e}
                    </option>
                  ))}
                </Form.Select>
              </Form.Group>
            </div>
          )}
        </Col>
        <Col sm={3}>
          <Form.Group controlId="calculateRegion" className="mb-3">
            <Form.Label>Region Type</Form.Label>
            <Form.Select {...register("calculateRegion")}>
              <option value="gene">Gene</option>
              <option value="region">Region</option>
              <option value="variant">Variant</option>
            </Form.Select>
          </Form.Group>
          {calculateRegion === "gene" && (
            <div>
              {" "}
              <div>
                <Form.Group controlId="gene[name]" className="mb-3">
                  <Form.Label>Gene name</Form.Label>
                  <Form.Control {...register("gene[name]")} placeholder="Gene name" />
                </Form.Group>
                <Form.Group controlId="gene[basepair]" className="mb-3">
                  <Form.Label>Base pair window</Form.Label>
                  <div className="d-flex align-items-center">
                    ±&nbsp;
                    <Form.Control type="number" {...register("gene[basepair]")} placeholder="100000" />
                  </div>
                </Form.Group>
                <Form.Group controlId="gene[index]" className="mb-3">
                  <Form.Label>Index RSID</Form.Label>
                  <Form.Control {...register("gene[index]")} placeholder="(optional)" />
                </Form.Group>
              </div>
            </div>
          )}
          {calculateRegion === "region" && (
            <div>
              <Form.Group controlId="region[start]" className="mb-3">
                <Form.Label>Region Start</Form.Label>
                <Form.Control {...register("region[start]")} placeholder="Start Coord (chr1:50000 or 1:50000)" />
              </Form.Group>
              <Form.Group controlId="region[end]" className="mb-3">
                <Form.Label>Region End</Form.Label>
                <Form.Control {...register("region[end]")} placeholder="End Coord (chr1:50000 or 1:50000)" />
              </Form.Group>
              <Form.Group controlId="region[index]" className="mb-3">
                <Form.Label>Index RSID</Form.Label>
                <Form.Control {...register("region[index]")} placeholder="(optional)" />
              </Form.Group>
            </div>
          )}
          {calculateRegion === "variant" && (
            <div>
              <Form.Group controlId="variant[end]" className="mb-3">
                <Form.Label>Variant RSID</Form.Label>
                <Form.Control {...register("variant[index]")} placeholder="Variant RSID" />
              </Form.Group>
              <Form.Group controlId="variant[basepair]" className="mb-3">
                <Form.Label>Base pair window</Form.Label>
                <div className="d-flex align-items-center">
                  ±&nbsp;
                  <Form.Control type="number" {...register("variant[basepair]")} />
                </div>
              </Form.Group>
            </div>
          )}
        </Col>
        <Col sm={3}>
          <Form.Group controlId="pop" className="mb-3">
            <Form.Label>Population</Form.Label>
            <PopSelect name="pop" control={control} />
          </Form.Group>
          <Form.Group controlId="dprime" className="mb-3">
            <Form.Label>LD measure:</Form.Label>
            <ButtonGroup className="ms-3">
              <ToggleButton
                id="radio-r2"
                type="radio"
                variant="outline-primary"
                {...register("dprime")}
                value="false"
                checked={!watch("dprime")}
                onChange={() => {
                  setValue("dprime", false);
                }}>
                R<sup>2</sup>
              </ToggleButton>
              <ToggleButton
                id="radio-dprime"
                type="radio"
                variant="outline-primary"
                {...register("dprime")}
                value="true"
                checked={!!watch("dprime")}
                onChange={() => {
                  setValue("dprime", true);
                }}>
                D&#39;
              </ToggleButton>
            </ButtonGroup>
          </Form.Group>
          <Form.Group controlId="transcript" className="mb-3">
            <Form.Label>Collapse transcripts:</Form.Label>
            <ButtonGroup className="ms-3">
              <ToggleButton
                id="radio-transcript-yes"
                type="radio"
                variant="outline-primary"
                {...register("transcript")}
                value="true"
                checked={!!watch("transcript")}
                onChange={() => {
                  setValue("transcript", true);
                }}>
                Yes
              </ToggleButton>
              <ToggleButton
                id="radio-transcript-no"
                type="radio"
                variant="outline-primary"
                {...register("transcript")}
                value="false"
                checked={!watch("transcript")}
                onChange={() => {
                  setValue("transcript", false);
                }}>
                No
              </ToggleButton>
            </ButtonGroup>
          </Form.Group>
          <Form.Group controlId="annotate" className="mb-3">
            <Form.Label>Annotation:</Form.Label>
            <ButtonGroup className="ms-3">
              <ToggleButton
                id="radio-annotate-forgedb"
                type="radio"
                variant="outline-primary"
                {...register("annotate")}
                value="forge"
                checked={watch("annotate") === "forge"}
                onChange={() => {
                  setValue("annotate", "forge");
                }}>
                FORGEdb
              </ToggleButton>
              <ToggleButton
                id="radio-annotate-regulome"
                type="radio"
                variant="outline-primary"
                {...register("annotate")}
                value="regulome"
                checked={watch("annotate") === "regulome"}
                onChange={() => {
                  setValue("annotate", "regulome");
                }}>
                RegulomeDB
              </ToggleButton>
              <ToggleButton
                id="radio-annotate-no"
                type="radio"
                variant="outline-primary"
                {...register("annotate")}
                value="no"
                checked={watch("annotate") === "no"}
                onChange={() => {
                  setValue("annotate", "no");
                }}>
                None
              </ToggleButton>
            </ButtonGroup>
          </Form.Group>
        </Col>
        <Col sm={3}>
          <div className="text-end">
            <Button type="reset" variant="outline-danger" className="me-1">
              Reset
            </Button>
            <Button type="submit" variant="primary" disabled={submitForm.isPending}>
              Submit
            </Button>
          </div>
        </Col>
      </Row>
      {submitForm.isPending && <CalculateLoading />}
    </Form>
  );
}
