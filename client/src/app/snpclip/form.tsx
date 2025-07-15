"use client";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { Row, Col, Form, Button } from "react-bootstrap";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter, usePathname } from "next/navigation";
import { ldhap } from "@/services/queries";
import PopSelect from "@/components/select/pop-select";
import CalculateLoading from "@/components/calculateLoading";
import { useStore } from "@/store";
import { parseSnps } from "@/services/utils";
import { FormData, LdhapFormData, Ldhap } from "./types";


export default function SNPClipForm() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const pathname = usePathname();
  const { genome_build } = useStore((state: { genome_build: string }) => state);

  const defaultForm: FormData = {
    snps: "",
    pop: [],
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
  }, [varFile, setValue]);

  const submitForm = useMutation<Ldhap, Error, LdhapFormData>({
    mutationFn: (params: LdhapFormData) => ldhap(params),
    onSuccess: (_data, variables) => {
      if (variables && variables.reference) {
        router.push(`${pathname}?ref=${variables.reference}`);
      }
    },
  });

  async function onSubmit(form: FormData) {
    const reference = Math.floor(Math.random() * (99999 - 10000 + 1)).toString();
    const { varFile, ...data } = form;
    const formData: LdhapFormData = {
      ...data,
      reference,
      genome_build,
      pop: data.pop.map((e) => e.value).join("+"),
    };

    queryClient.setQueryData(["ldhap-form-data", reference], formData);
    submitForm.mutate(formData);
  }

  function onReset(event: React.FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    router.push("/ldhap");
    reset(defaultForm);
    queryClient.invalidateQueries({ queryKey: ["ldhap-form-data"] });
  }

  return (
    <Form id="ldhap-form" onSubmit={handleSubmit(onSubmit)} onReset={onReset} noValidate>
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
                  message: "Invalid SNP or coordinate format, only one per line",
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
    </Form>
  );
}
