"use client";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { Row, Col, Form, Button } from "react-bootstrap";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter, usePathname } from "next/navigation";
import { snpclip } from "@/services/queries";
import CalculateLoading from "@/components/calculateLoading";
import { useStore } from "@/store";
import { parseSnps } from "@/services/utils";
import { FormData, SnpClipData } from "./types";
import PopSelect, { getSelectedPopulationGroups, PopOption } from "@/components/select/pop-select";
import MultiSnp from "@/components/form/multiSnp";

export default function SNPClipForm() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const pathname = usePathname();
  const { genome_build } = useStore((state: { genome_build: string }) => state);

  const defaultForm: FormData = {
    snps: "",
    pop: [],
    r2_threshold: "0.1",
    maf_threshold: "0.01",
    genome_build: "grch37",
    varFile: "",
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

  const submitForm = useMutation<any, Error, SnpClipData>({
    mutationFn: (params: SnpClipData) => snpclip(params),
    onSuccess: (_data, variables) => {
      if (variables && variables.reference) {
        router.push(`${pathname}?ref=${variables.reference}`);
      }
    },
  });

  async function onSubmit(form: FormData) {
    const reference = Math.floor(Math.random() * (99999 - 10000 + 1));
    const { varFile, ...data } = form;
    const formData: SnpClipData = {
      ...data,
      reference,
      genome_build,
      pop: getSelectedPopulationGroups(data.pop),
    };

    queryClient.setQueryData(["snpclip-form-data", reference.toString()], formData);
    submitForm.mutate(formData);
  }

  function onReset(event: React.FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    router.push("/snpclip");
    reset(defaultForm);
    queryClient.invalidateQueries({ queryKey: ["snpclip-form-data"] });
    submitForm.reset();
  }

  return (
    <Form id="snpclip-form" onSubmit={handleSubmit(onSubmit)} onReset={onReset} noValidate>
      <Row>
        <Col sm="auto">
          <MultiSnp name="snps" register={register} errors={errors} />
        </Col>
        <Col sm={2}>
          <Form.Group controlId="varFile" className="mb-3">
            <Form.Label>Upload file with variants</Form.Label>
            {typeof varFile === "string" && varFile !== "" ? (
              <div className="form-control bg-light">{varFile}</div>
            ) : (
              <Form.Control placeholder="Upload" type="file" {...register("varFile")} />
            )}
          </Form.Group>
        </Col>
        <Col sm={3}>
          <Form.Group controlId="pop" className="mb-3">
            <Form.Label>Population</Form.Label>
            <PopSelect name="pop" control={control} rules={{ required: "Population is required" }} />
            <Form.Text className="text-danger">{errors?.pop?.message}</Form.Text>
          </Form.Group>
        </Col>
        <Col sm={2}>
          <div>Thresholds</div>
          <Form.Group controlId="r2_threshold" className="mb-3">
            <Row className="align-items-center">
              <Col sm={3} xs="auto" style={{ maxWidth: "300px" }}>
                <Form.Label className="mb-0">
                  R<sup>2</sup>
                </Form.Label>
              </Col>
              <Col>
                <Form.Control
                  type="number"
                  step="0.01"
                  min="0"
                  max="1"
                  {...register("r2_threshold", {
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
                      message: "Value must be between 0 and 1",
                    },
                  })}
                  title="R2 Threshold must be a number between 0 and 1."
                />
                <Form.Text className="text-danger">{errors?.r2_threshold?.message}</Form.Text>
              </Col>
            </Row>
          </Form.Group>
          <Form.Group controlId="maf_threshold" className="mb-3">
            <Row className="align-items-center">
              <Col sm={3} xs="auto" style={{ maxWidth: "300px" }}>
                <Form.Label className="mb-0">MAF </Form.Label>
              </Col>
              <Col>
                <Form.Control
                  type="number"
                  step="0.01"
                  min="0"
                  max="1"
                  {...register("maf_threshold", {
                    required: "MAF is required",
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
                      message: "Value must be between 0 and 1",
                    },
                  })}
                  title="MAF must be a number between 0 and 1"
                />
                <Form.Text className="text-danger">{errors?.maf_threshold?.message}</Form.Text>
              </Col>
            </Row>
          </Form.Group>
        </Col>

        <Col sm={2} className="d-flex justify-content-end align-items-start ms-auto">
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
