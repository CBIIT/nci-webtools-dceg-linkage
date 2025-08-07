"use client";
import { useMemo, useEffect } from "react";
import { useForm, Controller } from "react-hook-form";
import { Row, Col, Form, Button, ButtonGroup, ToggleButton, Alert } from "react-bootstrap";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter, usePathname } from "next/navigation";
import Select from "react-select";
import { ldexpress, ldexpressTissues } from "@/services/queries";
import PopSelect, { getSelectedPopulationGroups } from "@/components/select/pop-select";
import CalculateLoading from "@/components/calculateLoading";
import { useStore } from "@/store";
import { parseSnps, rsChrMultilineRegex } from "@/services/utils";
import { FormData, Ldexpress, LdexpressFormData, Tissue } from "./types";

export default function LDExpressForm() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const pathname = usePathname();
  const { genome_build } = useStore((state) => state);

  const defaultForm: FormData = {
    snps: "",
    pop: [],
    tissues: [],
    r2_d: "r2",
    p_threshold: 0.1,
    r2_d_threshold: 0.1,
    window: 500000,
    genome_build: "grch37",
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

  const ldexpressFile = watch("ldexpressFile") as string | FileList;
  const r2_d = watch("r2_d");

  useEffect(() => {
    if (ldexpressFile instanceof FileList && ldexpressFile.length > 0) {
      const file = ldexpressFile[0];
      const reader = new FileReader();
      reader.onload = (e) => {
        const text = e.target?.result as string;
        if (text) {
          setValue("snps", parseSnps(text));
        }
      };
      reader.readAsText(file);
    }
  }, [ldexpressFile, setValue]);

  const { data: tissues, isFetching } = useQuery({
    queryKey: ["ldexpress_tissues"],
    queryFn: () => ldexpressTissues(),
  });

  const tissueOptions = useMemo(() => {
    const options = tissues
      ? (tissues.tissueInfo as Tissue[]).map((e) => ({ value: e.tissueSiteDetailId, label: e.tissueSiteDetail }))
      : [];
    if (options.length) {
      return [{ value: "all", label: "All Tissues" }, ...options];
    }
    return options;
  }, [tissues]);

  const submitForm = useMutation<Ldexpress, unknown, LdexpressFormData>({
    mutationFn: (params) => ldexpress(params),
    onSuccess: (_data, variables) => {
      if (variables && variables.reference) {
        router.push(`${pathname}?ref=${variables.reference}`);
      }
    },
  });

  async function onSubmit(form: FormData) {
    const reference = Math.floor(Math.random() * (99999 - 10000 + 1)).toString();
    const { ldexpressFile, ...data } = form;
    const formData: LdexpressFormData = {
      ...data,
      reference,
      genome_build,
      window: data.window.toString(),
      pop: getSelectedPopulationGroups(data.pop),
      tissues:
        data.tissues[0].value === "all"
          ? (tissues.tissueInfo as Tissue[]).map((e) => e.tissueSiteDetailId).join("+")
          : data.tissues.map((e) => e.value).join("+"),
    };

    queryClient.setQueryData(["ldexpress-form-data", reference], formData);
    router.push(`${pathname}`);
    submitForm.mutate(formData);
  }

  function onReset(event: React.FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    router.push("/ldexpress");
    reset(defaultForm);
    queryClient.invalidateQueries();
    submitForm.reset();
  }

  return (
    <Form id="ldexpress-form" onSubmit={handleSubmit(onSubmit)} onReset={onReset} noValidate>
      <Row>
        <Col sm="auto" style={{ maxWidth: "300px" }}>
          <Form.Group controlId="snps" className="mb-3" style={{ maxWidth: "230px" }}>
            <Form.Label>RS Numbers or Genomic Coordinates</Form.Label>
            <Form.Control
              as="textarea"
              rows={2}              
              {...register("snps", {
                required: "This field is required",
                pattern: {
                  value: rsChrMultilineRegex,
                  message:
                    "Please match the format requested: rs followed by 1 or more digits (ex: rs12345), no spaces permitted - or - chr(0-22, X, Y):##### (ex: chr1:12345)",
                },
              })}
              title="Enter list of RS numbers or Genomic Coordinates (one per line)"
            />
            <Form.Text className="text-danger">{errors?.snps?.message}</Form.Text>
          </Form.Group>
        </Col>
        <Col sm={2}>
          <Form.Group controlId="ldexpressFile" className="mb-3">
            <Form.Label>Upload file with variants</Form.Label>
            {typeof ldexpressFile === "string" && ldexpressFile !== "" ? (
              <div className="form-control bg-light">{ldexpressFile}</div>
            ) : (
              <Form.Control placeholder="Upload" type="file" {...register("ldexpressFile")} />
            )}
          </Form.Group>
        </Col>

        <Col sm={3}>
          <Form.Group controlId="pop" className="mb-3">
            <Form.Label>Population</Form.Label>
            <PopSelect name="pop" control={control} rules={{ required: "Population is required" }} />
            <Form.Text className="text-danger">{errors?.pop?.message}</Form.Text>
          </Form.Group>
          <Form.Group controlId="tissues" className="mb-3">
            <Form.Label>Tissues</Form.Label>
            <Controller
              name={"tissues"}
              control={control}
              rules={{ required: "Tissue is required" }}
              render={({ field }) => (
                <Select
                  {...field}
                  inputId="tissues"
                  isMulti
                  options={tissueOptions}
                  closeMenuOnSelect={false}
                  className="basic-multi-select"
                  classNamePrefix="select"
                  value={field.value || []}
                  isDisabled={isFetching}
                  onChange={(selected) => {
                    const allTissuesOption = { value: "all", label: "All Tissues" };
                    if (selected.some((s) => s.value === "all") && !field.value.some((s) => s.value === "all")) {
                      field.onChange([allTissuesOption]);
                    } else if (selected.some((s) => s.value === "all") && selected.length > 1) {
                      field.onChange(selected.filter((s) => s.value !== "all"));
                    } else {
                      field.onChange(selected);
                    }
                  }}
                />
              )}
            />
            <Form.Text className="text-danger">{errors?.tissues?.message}</Form.Text>
          </Form.Group>
        </Col>
        <Col sm={"auto"} style={{ maxWidth: "300px" }}>
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
                id="radio-d"
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
        </Col>
        <Col>
          Thresholds
          <Form.Group as={Row} controlId="r2_d_threshold" className="align-items-center mb-2">
            <Col sm="auto" className="pe-0" style={{ maxWidth: "300px" }}>
              <Form.Label style={{ width: "1.8rem" }}>
                {r2_d === "r2" ? (
                  <>
                    R<sup>2</sup>
                  </>
                ) : (
                  <>D&#39;</>
                )}{" "}
                ≥
              </Form.Label>
            </Col>
            <Col>
              <Form.Control
                {...register("r2_d_threshold", {
                  required: "Threshold is required",
                  min: {
                    value: 0,
                    message: "Value must be at least 0",
                  },
                  max: {
                    value: 1,
                    message: "Value must be at most 1",
                  },
                  pattern: {
                    value: /(0(\.[0-9]+)?|1(\.0+)?|\.([0-9]+)?|e-[1-9]+)/,
                    message: "Value must be between 0 and 1. Scientific notation supported (e.g., 1e-5)",
                  },
                })}
                title="Threshold must be a number between 0 and 1.&#013;Scientific notation supported (i.e. 1e-5)."
              />
            </Col>
            <Form.Text className="text-danger">{errors?.r2_d_threshold?.message}</Form.Text>
          </Form.Group>
          <Form.Group as={Row} controlId="p_threshold" className="d-flex align-items-center mb-2">
            <Col sm="auto" className="pe-0" style={{ maxWidth: "300px" }}>
              <Form.Label style={{ width: "1.8rem" }}>P {"<"}</Form.Label>
            </Col>
            <Col>
              <Form.Control
                {...register("p_threshold", {
                  required: "Threshold is required",
                  min: {
                    value: 0,
                    message: "Value must be at least 0",
                  },
                  max: {
                    value: 1,
                    message: "Value must be at most 1",
                  },
                  pattern: {
                    value: /(0(\.[0-9]+)?|1(\.0+)?|\.([0-9]+)?|e-[1-9]+)/,
                    message: "Value must be between 0 and 1. Scientific notation supported (e.g., 1e-5)",
                  },
                })}
                title="Threshold must be a number between 0 and 1.&#013;Scientific notation supported (i.e. 1e-5)."
              />
            </Col>
            <Form.Text className="text-danger">{errors?.p_threshold?.message}</Form.Text>
          </Form.Group>
          <Form.Group controlId="window" className="mb-2">
            <Form.Label>Base pair window</Form.Label>
            <div className="d-flex align-items-center">
              ±&nbsp;
              <Form.Control
                type="number"
                {...register("window", {
                  required: "Base pair window is required",
                  min: { value: 0, message: "Minimum value is 0" },
                  max: { value: 1000000, message: "Max value is 1000000" },
                })}
                placeholder="500000"
                title="Value must be a number between 0 and 1,000,000"
              />
            </div>
            <Form.Text className="text-danger">{errors?.window?.message}</Form.Text>
          </Form.Group>
        </Col>
        <Col>
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
