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
  window: number;
  windowUnit: "kb" | "cM";
}

export default function LdScoreForm() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const pathname = usePathname();
  const { genome_build } = useStore((state) => state);

  // Heritability form state
  const heritabilityForm = useForm<FormData>({
    defaultValues: {
      analysis_type: "heritability",
      pop: [],
      window: 0,
      windowUnit: "cM"
    }
  });
  const heritabilityMutation = useMutation({
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
  const onHeritabilitySubmit = async (data: FormData) => {
    const formData = new FormData();
    if (data.file) formData.append("file", data.file);
    formData.append("analysis_type", "heritability");
    formData.append("pop", data.pop[0]?.value || "");
    heritabilityMutation.mutate(formData);
  };
  const onHeritabilityReset = () => {
    heritabilityForm.reset();
  };

  // Genetic correlation form state
  const geneticForm = useForm<FormData>({
    defaultValues: {
      analysis_type: "genetic_correlation",
      pop: [],
      window: 0,
      windowUnit: "cM"
    }
  });
  const geneticMutation = useMutation({
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
  const onGeneticSubmit = async (data: FormData) => {
    const formData = new FormData();
    if (data.file) formData.append("file", data.file);
    if (data.file2) formData.append("file2", data.file2);
    formData.append("analysis_type", "genetic_correlation");
    formData.append("pop", data.pop[0]?.value || "");
    geneticMutation.mutate(formData);
  };
  const onGeneticReset = () => {
    geneticForm.reset();
  };

  // LD calculation form state
  const ldForm = useForm<FormData>({
    defaultValues: {
      analysis_type: "ld_calculation",
      pop: [],
      window: 0,
      windowUnit: "cM"
    }
  });
  const ldMutation = useMutation({
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
  const onLdSubmit = async (data: FormData) => {
    const formData = new FormData();
    if (data.file) formData.append("file", data.file);
    formData.append("analysis_type", "ld_calculation");
    formData.append("pop", data.pop[0]?.value || "");
    formData.append("window", String(data.window));
    formData.append("windowUnit", data.windowUnit);
    ldMutation.mutate(formData);
  };
  const onLdReset = () => {
    ldForm.reset();
  };

  const analysisType = heritabilityForm.watch("analysis_type");

  if (heritabilityMutation.isPending || geneticMutation.isPending || ldMutation.isPending) {
    return <CalculateLoading />;
  }

  return (
    <Tab.Container activeKey={analysisType} onSelect={(key) => heritabilityForm.setValue("analysis_type", key as any)}>
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
          <Form id="ldscore-form-heritability" onSubmit={heritabilityForm.handleSubmit(onHeritabilitySubmit)} onReset={onHeritabilityReset} noValidate>
            <Row>
              <Col sm={3}>
                <Form.Group controlId="file" className="mb-3">
                  <Form.Label>Upload pre-munged GWAS sumstats file</Form.Label>
                  <Form.Control 
                    type="file" 
                    {...heritabilityForm.register("file", { required: "File is required" })}
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
                          heritabilityForm.setValue("analysis_type", "heritability");
                          heritabilityForm.setValue("pop", [{ label: "(ALL) All Populations", value: "ALL" }]);
                        } else {
                          // Clear example data
                          heritabilityForm.setValue("pop", []);
                        }
                      }}
                    />
                  </div>
                  <Form.Text className="text-danger">{heritabilityForm.formState.errors?.file?.message}</Form.Text>
                </Form.Group>
              </Col>

              <Col sm={3}>
                <Form.Group controlId="pop" className="mb-3">
                  <Form.Label>Population</Form.Label>
                  <LdscorePopSelect name="pop" control={heritabilityForm.control} rules={{ required: "Population is required" }} />
                  <Form.Text className="text-danger">{heritabilityForm.formState.errors?.pop?.message}</Form.Text>
                </Form.Group>
              </Col>

              <Col />
              <Col sm={2}>
                <div className="text-end">
                  <Button type="reset" variant="outline-danger" className="me-1">
                    Reset
                  </Button>
                  <Button type="submit" variant="primary" disabled={heritabilityMutation.isPending}>
                    Calculate
                  </Button>
                </div>
              </Col>
            </Row>
          </Form>

          {heritabilityMutation.isError && (
            <Row>
              <Col>
                <Alert variant="danger" className="mt-3">
                  <Alert.Heading>Error</Alert.Heading>
                  <p>Failed to process Heritability calculation. Please check your input and try again.</p>
                </Alert>
              </Col>
            </Row>
          )}
        </Tab.Pane>

        <Tab.Pane eventKey="genetic_correlation">
          <Form id="ldscore-form-genetic-correlation" onSubmit={geneticForm.handleSubmit(onGeneticSubmit)} onReset={onGeneticReset} noValidate>
            <Row>
              <Col sm={3}>
                <Form.Group controlId="file" className="mb-3">
                  <Form.Label>Upload pre-munged GWAS sumstats file</Form.Label>
                  <Form.Control 
                    type="file" 
                    {...geneticForm.register("file", { required: "Trait 1 file is required" })}
                    accept=".txt,.tsv,.csv"
                  />
                  <Form.Text className="text-muted">
                    
                  </Form.Text>
                  <Form.Text className="text-danger">{geneticForm.formState.errors?.file?.message}</Form.Text>
                </Form.Group>
                <Form.Group controlId="file2" className="mb-3">
                  <Form.Control 
                    type="file" 
                    {...geneticForm.register("file2", { required: "Trait 2 file is required" })}
                    accept=".txt,.tsv,.csv"
                  />
                  <Form.Text className="text-muted">
                   
                  </Form.Text>
                  <div className="mt-2">
                    <a href="#" className="text-decoration-none">
                      Click here for sample format
                    </a>
                  </div>
                  <Form.Text className="text-danger">{geneticForm.formState.errors?.file2?.message}</Form.Text>
                </Form.Group>
              </Col>
              <Col sm={1}>
              </Col>
              <Col sm={3}>
                <Form.Group controlId="pop" className="mb-3">
                  <Form.Label>Population</Form.Label>
                  <LdscorePopSelect name="pop" control={geneticForm.control} rules={{ required: "Population is required" }} />
                  <Form.Text className="text-danger">{geneticForm.formState.errors?.pop?.message}</Form.Text>
                </Form.Group>
              </Col>

              <Col />
              <Col sm={3}>
                <div className="text-end">
                  <Button type="reset" variant="outline-danger" className="me-1">
                    Reset
                  </Button>
                  <Button type="submit" variant="primary" disabled={geneticMutation.isPending}>
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
                        geneticForm.setValue("analysis_type", "genetic_correlation");
                        //setValue("pop", [{ label: "(ALL) All Populations", value: "ALL" }]);
                      } else {
                        // Clear example data
                        geneticForm.setValue("pop", []);
                      }
                    }}
                  />
                </div>
              </Col>
            </Row>

            {geneticMutation.isError && (
              <Row>
                <Col>
                  <Alert variant="danger" className="mt-3">
                    <Alert.Heading>Error</Alert.Heading>
                    <p>Failed to process Genetic Correlation calculation. Please check your input and try again.</p>
                  </Alert>
                </Col>
              </Row>
            )}
          </Form>
        </Tab.Pane>

        <Tab.Pane eventKey="ld_calculation">
          <Form id="ldscore-form-ld-calculation" onSubmit={ldForm.handleSubmit(onLdSubmit)} onReset={onLdReset} noValidate>
            <Row>
              <Col sm={3}>
                <Form.Group controlId="file" className="mb-3">
                  <Form.Label> *.bed *.bim *.fam are required</Form.Label>
                  <Form.Control 
                    type="file" 
                    {...ldForm.register("file", { required: "File is required" })}
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
                          ldForm.setValue("analysis_type", "ld_calculation");
                          //setValue("pop", [{ label: "(ALL) All Populations", value: "ALL" }]);
                        } else {
                          // Clear example data
                          ldForm.setValue("pop", []);
                        }
                      }}
                    />
                  </div>
                  <Form.Text className="text-danger">{ldForm.formState.errors?.file?.message}</Form.Text>
                </Form.Group>
              </Col>

              <Col sm={3}>
                <Form.Group controlId="window" className="mb-3">
                  <Form.Label>Window</Form.Label>
                  <div className="d-flex">
                    <Form.Control
                      type="number"
                      {...ldForm.register("window", { required: "Window is required" })}
                      style={{ maxWidth: "120px", marginRight: "8px" }}
                      title="Please enter an integer greater than 0"
                    />
                    <Form.Select
                      {...ldForm.register("windowUnit")}
                      style={{ maxWidth: "80px" }}
                      defaultValue="cM"
                    >
                      <option value="kb">kb</option>
                      <option value="cM">cM</option>
                    </Form.Select>
                  </div>
                  <Form.Text className="text-danger">{ldForm.formState.errors?.window?.message}</Form.Text>
                </Form.Group>
              </Col>

              <Col />
              <Col sm={2}>
                <div className="text-end">
                  <Button type="reset" variant="outline-danger" className="me-1">
                    Reset
                  </Button>
                  <Button type="submit" variant="primary" disabled={ldMutation.isPending}>
                    Calculate
                  </Button>
                </div>
              </Col>
            </Row>
          </Form>

          {ldMutation.isError && (
            <Row>
              <Col>
                <Alert variant="danger" className="mt-3">
                  <Alert.Heading>Error</Alert.Heading>
                  <p>Failed to process LD Score calculation. Please check your input and try again.</p>
                </Alert>
              </Col>
            </Row>
          )}
        </Tab.Pane>
      </Tab.Content>
    </Tab.Container>
  );
}
