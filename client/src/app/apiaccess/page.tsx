"use client";
import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { Container, Row, Col, Form, Button, Alert, Modal, Spinner } from "react-bootstrap";
import Image from "next/image";

const BASE_URL =
  "https://" + process.env.NEXT_PUBLIC_BASE_URL || (typeof window !== "undefined" ? window.location.origin : "");

const API_EXAMPLES = [
  {
    name: "LDexpress",
    link: "/help#LDexpress",
    code: [
      `curl -k -X GET '${BASE_URL}/LDlinkRest/ldexpressget?snps=rs3%0Ars4&pop=YRI&tissues=Adipose_Subcutaneous%2BAdipose_Visceral_Omentum&r2_d=r2&r2_d_threshold=0.1&p_threshold=0.1&window=500000&genome_build=grch37&token=faketoken123'`,
      `curl -k -H "Content-Type: application/json" -X POST -d '{"snps": "rs3\\nrs4", "pop": "YRI+CEU", "tissues": "Adipose_Subcutaneous+Adipose_Visceral_Omentum", "r2_d": "r2", "r2_d_threshold": "0.1", "p_threshold": "0.1", "window": "500000", "genome_build": "grch37"}' '${BASE_URL}/LDlinkRest/ldexpress?token=faketoken123'`,
    ],
  },
  {
    name: "LDhap",
    link: "/help#LDhap",
    code: `curl -k -X GET '${BASE_URL}/LDlinkRest/ldhap?snps=rs3%0Ars4&pop=ALL&genome_build=grch38&token=faketoken123'`,
  },
  {
    name: "LDmatrix",
    link: "/help#LDmatrix",
    code: [
      `curl -k -X GET '${BASE_URL}/LDlinkRest/ldmatrix?snps=rs3%0Ars4%0Ars148890987&pop=CEU&r2_d=d&genome_build=grch38_high_coverage&token=faketoken123'`,
      `curl -k -H "Content-Type: application/json" -X POST -d '{"snps": "rs3\\nrs4", "pop": "CEU","r2_d": "d", "genome_build": "grch37"}' '${BASE_URL}/LDlinkRest/ldmatrix?token=faketoken123'`,
    ],
    notes: ["GET requests can support up to 300 SNPs.", "POST requests can support up to 2,500 SNPs."],
  },
  {
    name: "LDpair",
    link: "/help#LDpair",
    code: [
      `curl -k -X GET '${BASE_URL}/LDlinkRest/ldpair?var1=rs3&var2=rs4&pop=CEU%2BYRI%2BCHB&genome_build=grch37&json_out=false&token=faketoken123'`,
      `curl -k -H "Content-Type: application/json" -X POST -d '{"snp_pairs": [["rs3", "rs4"], ["rs7837688", "rs4242384"]], "pop": "CEU+YRI+CHB","genome_build": "grch37", "json_out": true}' '${BASE_URL}/LDlinkRest/ldpair?token=faketoken123'`,
    ],
    notes: [
      "GET requests only support 1 SNP pair.",
      "POST requests can support up to 10 SNP pairs. If more than 1 SNP pair is provided, a JSON response will always be returned.",
    ],
  },
  {
    name: "LDpop",
    link: "/help#LDpop",
    code: `curl -k -X GET '${BASE_URL}/LDlinkRest/ldpop?var1=rs3&var2=rs4&pop=CEU%2BYRI%2BCHB&r2_d=r2&genome_build=grch37&token=faketoken123'`,
  },
  {
    name: "LDproxy",
    link: "/help#LDproxy",
    code: `curl -k -X GET '${BASE_URL}/LDlinkRest/ldproxy?var=rs3&pop=MXL&r2_d=r2&window=500000&genome_build=grch37&token=faketoken123'`,
  },
  {
    name: "LDtrait",
    link: "/help#LDtrait",
    code: [
      `curl -k -X GET '${BASE_URL}/LDlinkRest/ldtraitget?snps=rs3&pop=YRI&r2_d=r2&r2_d_threshold=0.1&window=500000&genome_build=grch37&token=faketoken123'`,
      `curl -k -H "Content-Type: application/json" -X POST -d '{"snps": "rs3\\nrs4", "pop": "YRI", "r2_d": "r2", "r2_d_threshold": "0.1", "window": "500000", "genome_build": "grch37"}' '${BASE_URL}/LDlinkRest/ldtrait?token=faketoken123'`,
    ],
  },
  {
    name: "SNPchip",
    link: "/help#SNPchip",
    code: `curl -k -H "Content-Type: application/json" -X POST -d '{"snps": "rs3\\nrs4\\nrs17795812", "platforms":"A_10X+A_250N+A_250S+A_50H+A_50X+A_AFR+A_ASI+A_CHB2+A_DMETplus+A_EAS+A_EUR+A_Exome1A+A_Exome319+A_Hu+A_Hu-CHB+A_LAT+A_Onco+A_OncoCNV+A_SNP5.0+A_SNP6.0+I_100+I_1M+I_1M-D+I_240S+I_300+I_300-D+I_550v1+I_550v3+I_610-Q+I_650Y+I_660W-Q+I_CNV-12+I_CNV370-D+I_CNV370-Q+I_CVD+I_CardioMetab+I_Core-12+I_CoreE-12v1+I_CoreE-12v1.1+I_CoreE-24v1+I_CoreE-24v1.1+I_Cyto-12v2+I_Cyto-12v2.1+I_Cyto-12v2.1f+I_Cyto850+I_Exome-12+I_Exon510S+I_Immuno-24v1+I_Immuno-24v2+I_Linkage-12+I_Linkage-24+I_ME-Global-8+I_NS-12+I_O1-Q+I_O1S-8+I_O2.5-4+I_O2.5-8+I_O2.5E-8v1+I_O2.5E-8v1.1+I_O2.5E-8v1.2+I_O2.5S-8+I_O5-4+I_O5E-4+I_OE-12+I_OE-12f+I_OE-24+I_OEE-8v1+I_OEE-8v1.1+I_OEE-8v1.2+I_OEE-8v1.3+I_OZH-8v1+I_OZH-8v1.1+I_OZH-8v1.2+I_OncoArray+I_Psyc-24v1+I_Psyc-24v1.1+I_GDA-C+I_GSA-v3C", "genome_build": "grch37"}' '${BASE_URL}/LDlinkRest/snpchip?token=faketoken123'`,
  },
  {
    name: "SNPclip",
    link: "/help#SNPclip",
    code: `curl -k -H "Content-Type: application/json" -X POST -d '{"snps": "rs3\\nrs4", "pop": "YRI", "r2_threshold": "0.1", "maf_threshold": "0.01", "genome_build": "grch37"}' '${BASE_URL}/LDlinkRest/snpclip?token=faketoken123'`,
  },
];

