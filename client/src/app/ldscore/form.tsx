"use client";
import { useForm } from "react-hook-form";
import { Row, Col, Form, Button, ButtonGroup, ToggleButton, Alert, Nav, Tab } from "react-bootstrap";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter, usePathname } from "next/navigation";
import { ldscore } from "@/services/queries";
import LdscorePopSelect, { LdscorePopOption } from "@/components/select/ldscore-pop-select";
import CalculateLoading from "@/components/calculateLoading";
import { useStore } from "@/store";
import "./style.css";

export interface FormData {
  file?: File;
  file2?: File; // Second file for genetic correlation
  analysis_type: "heritability" | "genetic_correlation" | "ld_calculation";
  pop: LdscorePopOption[];
}

export default function LdScoreForm() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const pathname = usePathname();
  const { genome_build } = useStore((state) => state);

  const defaultForm: FormData = {
    analysis_type: "heritability",
    pop: [],
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

  const mutation = useMutation({
    mutationFn: ldscore,
    onSuccess: (data: any) => {
      if (data?.error) {
        console.error("LDscore calculation failed:", data.error);
        return;
      }
      queryClient.setQueryData(["ldscore", data.id], data);
      router.push(`${pathname}?ref=${data.id}`);
    },
    onError: (error) => {
      console.error("LDscore mutation error:", error);
    },
  });

  const onSubmit = async (data: FormData) => {
    const formData = new FormData();
    
    if (data.file) {
      formData.append("file", data.file);
    }
    
    if (data.file2) {
      formData.append("file2", data.file2);
    }
    
    formData.append("analysis_type", data.analysis_type);
    formData.append("pop", data.pop[0]?.value || "");

    mutation.mutate(formData);
  };

  const onReset = () => {
    reset(defaultForm);
    router.push(pathname);
  };

  const analysisType = watch("analysis_type");

  if (mutation.isPending) {
    return <CalculateLoading />;
  }

  return (
    <Form id="ldscore-form" onSubmit={handleSubmit(onSubmit)} onReset={onReset} noValidate>
      <Tab.Container activeKey={analysisType} onSelect={(key) => setValue("analysis_type", key as any)}>
        <Row>
          <Col sm={12}>
            <Nav variant="tabs" className="mb-3">
              <Nav.Item>
                <Nav.Link eventKey="heritability">Heritability Analysis</Nav.Link>
              </Nav.Item>
              <Nav.Item>
                <Nav.Link eventKey="genetic_correlation">Genetic Correlation</Nav.Link>
              </Nav.Item>
              <Nav.Item>
                <Nav.Link eventKey="ld_calculation">LD Score Calculation</Nav.Link>
              </Nav.Item>
            </Nav>
          </Col>
        </Row>

        <Tab.Content>
          <Tab.Pane eventKey="heritability">
            <Row>
              <Col sm={3}>
                <Form.Group controlId="file" className="mb-3">
                  <Form.Label>Upload pre-munged GWAS sumstats file</Form.Label>
                  <Form.Control 
                    type="file" 
                    {...register("file", { required: "File is required" })}
                    accept=".txt,.tsv,.csv"
                    placeholder="Upload pre-munged GWAS sumstats"
                  />
                  <Form.Text className="text-muted">
                    
                  </Form.Text>
                  <div className="mt-2">
                    <a href="#" className="text-decoration-none">
                      Click here for sample format
                    </a>
                  </div>
                  <div className="mt-2">
                    <Form.Check 
                      type="switch"
                      id="use-example-heritability"
                      label="Use Example Data"
                      onChange={(e) => {
                        if (e.target.checked) {
                          // Load example data for heritability
                          setValue("analysis_type", "heritability");
                          setValue("pop", [{ label: "(ALL) All Populations", value: "ALL" }]);
                        } else {
                          // Clear example data
                          setValue("pop", []);
                        }
                      }}
                    />
                  </div>
                  <Form.Text className="text-danger">{errors?.file?.message}</Form.Text>
                </Form.Group>
              </Col>

              <Col sm={3}>
                <Form.Group controlId="pop" className="mb-3">
                  <Form.Label>Population</Form.Label>
                  <LdscorePopSelect name="pop" control={control} rules={{ required: "Population is required" }} />
                  <Form.Text className="text-danger">{errors?.pop?.message}</Form.Text>
                </Form.Group>
              </Col>

              <Col />
              <Col sm={2}>
                <div className="text-end">
                  <Button type="reset" variant="outline-danger" className="me-1">
                    Reset
                  </Button>
                  <Button type="submit" variant="primary" disabled={mutation.isPending}>
                    Calculate
                  </Button>
                </div>
              </Col>
            </Row>
          </Tab.Pane>

          <Tab.Pane eventKey="genetic_correlation">
            <Row>
              <Col sm={3}>
                <Form.Group controlId="file" className="mb-3">
                  <Form.Label>Upload pre-munged GWAS sumstats file</Form.Label>
                  <Form.Control 
                    type="file" 
                    {...register("file", { required: "Trait 1 file is required" })}
                    accept=".txt,.tsv,.csv"
                  />
                  <Form.Text className="text-muted">
                    
                  </Form.Text>
                  <Form.Text className="text-danger">{errors?.file?.message}</Form.Text>
                </Form.Group>
                <Form.Group controlId="file2" className="mb-3">
                  <Form.Control 
                    type="file" 
                    {...register("file2", { required: "Trait 2 file is required" })}
                    accept=".txt,.tsv,.csv"
                  />
                  <Form.Text className="text-muted">
                   
                  </Form.Text>
                  <div className="mt-2">
                    <a href="#" className="text-decoration-none">
                      Click here for sample format
                    </a>
                  </div>
                  <Form.Text className="text-danger">{errors?.file2?.message}</Form.Text>
                </Form.Group>
              </Col>
              <Col sm={1}>
              </Col>
              <Col sm={3}>
                <Form.Group controlId="pop" className="mb-3">
                  <Form.Label>Population</Form.Label>
                  <LdscorePopSelect name="pop" control={control} rules={{ required: "Population is required" }} />
                  <Form.Text className="text-danger">{errors?.pop?.message}</Form.Text>
                </Form.Group>
              </Col>

              <Col />
              <Col sm={3}>
                <div className="text-end">
                  <Button type="reset" variant="outline-danger" className="me-1">
                    Reset
                  </Button>
                  <Button type="submit" variant="primary" disabled={mutation.isPending}>
                    Calculate
                  </Button>
                </div>
              </Col>
            </Row>

            <Row>
              <Col sm={12}>
                <div className="mb-3">
                  <Form.Check 
                    type="switch"
                    id="use-example-correlation"
                    label="Use Example Data"
                    onChange={(e) => {
                      if (e.target.checked) {
                        // Load example data for genetic correlation
                        setValue("analysis_type", "genetic_correlation");
                        setValue("pop", [{ label: "(ALL) All Populations", value: "ALL" }]);
                      } else {
                        // Clear example data
                        setValue("pop", []);
                      }
                    }}
                  />
                </div>
              </Col>
            </Row>
          </Tab.Pane>

          <Tab.Pane eventKey="ld_calculation">
            <Row>
              <Col sm={3}>
                <Form.Group controlId="file" className="mb-3">
                  <Form.Label> *.bed *.bim *.fam are required</Form.Label>
                  <Form.Control 
                    type="file" 
                    {...register("file", { required: "File is required" })}
                    accept=".txt,.tsv,.csv"
                  />
                  <Form.Text className="text-muted">
                   
                  </Form.Text>
                  <div className="mt-2">
                    <a href="#" className="text-decoration-none">
                      Click here for sample format
                    </a>
                  </div>
                  <div className="mt-2">
                    <Form.Check 
                      type="switch"
                      id="use-example-ld"
                      label="Use Example Data"
                      onChange={(e) => {
                        if (e.target.checked) {
                          // Load example data for LD calculation
                          setValue("analysis_type", "ld_calculation");
                          setValue("pop", [{ label: "(ALL) All Populations", value: "ALL" }]);
                        } else {
                          // Clear example data
                          setValue("pop", []);
                        }
                      }}
                    />
                  </div>
                  <Form.Text className="text-danger">{errors?.file?.message}</Form.Text>
                </Form.Group>
              </Col>

              <Col sm={3}>
                <Form.Group controlId="pop" className="mb-3">
                  <Form.Label>Population</Form.Label>
                  <LdscorePopSelect name="pop" control={control} rules={{ required: "Population is required" }} />
                  <Form.Text className="text-danger">{errors?.pop?.message}</Form.Text>
                </Form.Group>
              </Col>

              <Col />
              <Col sm={2}>
                <div className="text-end">
                  <Button type="reset" variant="outline-danger" className="me-1">
                    Reset
                  </Button>
                  <Button type="submit" variant="primary" disabled={mutation.isPending}>
                    Calculate
                  </Button>
                </div>
              </Col>
            </Row>
          </Tab.Pane>
        </Tab.Content>
      </Tab.Container>

      {mutation.isError && (
        <Row>
          <Col>
            <Alert variant="danger" className="mt-3">
              <Alert.Heading>Error</Alert.Heading>
              <p>Failed to process LDscore calculation. Please check your input and try again.</p>
            </Alert>
          </Col>
        </Row>
      )}
    </Form>
  );
}
