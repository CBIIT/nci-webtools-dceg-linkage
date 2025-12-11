
  // ...existing code...
"use client";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { Row, Col, Form, Button, ButtonGroup, ToggleButton, InputGroup, Alert } from "react-bootstrap";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter, usePathname } from "next/navigation";
import { AxiosError } from "axios";
import { ldtrait } from "@/services/queries";
import PopSelect, { getSelectedPopulationGroups, getOptionsFromPop } from "@/components/select/pop-select";
import CalculateLoading from "@/components/calculateLoading";
import { useStore } from "@/store";
import { parseSnps, parseRateLimitError } from "@/services/utils";
import { FormData, Ldtrait, submitFormData } from "./types";
import MultiSnp from "@/components/form/multiSnp";



// Calculate estimated processing time using same formula as updateLDtrait()
export function calculateEstimatedTime(snps: string, window: string): string {
  if (!snps || !window) return "";

  const snpCount = snps.split("\n").filter((line) => line.trim()).length;
  const windowValue = parseInt(window) || 500000;

  const estimateWindowSizeMultiplier = windowValue / 500000.0;
  const estimateSeconds = Math.round(snpCount * 5 * estimateWindowSizeMultiplier);
  const estimateMinutes = estimateSeconds / 60;

  if (estimateSeconds < 60) {
    return `${estimateSeconds} seconds`;
  } else {
    return `${estimateMinutes.toFixed(2)} minute(s)`;
  }
}

