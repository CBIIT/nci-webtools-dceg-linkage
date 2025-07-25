"use client";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { Row, Col, Form, Button, ButtonGroup, ToggleButton, Alert, InputGroup } from "react-bootstrap";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter, usePathname } from "next/navigation";
import { ldtrait } from "@/services/queries";
import PopSelect, { getSelectedPopulationGroups } from "@/components/select/pop-select";
import CalculateLoading from "@/components/calculateLoading";
import { useStore } from "@/store";
import { parseSnps } from "@/services/utils";
import { FormData, LdtraitFormData, Ldtrait } from "./types";

export default function LdtraitForm() {
  const queryClient = useQueryClient();
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
  const r2_d = watch("r2_d");

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
  }, [varFile, setValue]);

  const submitForm = useMutation<Ldtrait, Error, LdtraitFormData>({
    mutationFn: (params: LdtraitFormData) => ldtrait(params),
    onSuccess: (_data, variables) => {
      if (variables && variables.reference) {
        router.push(`${pathname}?ref=${variables.reference}`);
      }
    },
  });

  async function onSubmit(form: FormData) {
    const reference = Math.floor(Math.random() * (99999 - 10000 + 1)).toString();
    const { varFile, ...data } = form;
    const formData: LdtraitFormData = {
      ...data,
      reference,
      genome_build,
      pop: getSelectedPopulationGroups(form.pop),
    };

    queryClient.setQueryData(["ldtrait-form-data", reference], formData);
    router.push(`${pathname}`);
    submitForm.mutate(formData);
  }

  function onReset(event: React.FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    router.push("/ldtrait");
    reset(defaultForm);
    queryClient.invalidateQueries({ queryKey: ["ldtrait-form-data"] });
    submitForm.reset();
  }

  return (
    <Form id="ldtrait-form" onSubmit={handleSubmit(onSubmit)} onReset={onReset} noValidate>
      <Row>
        <Col sm="2">
          <Form.Group controlId="snps" className="mb-3">
            <Form.Label>RS Numbers or Genomic Coordinates</Form.Label>
            <Form.Control
              as="textarea"
              rows={2}
              {...register("snps", {
                required: "This field is required",
                pattern: {
                  value: /^(([ |\t])*[r|R][s|S]\d+([ |\t])*|([ |\t])*[c|C][h|H][r|R][\d|x|X|y|Y]\d?:\d+([ |\t])*)$/m,
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
          <Form.Group controlId="varFile" className="mb-3">
            <Form.Label>File With Variants</Form.Label>
            <InputGroup>
              {typeof varFile === "string" && varFile !== "" ? (
                <div className="form-control bg-light">{varFile}</div>
              ) : (
                <Form.Control placeholder="Upload" type="file" {...register("varFile")} />
              )}
            </InputGroup>
          </Form.Group>
        </Col>

        <Col sm="3">
          <Form.Group controlId="pop" className="mb-3">
            <Form.Label>Population</Form.Label>
            <PopSelect name="pop" control={control} rules={{ required: "Population is required" }} />
            <Form.Text className="text-danger">{errors?.pop?.message}</Form.Text>
          </Form.Group>
        </Col>

        <Col sm="2">
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

          <Form.Group className="mb-3">
            <Form.Label>Thresholds</Form.Label>
            <InputGroup className="mb-2">
              <InputGroup.Text>{watch("r2_d") === "r2" ? "R²" : "D'"}</InputGroup.Text>
              <Form.Control
                type="text"
                {...register("r2_d_threshold", {
                  required: "This field is required",
                  pattern: {
                    value: /^\+?(0(\.[0-9]+)?|1(\.0+)?|\.([0-9]+)?)$/,
                    message: "Value must be between 0 and 1",
                  },
                })}
              />
            </InputGroup>
            <InputGroup>
              <InputGroup.Text>±</InputGroup.Text>
              <Form.Control
                type="number"
                {...register("window", {
                  required: "This field is required",
                  min: {
                    value: 0,
                    message: "Value must be at least 0",
                  },
                  max: {
                    value: 1000000,
                    message: "Value must be at most 1,000,000",
                  },
                })}
              />
              <InputGroup.Text>base pair window</InputGroup.Text>
            </InputGroup>
            <Form.Text className="text-danger">
              {errors?.r2_d_threshold?.message || errors?.window?.message}
            </Form.Text>
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