const FORM_FIELDS = [
  {
    name: "firstname",
    label: "First name",
    type: "text",
    placeholder: "First name",
    validation: { required: "First name is required" },
  },
  {
    name: "lastname",
    label: "Last name",
    type: "text",
    placeholder: "Last name",
    validation: { required: "Last name is required" },
  },
  {
    name: "email",
    label: "Email",
    type: "email",
    placeholder: "Email",
    validation: {
      required: "Email is required",
      validate: (value: string) => {
        if (!value.includes("@")) {
          return `Please include an '@' in the email address. ${value} is missing an '@'.`;
        }
        const atIndex = value.indexOf("@");
        if (atIndex === 0) {
          return `Please enter a part followed by '@'. ${value} is incomplete.`;
        }
        if (atIndex === value.length - 1) {
          return `Please enter a part following '@'. ${value} is incomplete.`;
        }
        const emailRegex = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)+$/;
        if (!emailRegex.test(value)) {
          return "Please enter a properly formatted email address (e.g., name@example.com).";
        }

        return true;
      },
    },
  },
  {
    name: "institution",
    label: "Institution",
    type: "text",
    placeholder: "Institution",
    validation: { required: "Institution is required" },
  },
];

export default function ApiAccessPage() {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [modal, setModal] = useState<{ show: boolean; type: "success" | "error"; email: string; message: string }>({
    show: false,
    type: "success",
    email: "",
    message: "",
  });

  const onSubmit = async (data: any) => {
    setError("");
    setLoading(true);

    try {
      const query = new URLSearchParams({ ...data, reference: "" });
      const res = await fetch(`/LDlinkRestWeb/apiaccess/register_web?${query}`);

      if (!res.ok) {
        throw new Error((await res.text()) || "Registration failed.");
      }

      const result = await res.json();
      const isError = result.registered === false;

      setModal({
        show: true,
        type: isError ? "error" : "success",
        email: result.email || data.email,
        message: result.message || "Registration Successful",
      });
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  const handleModalClose = () => {
    setModal((prev) => ({ ...prev, show: false }));
    reset();
  };

  const renderFormField = (field: (typeof FORM_FIELDS)[0], colProps?: any) => (
    <Col {...colProps} key={field.name}>
      <Form.Group controlId={`apiaccess-${field.name}`} className="mb-3">
        <Form.Label>
          {field.label}
          <span style={{ color: "red" }}>*</span>
        </Form.Label>
        <Form.Control
          type={field.type}
          placeholder={field.placeholder}
          {...register(field.name, field.validation)}
          isInvalid={!!errors[field.name]}
        />
        <Form.Text className="text-danger">{errors[field.name]?.message as string}</Form.Text>
      </Form.Group>
    </Col>
  );

  const renderApiExample = (example: (typeof API_EXAMPLES)[0]) => (
    <div key={example.name}>
      <p>
        <a href={example.link}>{example.name}</a>
      </p>
      {Array.isArray(example.code) ? (
        example.code.map((code, index) => (
          <div key={index}>
            <pre className="apiaccess-examples">{code}</pre>
            {example.notes?.[index] && (
              <p>
                <i>Note: {example.notes[index]}</i>
              </p>
            )}
          </div>
        ))
      ) : (
        <pre className="apiaccess-examples">{example.code}</pre>
      )}
    </div>
  );

  return (
    <Container className="py-4 tab-content mb-0">
      <div className="not-home">
        <div className="text-center">
          <h1>
            <Image
              src="/images/LDlink_logo_small_clear.png"
              alt="LDlink"
              style={{ verticalAlign: "bottom" }}
              width={91}
              height={36}
            />{" "}
            API Access
          </h1>
        </div>

        <p>
          LDlink modules are also accessible via command line from a terminal. This programmatic access facilitates
          researchers who are interested in performing batch queries. The syntax is similar to the web address link
          created for queries on the webpage. Generally text output is returned that is the same as the file a user
          would download from the online site. Please register below for an access token required for your API call.
          Once registered, your access token will be emailed to you.
        </p>

        <Row className="justify-content-center">
          <Col sm={7} className="ldlinkr_ad">
            <i>
              Interested in accessing LDlink&apos;s API using R? <br />
              Check out the new LDlinkR package now available on{" "}
              <a
                href="https://cran.r-project.org/web/packages/LDlinkR/index.html"
                title="LDlinkR CRAN"
                target="_blank"
                rel="noopener noreferrer">
                CRAN
              </a>
              .
            </i>
          </Col>
        </Row>

        <hr />

        <Row className="justify-content-center">
          <Col md={8}>
            <Form id="apiaccessForm" onSubmit={handleSubmit(onSubmit)} noValidate>
              <Row>
                {renderFormField(FORM_FIELDS[0], { sm: 6 })}
                {renderFormField(FORM_FIELDS[1], { sm: 6 })}
              </Row>
              {renderFormField(FORM_FIELDS[2])}
              {renderFormField(FORM_FIELDS[3])}

              <div className="mb-3">
                <Button type="submit" className="btn btn-primary calculate me-2" disabled={loading || isSubmitting}>
                  Register
                </Button>
                <Button
                  type="reset"
                  variant="outline-danger"
                  className="me-1"
                  disabled={loading || isSubmitting}
                  onClick={() => reset()}>
                  Reset
                </Button>
              </div>
            </Form>

            {loading && (
              <div className="text-center my-3">
                <Spinner animation="border" role="status" />
                <span className="visually-hidden">Loading...</span>
              </div>
            )}

            {error && (
              <Alert variant="danger" className="mt-3">
                {error}
              </Alert>
            )}

            <Alert className="mt-3 alert-api">
              <b>Important:</b> API access is limited to sequential requests only. Please wait until calculation results
              are returned before making another request. Contact{" "}
              <a href="mailto:NCILDlinkWebAdmin@mail.nih.gov?subject=LDlink" target="_top" title="Support">
                support
              </a>{" "}
              if you plan to make large volumes of API requests.
            </Alert>
          </Col>
        </Row>

        <hr />

        <p>
          Examples of command line arguments are listed below for each module. Replace the example token in{" "}
          <code>token=faketoken123</code> with your own registered token.
        </p>

        <div>
          {API_EXAMPLES.map(renderApiExample)}
          <p>
            <strong>Note</strong>: <a href="/help#LDassoc">LDassoc</a> is not currently accessible via programmatic
            access.
          </p>
        </div>

        <Modal show={modal.show} onHide={handleModalClose} centered backdrop="static">
          <div
            className="modal-content"
            style={{
              borderStyle: "solid",
              borderWidth: 3,
              borderColor: modal.type === "success" ? "#D6E9C6" : "#FFEEBA",
            }}>
            <div
              className="modal-header"
              style={{
                color: modal.type === "success" ? "#3C763D" : "#856404",
                backgroundColor: modal.type === "success" ? "#DFF0D8" : "#FFF3CD",
              }}>
              <h3 className="modal-title apiaccess">{modal.message}</h3>
            </div>
            <div className="modal-body" style={{ textAlign: "center" }}>
              {modal.type === "error" ? (
                <span style={{ color: "#a94442", fontWeight: "bold" }}>
                  An error occurred during registration. Try again later. Contact us if you continue to experience
                  issues.
                </span>
              ) : (
                <>
                  Your API token has been sent to the email:{" "}
                  <span className="apiaccess-user-email" style={{ fontWeight: "bold" }}>
                    {modal.email}
                  </span>
                </>
              )}
            </div>
            <div className="modal-footer">
              <Button className="btn btn-primary apiaccess-done" onClick={handleModalClose}>
                Done
              </Button>
            </div>
          </div>
        </Modal>
      </div>
    </Container>
  );
}
