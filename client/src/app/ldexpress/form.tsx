"use client";
import { useMemo, useEffect } from "react";
import { useForm, Controller } from "react-hook-form";
import { Row, Col, Form, Button, ButtonGroup, ToggleButton, Alert } from "react-bootstrap";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter, usePathname } from "next/navigation";
import Select from "react-select";
import { ldexpress, ldexpressTissues } from "@/services/queries";
import PopSelect, { getSelectedPopulationGroups,getOptionsFromKeys } from "@/components/select/pop-select";
import CalculateLoading from "@/components/calculateLoading";
import { useStore } from "@/store";
import { parseSnps } from "@/services/utils";
import { FormData, SubmitFormData, Ldexpress, LdexpressFormData, Tissue } from "./types";
import MultiSnp from "@/components/form/multiSnp";

export default function LDExpressForm({ params }: { params: SubmitFormData }) {
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
    ldexpressFile: "",
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

  const { data: tissues, isFetching } = useQuery({
    queryKey: ["ldexpress_tissues"],
    queryFn: () => ldexpressTissues(),
  });

  // Auto-populate and submit form from URL params
  useEffect(() => {
    const hasAllParams = params && params.snps && params.pop && params.tissues && !params.reference;
    if (hasAllParams && tissues?.tissueInfo) {
      // 1. Format population array
      const popArray = Array.isArray(params.pop)
        ? params.pop.map((p: any) => (typeof p === "string" ? { value: p, label: p } : p))
        : [{ value: params.pop, label: params.pop }];

      // 2. Find the correct tissue object from the API response
      const tissueNameFromParam = Array.isArray(params.tissues)
        ? typeof params.tissues[0] === "string"
          ? params.tissues[0]
          : params.tissues[0].label
        : typeof params.tissues === "string"
        ? params.tissues
        : typeof params.tissues === "object" && params.tissues !== null && "label" in params.tissues
        ? (params.tissues as { label: string }).label
        : "";
      const tissueInfo = (tissues.tissueInfo as Tissue[]).find(
        (t) => t.tissueSiteDetail.toLowerCase() === tissueNameFromParam.replace(/_/g, " ").toLowerCase(),
      );

      // 3. Proceed only if a valid tissue was found
      if (tissueInfo) {
        const tissuesArray = [{ value: tissueInfo.tissueSiteDetailId, label: tissueInfo.tissueSiteDetail }];

        // 4. Construct the final form data
        const formData: FormData = {
          ...defaultForm,
          ...params,
          pop: popArray,
          tissues: tissuesArray,
        };

        // 5. Reset the form state and submit
        reset(formData);
        onSubmit(formData);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params, tissues, reset]);

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
  }, [ldexpressFile, setValue, reset]);

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
    <>
      <Form id="ldexpress-form" onSubmit={handleSubmit(onSubmit)} onReset={onReset} noValidate>
      <Row>
        <Col xs={12} sm={6} md={4}lg={4} xl={2}>
          <MultiSnp name="snps" register={register} errors={errors} />
        </Col>
        <Col xs={12} sm={6} md={4} lg={4} xl={2}>
          <Form.Group controlId="ldexpressFile" className="mb-3">
            <Form.Label>Upload file with variants</Form.Label>
            {typeof ldexpressFile === "string" && ldexpressFile !== "" ? (
              <div className="form-control bg-light">{ldexpressFile}</div>
            ) : (
              <Form.Control placeholder="Upload" type="file" {...register("ldexpressFile")} />
            )}
          </Form.Group>
        </Col>

        <Col xs={12} sm={6} md={4} lg={4} xl={2} style={{ minWidth: "200px" }}>
          <Form.Group controlId="pop" className="mb-3">
            <Form.Label>Population</Form.Label>
            <div className="">
              <PopSelect name="pop" control={control} rules={{ required: "Population is required" }} />
            </div>
            <Form.Text className="text-danger">{errors?.pop?.message}</Form.Text>
          </Form.Group>
          <Form.Group controlId="tissues" className="mb-3">
            <Form.Label>Tissues</Form.Label>
            <div className="">
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
            </div>
            <Form.Text className="text-danger">{errors?.tissues?.message}</Form.Text>
          </Form.Group>
        </Col>
        <Col xs={12} sm={6} md={4} lg={4} xl={2} className="ms-0 me-0">
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
        <Col xs={12} sm={6} md={4} lg={4} xl={2} >
         Thresholds
          <Form.Group as={Row} controlId="r2_d_threshold" className="text-nowrap d-flex align-items-center mb-2">
            <Col xs={4} sm={3} md="auto" lg={3} className="pe-0" style={{ maxWidth: "100px" }}>
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
            <Col xs={8} sm={9} md={5} lg={9} className="text-start">
              <Form.Control
                className="text-start"
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
          <Form.Group as={Row} controlId="p_threshold" className="text-nowrap d-flex align-items-center mb-2">
            <Col xs={4} sm={3} md="auto" lg={3} className="pe-0" style={{ maxWidth: "100px" }}>
              <Form.Label style={{ width: "1.8rem" }}>P {"<"}</Form.Label>
            </Col>
            <Col xs={8} sm={9} md={5} lg={9}>
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
              <Col xs={8} sm={9} md={8} lg={12}>
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
            </Col>
          </Form.Group>
        </Col>
        <Col xs={12} sm={6} md={4} lg={4} xl={2} style={{ minWidth: "180px" }}>
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
    </>
  );
}
