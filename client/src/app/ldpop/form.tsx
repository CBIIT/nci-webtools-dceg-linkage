"use client";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { Row, Col, Form, Button, Alert, ButtonGroup, ToggleButton } from "react-bootstrap";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter, usePathname } from "next/navigation";
import { ldpop } from "@/services/queries";
import PopSelect, { getOptionsFromKeys, getSelectedPopulationGroups } from "@/components/select/pop-select";
import CalculateLoading from "@/components/calculateLoading";
import { useStore } from "@/store";
import { FormData, submitFormData, LdPop } from "./types";
import { rsChrRegex } from "@/services/utils";

export default function LdPopForm({ params }: { params: submitFormData }) {
  const queryClient = useQueryClient();
  const router = useRouter();
  const pathname = usePathname();
  const { genome_build } = useStore((state: { genome_build: string }) => state);

  const defaultForm: FormData = {
    var1: "",
    var2: "",
    pop: [],
    genome_build: "grch37",
    r2_d: "r2",
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

  // load form form url params
  useEffect(() => {
    if (params && Object.keys(params).length > 0) {
      const popArray = getOptionsFromKeys(params.pop);
      reset({ ...params, pop: popArray });
    }
  }, [params, reset]);

  const submitForm = useMutation<LdPop, Error, submitFormData>({
    mutationFn: (params: submitFormData) => ldpop(params),
  });

  async function onSubmit(form: FormData) {
    const reference = Math.floor(Math.random() * (99999 - 10000 + 1)).toString();
    const formData: submitFormData = {
      ...form,
      reference,
      genome_build,
      pop: getSelectedPopulationGroups(form.pop),
    };

    router.push(pathname);
    await submitForm.mutateAsync(formData);
    const paramsObj: Record<string, string> = {
      var1: formData.var1,
      var2: formData.var2,
      pop: formData.pop,
      genome_build: formData.genome_build,
      r2_d: formData.r2_d,
      reference: formData.reference,
    };
    const params = new URLSearchParams(paramsObj).toString();
    router.push(pathname + "?" + params);
  }

  function onReset(event: React.FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    router.push("/ldpop");
    reset(defaultForm);
    queryClient.invalidateQueries({ queryKey: ["ldpop-form-data"] });
    submitForm.reset();
  }

  return (
    <Form id="ldpop-form" onSubmit={handleSubmit(onSubmit)} onReset={onReset} noValidate>
      <Row>
           <Col s={12} sm={12} md={5} lg={2}>
          <Form.Group controlId="var1" className="mb-3" style={{ maxWidth: "230px" }}>
            <Form.Label>Variant 1</Form.Label>
            <Form.Control
              {...register("var1", {
                required: "This field is required",
                pattern: {
                  value: rsChrRegex,
                  message:
                    "Please match the format requested: rs followed by 1 or more digits (ex: rs12345), no spaces permitted - or - chr(0-22, X, Y):##### (ex: chr1:12345)",
                },
              })}
              placeholder="Variant 1 RSID or CHR:POS"
              title="Enter ONE RSID or CHR:POS"
            />
            <Form.Text className="text-danger">{errors?.var1?.message}</Form.Text>
          </Form.Group>
        </Col>
           <Col s={12} sm={12} md={5} lg={2}>
          <Form.Group controlId="var2" className="mb-3" style={{ maxWidth: "230px" }}>
            <Form.Label>Variant 2</Form.Label>
            <Form.Control
              {...register("var2", {
                required: "This field is required",
                pattern: {
                  value: rsChrRegex,
                  message:
                    "Please match the format requested: rs followed by 1 or more digits (ex: rs12345), no spaces permitted - or - chr(0-22, X, Y):##### (ex: chr1:12345)",
                },
              })}
              placeholder="Variant 2 RSID or CHR:POS"
              title="Enter ONE RSID or CHR:POS"
            />
            <Form.Text className="text-danger">{errors?.var2?.message}</Form.Text>
          </Form.Group>
        </Col>
               <Col s={12} sm={12} md={5} lg={3}>
          <Form.Group controlId="pop" className="mb-3">
            <Form.Label>Population</Form.Label>
            <PopSelect name="pop" control={control} rules={{ required: "Population is required" }} />
            <Form.Text className="text-danger">{errors?.pop?.message}</Form.Text>
          </Form.Group>
        </Col>
        <Col s={12} sm={12} md={5} lg={2}>
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
        <Col />
        <Col s={12} sm={12} md={5} lg={2}>
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
