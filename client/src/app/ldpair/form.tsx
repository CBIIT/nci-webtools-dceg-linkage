"use client";
import { useForm } from "react-hook-form";
import { Row, Col, Form, Button, Alert } from "react-bootstrap";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter, usePathname } from "next/navigation";
import { ldpair } from "@/services/queries";
import PopSelect from "@/components/select/pop-select";
import CalculateLoading from "@/components/calculateLoading";
import { useStore } from "@/store";
import { FormData, submitFormData, LdPair } from "./types";

export default function LdPairForm() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const pathname = usePathname();
  const { genome_build } = useStore((state: { genome_build: string }) => state);

  const defaultForm: FormData = {
    var1: "",
    var2: "",
    pop: [],
    genome_build: "grch37",
  };
  const {
    control,
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormData>({
    defaultValues: defaultForm,
  });

  const submitForm = useMutation<LdPair, Error, submitFormData>({
    mutationFn: (params: submitFormData) => ldpair(params),
    onSuccess: (_data, variables) => {
      if (variables && variables.reference) {
        router.push(`${pathname}?ref=${variables.reference}`);
      }
    },
  });

  async function onSubmit(form: FormData) {
    const reference = Math.floor(Math.random() * (99999 - 10000 + 1)).toString();
    const formData: submitFormData = {
      ...form,
      reference,
      genome_build,
      pop: form.pop.map((e) => e.value).join("+"),
    };

    queryClient.setQueryData(["ldpair-form-data", reference], formData);
    submitForm.mutate(formData);
  }

  function onReset(event: React.FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    router.push("/ldpair");
    reset(defaultForm);
    queryClient.invalidateQueries({ queryKey: ["ldpair-form-data"] });
  }

  return (
    <Form id="ldpair-form" onSubmit={handleSubmit(onSubmit)} onReset={onReset} noValidate>
      <Row>
        <Col sm={2}>
          <Form.Group controlId="snps" className="mb-3">
            <Form.Label>Variant 1</Form.Label>
            <Form.Control
              {...register("var1", {
                required: "Required",
                pattern: {
                  value: /^\s*(?:[rR][sS]\d+|[cC][hH][rR](?:[xXyY]|\d+)?(?::\d+))\s*$/,
                  message: "Invalid SNP or coordinate format",
                },
              })}
              placeholder="Variant 1 RSID or CHR:POS"
              title="Enter ONE RSID or CHR:POS"
            />
            <Form.Text className="text-danger">{errors?.var1?.message}</Form.Text>
          </Form.Group>
        </Col>
        <Col sm={2}>
          <Form.Group controlId="snps" className="mb-3">
            <Form.Label>Variant 2</Form.Label>
            <Form.Control
              {...register("var2", {
                required: "Required",
                pattern: {
                  value: /^\s*(?:[rR][sS]\d+|[cC][hH][rR](?:[xXyY]|\d+)?(?::\d+))\s*$/,
                  message: "Invalid SNP or coordinate format",
                },
              })}
              placeholder="Variant 2 RSID or CHR:POS"
              title="Enter ONE RSID or CHR:POS"
            />
            <Form.Text className="text-danger">{errors?.var2?.message}</Form.Text>
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
      {submitForm.isError && (
        <Alert variant="danger" className="mt-3">
          <p>Error: {submitForm.error instanceof Error ? submitForm.error.message : "An unknown error occurred."}</p>
        </Alert>
      )}
    </Form>
  );
}
