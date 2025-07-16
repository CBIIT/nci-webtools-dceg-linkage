"use client";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { Row, Col, Form, Button, ButtonGroup, ToggleButton, Alert } from "react-bootstrap";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter, usePathname } from "next/navigation";
import { ldmatrix } from "@/services/queries";
import PopSelect, { PopOption } from "@/components/select/pop-select";
import CalculateLoading from "@/components/calculateLoading";
import { useStore } from "@/store";
import { parseSnps } from "@/services/utils";
import { FormData, LdmatrixFormData } from "./types";

export default function LDMatrixForm() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const pathname = usePathname();
  const { genome_build } = useStore((state) => state);

  const defaultForm: FormData = {
    snps: "",
    pop: [],
    reference: "",
    genome_build: "grch37",
    r2_d: "d",
    collapseTranscript: false,
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

  const varFile = watch("varFile") as string | FileList;

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

  const submitForm = useMutation<any, unknown, LdmatrixFormData>({
    mutationFn: (params: any) => ldmatrix(params),
    onSuccess: (_data, variables) => {
      if (variables && variables.reference) {
        router.push(`${pathname}?ref=${variables.reference}`);
      }
    },
  });

  async function onSubmit(data: FormData) {
    const reference = Math.floor(Math.random() * (99999 - 10000 + 1)).toString();
    const formData: LdmatrixFormData = {
      ...data,
      reference,
      genome_build,
      pop: data.pop.map((e: PopOption) => e.value).join("+"),
    };
    queryClient.setQueryData(["ldmatrix-form-data", reference], formData);
    router.push(`${pathname}`);
    submitForm.mutate(formData);
  }

  function onReset(event: any): void {
    event.preventDefault();
    router.push("/ldmatrix");
    reset(defaultForm);
    queryClient.invalidateQueries();
  }

  return (
    <Form id="ldmatrix-form" onSubmit={handleSubmit(onSubmit)} onReset={onReset} noValidate>
      <Row>
        <Col sm="auto">
          <Form.Group controlId="snps" className="mb-3">
            <Form.Label>RS Numbers or Genomic Coordinates</Form.Label>
            <Form.Control
              as="textarea"
              rows={2}
              {...register("snps", {
                required: "snps are required",
                pattern: {
                  value:
                    /^((([rR][sS]\d+)|([cC][hH][rR][\dxXyY]\d?:\d+))(\n((([rR][sS]\d+)|([cC][hH][rR][\dxXyY]\d?:\d+))))*)?$/,
                  message: "Invalid SNP or coordinate format, only one per line. Please match the format requested: rs followed by 1 or more digits (ex: rs12345), no spaces permitted - or - chr(0-22, X, Y):##### (ex: chr1:12345)",
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
            {typeof varFile === "string" && varFile !== "" ? (
              <div className="form-control bg-light">{varFile}</div>
            ) : (
              <Form.Control placeholder="Upload" type="file" {...register("varFile")} />
            )}
          </Form.Group>
        </Col>
        <Col sm="3">
          <Form.Group controlId="pop" className="mb-3">
            <Form.Label>Population</Form.Label>
            <PopSelect name="pop" control={control} rules={{ required: "Population is required" }} />
            <Form.Text className="text-danger">{errors?.pop?.message}</Form.Text>
          </Form.Group>
        </Col>
        <Col sm="auto">
          <Form.Group controlId="collapseTranscript" className="mb-3">
            <Form.Label className="d-block">Collapse transcripts:</Form.Label>
            <ButtonGroup>
              <ToggleButton
                id="radio-transcript-yes"
                type="radio"
                variant="outline-primary"
                {...register("collapseTranscript")}
                title="Collapse transcripts"
                value="true"
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
                value="false"
                checked={!watch("collapseTranscript")}
                onChange={() => {
                  setValue("collapseTranscript", false);
                }}>
                No
              </ToggleButton>
            </ButtonGroup>
          </Form.Group>
          <Form.Group controlId="annotate" className="mb-3">
            <Form.Label className="d-block">Annotation:</Form.Label>
            <ButtonGroup>
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
        <Col />
        <Col sm="2">
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