export default function LdtraitForm({ params }: { params: submitFormData }) {
  const router = useRouter();
  const pathname = usePathname();
  const { genome_build } = useStore((state: { genome_build: string }) => state);

  const defaultForm: FormData = {
    snps: "",
    pop: [],
    genome_build: "grch37",
    r2_d: "r2",
    r2_d_threshold: "0.1",
    window: "500000",
    ifContinue: "Continue",
    varFile: "",
    reference: "",
  };

  const {
    control,
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors },
  } = useForm<FormData>({
    defaultValues: defaultForm,
  });

  const varFile = watch("varFile") as string | FileList;
  const snps = watch("snps");
  const window = watch("window");

  // Load form from URL params
  useEffect(() => {
    if (params && Object.keys(params).length > 0) {
      const popArray = getOptionsFromPop(params.pop);
      reset({
        ...params,
        pop: popArray,
        varFile: "",
      });
    }
  }, [params, reset]);

  useEffect(() => {
    if (varFile instanceof FileList && varFile.length > 0) {
      const file = varFile[0];
      const reader = new FileReader();
      reader.onload = (e: ProgressEvent<FileReader>) => {
        const text = e.target?.result as string;
        if (text) {
          setValue("snps", parseSnps(text));
        }
      };
      reader.readAsText(file);
    }
  }, [varFile, setValue, reset]);

  const submitForm = useMutation<Ldtrait, Error, submitFormData>({
    mutationFn: (params: submitFormData) => ldtrait(params),
    onSuccess: (_data, variables) => {
      if (variables && variables.reference) {
        const urlParams = new URLSearchParams({ ...variables });
        router.push(`${pathname}?${urlParams.toString()}`);
      }
    },
  });

  async function onSubmit(form: FormData) {
    const reference = Math.floor(Math.random() * (99999 - 10000 + 1) + 10000).toString();
    const { varFile, ...data } = form;
    const formData: submitFormData = {
      ...data,
      reference,
      genome_build,
      pop: getSelectedPopulationGroups(form.pop),
      ifContinue: "Continue",
    };

    router.push(`${pathname}`);
    submitForm.mutate(formData);
  }

  // Auto-submit if all required params are present in URL
  useEffect(() => {
    if (
      params &&
      params.snps &&
      params.pop &&
      params.genome_build &&
      params.r2_d &&
      params.r2_d_threshold &&
      params.window &&
      params.ifContinue &&
      !params.reference // Only submit if no reference/result yet
    ) {
      const popArray = Array.isArray(params.pop) ? params.pop : [params.pop];
      onSubmit({
        snps: params.snps,
        pop: popArray.filter(Boolean).map((p: any) => typeof p === "string" ? { value: p, label: p } : p),
        genome_build: params.genome_build,
        r2_d: params.r2_d,
        r2_d_threshold: params.r2_d_threshold,
        window: params.window,
        ifContinue: params.ifContinue,
        varFile: "",
        reference: "",
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params]);

  function onReset(event: React.FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    router.push("/ldtrait");
    reset(defaultForm);
    submitForm.reset();
  }

  return (
    <Form id="ldtrait-form" onSubmit={handleSubmit(onSubmit)} onReset={onReset} noValidate>
      <Row>
        <Col s={12} sm={12} md={6} lg={3} xl={2} >
          <MultiSnp name="snps" register={register} errors={errors} />
        </Col>

         <Col s={12} sm={12} md={6} lg={3} xl={2} style={{ minWidth: "200px" }}>
          <Form.Group controlId="varFile" className="mb-3">
            <Form.Label>Upload file with variants</Form.Label>
            <InputGroup>
              {typeof varFile === "string" && varFile !== "" ? (
                <div className="form-control bg-light">{varFile}</div>
              ) : (
                <Form.Control placeholder="Upload" type="file" {...register("varFile")} />
              )}
            </InputGroup>
          </Form.Group>
        </Col>

         <Col s={12} sm={12} md={6} lg={3} xl={2} style={{ minWidth: "200px" }}>
          <Form.Group controlId="pop" className="mb-3">
            <Form.Label>Population</Form.Label>
            <PopSelect name="pop" control={control} rules={{ required: "Population is required" }} />
            <Form.Text className="text-danger">{errors?.pop?.message}</Form.Text>
          </Form.Group>
        </Col>

        <Col s={12} sm={12} md={6} lg={2} xl={2}>
          <Form.Group controlId="r2_d" className="mb-3">
            <Form.Label className="d-block">LD measure</Form.Label>
            <ButtonGroup className="ms-1">
              <ToggleButton
                id="radio-r2"
                type="radio"
                variant="outline-primary"
                {...register("r2_d")}
                title="Select R-squared attribute"
                value="r2"
                checked={watch("r2_d") === "r2"}
                onChange={() => setValue("r2_d", "r2")}>
                R<sup>2</sup>
              </ToggleButton>
              <ToggleButton
                id="radio-d"
                type="radio"
                variant="outline-primary"
                {...register("r2_d")}
                title="Select D-prime attribute"
                value="d"
                checked={watch("r2_d") === "d"}
                onChange={() => setValue("r2_d", "d")}>
                D&#39;
              </ToggleButton>
            </ButtonGroup>
          </Form.Group>
        </Col>
         <Col s={12} sm={12} md={6} lg={3} xl={2}>
          <Form.Group className="mb-3">
            <Form.Label>Thresholds</Form.Label>
            <InputGroup className="mb-2">
              <InputGroup.Text>{watch("r2_d") === "r2" ? "R²" : "D'"}</InputGroup.Text>
              <Form.Control
                type="text"
                {...register("r2_d_threshold", {
                  required: "This field is required",
                  min: {
                    value: 0,
                    message: "Value must be at least 0",
                  },
                  max: {
                    value: 1,
                    message: "Value must be at most 1",
                  },
                  pattern: {
                    value: /^\+?(0(\.[0-9]+)?|1(\.0+)?|\.([0-9]+)?)$/,
                    message: "Value must be between 0 and 1",
                  },
                })}
                title="Threshold must be a number between 0 and 1."
              />
                <Form.Text className="text-danger">{errors?.r2_d_threshold?.message}</Form.Text>
            </InputGroup>
            <Form.Label>Base pair window</Form.Label>
            <InputGroup>
              <InputGroup.Text>±</InputGroup.Text>
              <Form.Control
                type="number"
                {...register("window", {
                  required: "Base pair window is required",
                  min: {
                    value: 0,
                    message: "Value must be at least 0",
                  },
                  max: {
                    value: 1000000,
                    message: "Value must be at most 1,000,000",
                  },
                  pattern: { value: /^\d+$/, message: "Invalid base pair window" },
                })}
                placeholder="500000"
                title="Value must be a number between 0 and 1,000,000"
              />
            </InputGroup>
            <Form.Text className="text-danger">{errors?.window?.message}</Form.Text>
          </Form.Group>
        </Col>
        <Col s={12} sm={12} md={12} lg={3} xl={2} style={{ minWidth: "180px" }}>
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

      {submitForm.isPending && (
        <div className="text-center my-3">
          <CalculateLoading />
          <p className="text-muted">Estimated calculation time: {calculateEstimatedTime(snps, window)}</p>
        </div>
      )}
      {submitForm.isError && (
        <Alert variant="danger" className="mt-3">
          <p>
            {submitForm.error instanceof AxiosError && submitForm.error.response?.status === 429
              ? parseRateLimitError(submitForm.error)
              : submitForm.error instanceof AxiosError
              ? submitForm.error.message
              : "An unknown error occurred."}
          </p>
        </Alert>
      )}
    </Form>
  );
}
