"use client";
import { useForm } from "react-hook-form";
import { Row, Col, Form, Button, ButtonGroup, ToggleButton, Alert } from "react-bootstrap";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter, usePathname } from "next/navigation";
import { ldproxy } from "@/services/queries";
import PopSelect, { getSelectedPopulationGroups, PopOption } from "@/components/select/pop-select";
import CalculateLoading from "@/components/calculateLoading";
import { useStore } from "@/store";
import './style.css';

export interface FormData {
  var: string;
  pop: PopOption[];
  reference: string;
  genome_build: "grch37" | "grch38" | "grch38_high_coverage";
  r2_d: string;
  window: string;
  collapseTranscript: boolean;
  annotate: "forge" | "regulome" | "no";
}

export default function LdProxyForm() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const pathname = usePathname();
  const { genome_build } = useStore((state) => state);

  const defaultForm: FormData = {
    var: "",
    pop: [],
    reference: "",
    genome_build: "grch37",
    r2_d: "r2",
    window: "500000",
    collapseTranscript: true,
    annotate: "forge",
  };
  const {
    control,
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors },
  } = useForm({
    defaultValues: defaultForm,
  });

  const submitForm = useMutation<any, unknown, any>({
    mutationFn: (params: any) => ldproxy(params),
    onSuccess: (_data, variables) => {
      if (variables && variables.reference) {
        router.push(`${pathname}?ref=${variables.reference}`);
      }
    },
  });

  async function onSubmit(data: any) {
    const reference = Math.floor(Math.random() * (99999 - 10000 + 1)).toString();
    const formData = {
      ...data,
      reference,
      genome_build,
      pop: getSelectedPopulationGroups(data.pop),
    };
    queryClient.setQueryData(["ldproxy-form-data", reference], formData);
    router.push(`${pathname}`);
    submitForm.mutate(formData);
  }

  function onReset(event: any): void {
    event.preventDefault();
    router.push("/ldproxy");
    reset(defaultForm);
    queryClient.invalidateQueries();
  }

  return (
    <Form id="ldproxy-form" onSubmit={handleSubmit(onSubmit)} onReset={onReset} noValidate>
      <Row>
        <Col sm={2}>
          <Form.Group controlId="var">
            <Form.Label>Variant</Form.Label>
            <Form.Control
              {...register("var", { 
                required: "This field is required",
                pattern: {
                  value: /^(rs\d+|\d+:\d+)$/,
                  message: "Please match the requested format. rs followed by 1 or more digits (ex. rs12345) or CHR:POS, no spaces permitted"
                }
              })} 
              title="rs followed by 1 or more digits (ex. rs12345) or CHR:POS, no spaces permitted"
              placeholder="Variant RSID or CHR:POS"
            />
            <Form.Text className="text-danger">{errors?.var?.message}</Form.Text>
          </Form.Group>
        </Col>

        <Col sm={3}>
          <Form.Group controlId="pop" className="mb-3">
            <Form.Label>Population</Form.Label>
            <PopSelect name="pop" control={control} rules={{ required: "Population is required" }} />
            <Form.Text className="text-danger">{errors?.pop?.message}</Form.Text>
          </Form.Group>
        </Col>
        <Col sm={"auto"}>
          <Form.Group controlId="r2_d" className="mb-3">
            <Form.Label className="d-block">LD measure</Form.Label>
            <ButtonGroup className="ms-1">
              <ToggleButton
                id="radio-r2"
                type="radio"
                variant="outline-primary"
                {...register("r2_d")}
                title="Select pairwise value"
                value="r2"
                checked={watch("r2_d") === "r2"}
                onChange={() => {
                  setValue("r2_d", "r2");
                }}>
                R<sup>2</sup>
              </ToggleButton>
              <ToggleButton
                id="radio-r2_d"
                type="radio"
                variant="outline-primary"
                {...register("r2_d")}
                title="Select pairwise value"
                value="d"
                checked={watch("r2_d") === "d"}
                onChange={() => {
                  setValue("r2_d", "d");
                }}>
                D&#39;
              </ToggleButton>
            </ButtonGroup>
          </Form.Group>
          <Form.Group controlId="collapseTranscript" className="mb-3">
            <Form.Label className="d-block">Collapse transcripts</Form.Label>
            <ButtonGroup className="ms-1">
              <ToggleButton
                id="radio-transcript-yes"
                type="radio"
                variant="outline-primary"
                {...register("collapseTranscript")}
                title="Collapse transcripts"
                value={"true"}
                checked={!!watch("collapseTranscript")}
                onChange={() => {
                  setValue("collapseTranscript", true);
                }}>
                Yes
              </ToggleButton>
              <ToggleButton
                id="radio-transcript-no"
                type="radio"
                variant="outline-primary"
                {...register("collapseTranscript")}
                title="Show transcripts"
                value={"false"}
                checked={!watch("collapseTranscript")}
                onChange={() => {
                  setValue("collapseTranscript", false);
                }}>
                No
              </ToggleButton>
            </ButtonGroup>
          </Form.Group>
          <Form.Group controlId="annotate" className="mb-3">
            <Form.Label className="d-block">Annotation</Form.Label>
            <ButtonGroup className="ms-1">
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
        <Col>
          <Form.Group controlId="window" className="mb-3">
            <Form.Label style={{ whiteSpace: "nowrap" }}>Base pair window</Form.Label>
            <div className="d-flex align-items-center" >
              ±&nbsp;
              <Form.Control
                  type="number"
                  {...register("window", {
                    required: "Base pair window is required",
                    valueAsNumber: true,
                    min: {
                      value: 0,
                      message: "Minimum value is 0"
                    },
                    max: {
                      value: 1000000,
                      message: "Max value is 1000000"
                    },
                    validate: {
                      isInteger: (value) => {
                        return Number.isInteger(value) || "Must be a whole number";
                      }
                    }
                  })}
                  title="Value must be a number between 0 and 1,000,000"
                />
            </div>
            <Form.Text className="text-danger">{errors?.window?.message}</Form.Text>
          </Form.Group>
        </Col>
        <Col />
        <Col sm={2}>
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
      {submitForm.isError && (
        <Alert variant="danger" className="mt-3">
          <p>Error: {submitForm.error instanceof Error ? submitForm.error.message : "An unknown error occurred."}</p>
        </Alert>
      )}
    </Form>
  );
}
