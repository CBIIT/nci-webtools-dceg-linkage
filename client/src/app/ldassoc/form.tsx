"use client";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { Row, Col, Form, Button, ButtonGroup, ToggleButton } from "react-bootstrap";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter, usePathname } from "next/navigation";
import { upload, ldassoc, ldassocExample } from "@/services/queries";
import PopSelect, { PopOption } from "@/components/select/pop-select";
import CalculateLoading from "@/components/calculateLoading";
import { useStore } from "@/store";

export interface FormData {
  pop: PopOption[];
  filename: string;
  reference: string;
  columns: {
    chromosome: string;
    position: string;
    pvalue: string;
  };
  calculateRegion: "" | "region" | "gene" | "variant";
  gene: {
    name: string;
    basepair: string;
    index: string;
  };
  region: {
    start: string;
    end: string;
    index: string;
  };
  variant: {
    index: string;
    basepair: string;
  };
  genome_build: "grch37" | "grch38" | "grch38_high_coverage";
  dprime: boolean;
  transcript: boolean;
  annotate: "forge" | "regulome" | "no";
  useEx: boolean;
}

export default function LDAssocForm() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const pathname = usePathname();
  const { genome_build } = useStore((state) => state);

  const defaultForm: FormData = {
    pop: [],
    filename: "",
    reference: "",
    columns: {
      chromosome: "",
      position: "",
      pvalue: "",
    },
    calculateRegion: "",
    gene: {
      name: "",
      basepair: "100000",
      index: "",
    },
    region: {
      start: "",
      end: "",
      index: "",
    },
    variant: {
      index: "",
      basepair: "500000",
    },
    genome_build: "grch37",
    dprime: false,
    transcript: false,
    annotate: "forge",
    useEx: false,
  };
  const {
    control,
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    setError,
    formState: { errors },
  } = useForm({
    defaultValues: defaultForm,
  });
  const [columnOptions, setColumnOptions] = useState<string[]>([]);

  const filename = watch("filename") as string | FileList;
  const useEx = watch("useEx");
  const calculateRegion = watch("calculateRegion");

  // get headers from association file
  useEffect(() => {
    if (filename && typeof filename !== "string" && filename.length > 0) {
      const file = filename[0];
      const reader = new FileReader();
      reader.onload = (e) => {
        const text = e.target?.result as string;
        if (text) {
          const [header] = text.split("\n");
          const columns = header.trim().split(/\s+/);
          if (columns.length > 0 && columns[0]) {
            setColumnOptions(columns);
            setValue("columns.chromosome", "");
            setValue("columns.position", "");
            setValue("columns.pvalue", "");
            setError("filename", {});
          } else {
            setColumnOptions([]);
            setError("filename", {
              type: "manual",
              message: "Header not found. Please ensure the file is not empty and contains a header row.",
            });
          }
        }
      };
      reader.readAsText(file);
    }
  }, [filename, setValue, setError]);

  const { data: exampleData, isFetching } = useQuery({
    queryKey: ["ldassoc", genome_build, useEx],
    queryFn: () => ldassocExample(genome_build),
    enabled: useEx,
  });

  useEffect(() => {
    if (exampleData) {
      setColumnOptions(exampleData.headers);
      setValue("filename", exampleData.filename);
      setValue("columns.chromosome", exampleData.headers[0]);
      setValue("columns.position", exampleData.headers[1]);
      setValue("columns.pvalue", exampleData.headers[3]);
      setValue("calculateRegion", "region");
      setValue("region.index", "rs7837688");
      setValue("pop", [{ value: "CEU", label: "(CEU) Utah Residents from North and West Europe" }]);
      switch (genome_build) {
        case "grch37":
          setValue("region.start", "chr8:128289591");
          setValue("region.end", "chr8:128784397");
          break;
        case "grch38":
        case "grch38_high_coverage":
          setValue("region.start", "chr8:127277115");
          setValue("region.end", "chr8:127777115");
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
      genome_build,
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
    <Form id="ldassoc-form" onSubmit={handleSubmit(onSubmit)} onReset={onReset} noValidate>
      <Row>
        <Col sm={3}>
          <Form.Group controlId="filename" className="mb-3">
            <Form.Label>Association Data File</Form.Label>
            {typeof filename === "string" && filename !== "" ? (
              <div className="form-control bg-light">{filename}</div>
            ) : (
              <Form.Control
                placeholder="Upload"
                type="file"
                {...register("filename", { required: "Association data file is required" })}
              />
            )}
            <Form.Text className="text-danger">{errors?.filename?.message}</Form.Text>
          </Form.Group>
          <Form.Group controlId="useEx">
            <Form.Check type="switch" id="useEx" label="Use example GWAS data" {...register("useEx")} />
          </Form.Group>

          {filename.length > 0 && (
            <div>
              <Form.Group controlId="columns.chromosome" className="mb-3">
                <Form.Label>Chromosome Column</Form.Label>
                <Form.Select {...register("columns.chromosome", { required: "Chromosome column is required" })}>
                  <option value="" disabled>
                    Select...
                  </option>
                  {columnOptions.map((e, i) => (
                    <option key={e + i + "chr"} value={e}>
                      {e}
                    </option>
                  ))}
                </Form.Select>
                <Form.Text className="text-danger">{errors?.columns?.chromosome?.message}</Form.Text>
              </Form.Group>
              <Form.Group controlId="columns.position" className="mb-3">
                <Form.Label>Position Column</Form.Label>
                <Form.Select {...register("columns.position", { required: "Position column is required" })}>
                  <option value="" disabled>
                    Select...
                  </option>
                  {columnOptions.map((e, i) => (
                    <option key={e + i + "pos"} value={e}>
                      {e}
                    </option>
                  ))}
                </Form.Select>
                <Form.Text className="text-danger">{errors?.columns?.position?.message}</Form.Text>
              </Form.Group>
              <Form.Group controlId="columns.pvalue" className="mb-3">
                <Form.Label>P-Value</Form.Label>
                <Form.Select {...register("columns.pvalue", { required: "P-value column is required" })}>
                  <option value="" disabled>
                    Select...
                  </option>
                  {columnOptions.map((e, i) => (
                    <option key={e + i + "pval"} value={e}>
                      {e}
                    </option>
                  ))}
                </Form.Select>
                <Form.Text className="text-danger">{errors?.columns?.pvalue?.message}</Form.Text>
              </Form.Group>
            </div>
          )}
        </Col>
        <Col sm={3}>
          <Form.Group controlId="calculateRegion" className="mb-3">
            <Form.Label>Allele</Form.Label>
            <Form.Select {...register("calculateRegion", { required: "Allele is required" })}>
              <option value="" disabled>
                Select...
              </option>
              <option value="gene">Gene</option>
              <option value="region">Region</option>
              <option value="variant">Variant</option>
            </Form.Select>
            <Form.Text className="text-danger">{errors?.calculateRegion?.message}</Form.Text>
          </Form.Group>
          {calculateRegion === "gene" && (
            <div>
              <div>
                <Form.Group controlId="gene.name" className="mb-3">
                  <Form.Label>Gene name</Form.Label>
                  <Form.Control
                    {...register("gene.name", {
                      required: "Gene name is required",
                      pattern: { value: /^[A-Za-z0-9-]+$/, message: "Invalid gene name" },
                    })}
                    placeholder="Gene name"
                  />
                  <Form.Text className="text-danger">{errors?.gene?.name?.message}</Form.Text>
                </Form.Group>
                <Form.Group controlId="gene.basepair" className="mb-3">
                  <Form.Label>Base pair window</Form.Label>
                  <div className="d-flex align-items-center">
                    ±&nbsp;
                    <Form.Control
                      type="number"
                      {...register("gene.basepair", {
                        required: "Base pair window is required",
                        pattern: { value: /^\d+$/, message: "Invalid base pair window" },
                      })}
                      placeholder="100000"
                    />
                  </div>
                  <Form.Text className="text-danger">{errors?.gene?.basepair?.message}</Form.Text>
                </Form.Group>
                <Form.Group controlId="gene.index" className="mb-3">
                  <Form.Label>Index RSID</Form.Label>
                  <Form.Control
                    {...register("gene.index", {
                      pattern: { value: /^rs\d+$/, message: "Invalid RSID" },
                    })}
                    placeholder="(optional)"
                  />
                  <Form.Text className="text-danger">{errors?.gene?.index?.message}</Form.Text>
                </Form.Group>
              </div>
            </div>
          )}
          {calculateRegion === "region" && (
            <div>
              <Form.Group controlId="region.start" className="mb-3">
                <Form.Label>Region Start</Form.Label>
                <Form.Control
                  {...register("region.start", {
                    required: "Region start is required",
                    pattern: { value: /^(chr)?(\d{1,2}|[xyXY]):\d+$/, message: "Invalid region start" },
                  })}
                  placeholder="Start Coord (chr1:50000 or 1:50000)"
                />
                <Form.Text className="text-danger">{errors?.region?.start?.message}</Form.Text>
              </Form.Group>
              <Form.Group controlId="region.end" className="mb-3">
                <Form.Label>Region End</Form.Label>
                <Form.Control
                  {...register("region.end", {
                    required: "Region end is required",
                    pattern: { value: /^(chr)?(\d{1,2}|[xyXY]):\d+$/, message: "Invalid region end" },
                  })}
                  placeholder="End Coord (chr1:50000 or 1:50000)"
                />
                <Form.Text className="text-danger">{errors?.region?.end?.message}</Form.Text>
              </Form.Group>
              <Form.Group controlId="region.index" className="mb-3">
                <Form.Label>Index RSID</Form.Label>
                <Form.Control
                  {...register("region.index", { pattern: { value: /^rs\d+$/, message: "Invalid RSID" } })}
                  placeholder="(optional)"
                />
                <Form.Text className="text-danger">{errors?.region?.index?.message}</Form.Text>
              </Form.Group>
            </div>
          )}
          {calculateRegion === "variant" && (
            <div>
              <Form.Group controlId="variant.index" className="mb-3">
                <Form.Label>Variant RSID</Form.Label>
                <Form.Control
                  {...register("variant.index", {
                    required: "Variant RSID is required",
                    pattern: { value: /^rs\d+$/, message: "Invalid RSID" },
                  })}
                  placeholder="Variant RSID"
                />
                <Form.Text className="text-danger">{errors?.variant?.index?.message}</Form.Text>
              </Form.Group>
              <Form.Group controlId="variant.basepair" className="mb-3">
                <Form.Label>Base pair window</Form.Label>
                <div className="d-flex align-items-center">
                  ±&nbsp;
                  <Form.Control
                    type="number"
                    {...register("variant.basepair", {
                      required: "Base pair window is required",
                      pattern: { value: /^\d+$/, message: "Invalid base pair window" },
                    })}
                  />
                </div>
                <Form.Text className="text-danger">{errors?.variant?.basepair?.message}</Form.Text>
              </Form.Group>
            </div>
          )}
        </Col>
        <Col sm={3}>
          <Form.Group controlId="pop" className="mb-3">
            <Form.Label>Population</Form.Label>
            <PopSelect name="pop" control={control} rules={{ required: "Population is required" }} />
            <Form.Text className="text-danger">{errors?.pop?.message}</Form.Text>
          </Form.Group>
          <Form.Group controlId="dprime" className="mb-3">
            <Form.Label>LD measure:</Form.Label>
            <ButtonGroup className="ms-3">
              <ToggleButton
                id="radio-r2"
                type="radio"
                variant="outline-primary"
                {...register("dprime")}
                title="Select R-squared attribute"
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
                title="Select D-prime attribute"
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
                title="Collapse transcripts"
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
                title="Show transcripts"
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
                title="Show ForgeDB annotation"
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
                title="Show RegulomeDB annotation"
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
                title="Hide annotation"
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
              Calculate
            </Button>
          </div>
        </Col>
      </Row>
      {submitForm.isPending && <CalculateLoading />}
    </Form>
  );
}
