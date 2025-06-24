"use client";
import { useForm } from "react-hook-form";
import { Row, Col, Container, Form, Button } from "react-bootstrap";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { upload } from "@/services/queries";
import PopSelect from "@/components/select/pop-select";

export default function LdAssoc() {
  const queryClient = useQueryClient();

  const defaultForm = {
    "pop": "",
    "filename": "",
    "reference": "",
    "columns['chromosome']": "chr",
    "columns['position']": "pos",
    "columns['pvalue']": "p",
    "calculateRegion": "region",
    "gene[name]": "",
    "gene[basepair]": "100000",
    "gene[index]": "",
    "region[start]": "",
    "region[end]": "",
    "region[index]": "",
    "variant[index]": "",
    "variant[basepair]": "500000",
    "genome_build": "grch37",
    "dprime": false,
    "transcript": false,
    "annotate": "forge",
    "useEx": true,
  };
  const { control, register, handleSubmit, reset, watch } = useForm({
    defaultValues: defaultForm,
  });

  const filename = watch("filename");

  const uploadFile = useMutation({
    mutationFn: ({ params, data }: { params: any; data: any }) => upload(params, data),
  });

  const onSubmit = (data: any) => {
    console.log(data);
  };

  function onReset(event: any): void {
    event.preventDefault();
    // router.push("/cansurv", { shallow: false });
    reset(defaultForm);
    // resetStore();
    // queryClient.invalidateQueries();
  }

  return (
    <Container fluid="md">
      <Form onSubmit={handleSubmit(onSubmit)} onReset={onReset}>
        <Row>
          <Col>
            <Form.Group controlId="genome_build" className="mb-3">
              <Form.Label>Genome Build (1000G)</Form.Label>
              <Form.Select {...register("genome_build")}>
                <option value="grch37">GRCh37</option>
                <option value="grch38">GRCh38</option>
                <option value="grch38_high_coverage">GRCh38 High Coverage</option>
              </Form.Select>
            </Form.Group>
          </Col>
        </Row>
        <Row>
          <Col sm={3}>
            <Form.Group controlId="filename" className="mb-3">
              <Form.Label>File</Form.Label>
              <Form.Control type="file" {...register("filename")} />
            </Form.Group>

            <Form.Group controlId="useExample">
              <Form.Check type="switch" id="useExample" label="Use example GWAS data" />
            </Form.Group>

            {filename && (
              <div>
                <Form.Group controlId="reference" className="mb-3">
                  <Form.Label>Reference</Form.Label>
                  <Form.Control type="text" {...register("reference")} />
                </Form.Group>

                <Form.Group controlId="columns.chromosome" className="mb-3">
                  <Form.Label>Chromosome Column</Form.Label>
                  <Form.Control type="text" {...register("columns['chromosome']")} />
                </Form.Group>

                <Form.Group controlId="columns.position" className="mb-3">
                  <Form.Label>Position Column</Form.Label>
                  <Form.Control type="text" {...register("columns['position']")} />
                </Form.Group>
              </div>
            )}
          </Col>
          <Col sm={3}>
            <Form.Group controlId="regionType" className="mb-3">
              <Form.Label>Genome Build (1000G)</Form.Label>
              <Form.Select {...register("genome_build")}>
                <option value="grch37">GRCh37</option>
                <option value="grch38">GRCh38</option>
                <option value="grch38_high_coverage">GRCh38 High Coverage</option>
              </Form.Select>
            </Form.Group>
          </Col>
          <Col sm={3}>
            <Form.Group controlId="pop" className="mb-3">
              <PopSelect name="pop" control={control} />
            </Form.Group>
          </Col>
          <Col sm={3}>
            <div className="text-end">
              <Button type="reset" variant="outline-danger" className="me-1">
                Reset
              </Button>
              <Button type="submit" variant="primary">
                Submit
              </Button>
            </div>
          </Col>
        </Row>
      </Form>
    </Container>
  );
}
