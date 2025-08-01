"use client";
import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { Container, Row, Col, Form, Button, Alert, Modal, Spinner } from "react-bootstrap";
import Image from "next/image";

export default function ApiAccessPage() {
  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm();
  const [submitted, setSubmitted] = useState(false);
  const [modalShow, setModalShow] = useState(false);
  const [modalType, setModalType] = useState<"new" | "existing" | "error">("new");
  const [modalEmail, setModalEmail] = useState("");
  const [modalTitle, setModalTitle] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const onSubmit = async (data: any) => {
    setError("");
    setLoading(true);
    const query = new URLSearchParams({
      firstname: data.firstname,
      lastname: data.lastname,
      email: data.email,
      institution: data.institution,
      reference: "",
    });
    try {
      const res = await fetch(
        `/LDlinkRestWeb/apiaccess/register_web?${query.toString()}`
      );
      if (!res.ok) {
        const errText = await res.text();
        setError(errText || "Registration failed.");
        return;
      }
      const result = await res.json();
      setSubmitted(true);
      setModalEmail(result.email || data.email);
      setModalTitle(result.message || "Registration Successful");
      if (result.registered === true && result.blocked === false) {
        setModalType("new");
      } else if (result.registered === false) {
        setModalType("error");
      } else {
        setModalType("existing");
      }
      setModalShow(true);
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    reset();
    setSubmitted(false);
  };

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
          LDlink modules are also accessible via command line from a terminal. This programmatic access facilitates researchers
          who are interested in performing batch queries. The syntax is similar to the web address link created
          for queries on the webpage. Generally text output is returned that is the same as the file a user would
          download from the online site. Please register below for an access token required for your API call. Once registered, your access token will be emailed to you.
        </p>
        <Row className="justify-content-center">
          <Col sm={7} className="ldlinkr_ad">
            <i>
              Interested in accessing LDlink&apos;s API using R? <br />
              Check out the new LDlinkR package now available on{" "}
              <a href="https://cran.r-project.org/web/packages/LDlinkR/index.html" title="LDlinkR CRAN" target="_blank" rel="noopener noreferrer" className="dark-blue">
                CRAN
              </a>.
            </i>
          </Col>
        </Row>
        <hr />
        <Row className="justify-content-center">
          <Col md={8}>
            <Form id="apiaccessForm" onSubmit={handleSubmit(onSubmit)} onReset={handleReset} noValidate>
              <Row>
                <Col sm={6}>
                  <Form.Group controlId="apiaccess-firstname" className="mb-3">
                    <Form.Label>
                      First name<span style={{ color: "red" }}>*</span>
                    </Form.Label>
                    <Form.Control
                      type="text"
                      placeholder="First name"
                      {...register("firstname", { required: "First name is required" })}
                      isInvalid={!!errors.firstname}
                    />
                    <Form.Text className="text-danger">{errors.firstname?.message as string}</Form.Text>
                  </Form.Group>
                </Col>
                <Col sm={6}>
                  <Form.Group controlId="apiaccess-lastname" className="mb-3">
                    <Form.Label>
                      Last name<span style={{ color: "red" }}>*</span>
                    </Form.Label>
                    <Form.Control
                      type="text"
                      placeholder="Last name"
                      {...register("lastname", { required: "Last name is required" })}
                      isInvalid={!!errors.lastname}
                    />
                    <Form.Text className="text-danger">{errors.lastname?.message as string}</Form.Text>
                  </Form.Group>
                </Col>
              </Row>
              <Form.Group controlId="apiaccess-email" className="mb-3">
                <Form.Label>
                  Email<span style={{ color: "red" }}>*</span>
                </Form.Label>
                <Form.Control
                  type="email"
                  placeholder="Email"
                  {...register("email", {
                    required: "Email is required",
                    pattern: {
                      value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                      message: "Enter a valid email address",
                    },
                  })}
                  isInvalid={!!errors.email}
                />
                <Form.Text className="text-danger">{errors.email?.message as string}</Form.Text>
              </Form.Group>
              <Form.Group controlId="apiaccess-institution" className="mb-3">
                <Form.Label>
                  Institution<span style={{ color: "red" }}>*</span>
                </Form.Label>
                <Form.Control
                  type="text"
                  placeholder="Institution"
                  {...register("institution", { required: "Institution is required" })}
                  isInvalid={!!errors.institution}
                />
                <Form.Text className="text-danger">{errors.institution?.message as string}</Form.Text>
              </Form.Group>
              <div className="mb-3">
                <Button type="submit" className="btn btn-primary calculate me-2" disabled={loading || isSubmitting}>
                  Register
                </Button>
                <Button type="reset" variant="outline-danger" className="me-1" disabled={loading || isSubmitting}>
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
            {submitted && (
              <Alert variant="success">
                Thank you for registering! Your API token will be sent to your email.
              </Alert>
            )}
            <Alert className="mt-3 alert-api">
              <b>Important:</b> API access is limited to sequential requests only. Please wait until calculation results are returned before making another request.
              Contact <a href="mailto:NCILDlinkWebAdmin@mail.nih.gov?subject=LDlink" target="_top" title="Support" className="dark-blue">support</a> if you plan to make large volumes of API requests.
            </Alert>
          </Col>
        </Row>
        <hr />
        <p>
          Examples of command line arguments are listed below for each module. Replace the example token in <code>token=faketoken123</code> with your own registered token.
        </p>
        <div>
          <p>
            <a className="help-anchor-link" href="/help#LDexpress">LDexpress</a>
            <br />
            <pre className="apiaccess-examples">
              curl -k -H &quot;Content-Type: application/json&quot; -X POST -d
              &#123;&quot;snps&quot;: &quot;rs3\nrs4&quot;, &quot;pop&quot;: &quot;YRI+CEU&quot;, &quot;tissues&quot;: &quot;Adipose_Subcutaneous+Adipose_Visceral_Omentum&quot;, &quot;r2_d&quot;: &quot;r2&quot;, &quot;r2_d_threshold&quot;: &quot;0.1&quot;, &quot;p_threshold&quot;: &quot;0.1&quot;, &quot;window&quot;: &quot;500000&quot;, &quot;genome_build&quot;: &quot;grch37&quot;&#125; &apos;https://ldlink.nih.gov/LDlinkRest/ldexpress?token=faketoken123&apos;
            </pre>
          </p>
          
            <p>
            <a className="help-anchor-link" href="/help#LDhap">LDhap</a>
            <br />
            <pre className="apiaccess-examples">
                {`curl -k -X GET 'https://ldlink.nih.gov/LDlinkRest/ldhap?snps=rs3%0Ars4&pop=ALL&genome_build=grch38&token=faketoken123'`}
            </pre>
            </p>
            <p>
            <a className="help-anchor-link" href="/help#LDmatrix">LDmatrix</a>
            <br />
            <pre className="apiaccess-examples">
                {`curl -k -X GET 'https://ldlink.nih.gov/LDlinkRest/ldmatrix?snps=rs3%0Ars4%0Ars148890987&pop=CEU&r2_d=d&genome_build=grch38_high_coverage&token=faketoken123'`}
            </pre>
            <p>
                <i>Note: GET requests can support up to 300 SNPs.</i>
            </p>
            <pre className="apiaccess-examples">
                {`curl -k -H "Content-Type: application/json" -X POST -d '{"snps": "rs3\\nrs4", "pop": "CEU","r2_d": "d", "genome_build": "grch37"}' 'https://ldlink.nih.gov/LDlinkRest/ldmatrix?token=faketoken123'`}
            </pre>
            <p>
                <i>Note: POST requests can support up to 2,500 SNPs.</i>
            </p>
            </p>
            <p>
            <a className="help-anchor-link" href="/help#LDpair">LDpair</a>
            <br />
            <pre className="apiaccess-examples">
                {`curl -k -X GET 'https://ldlink.nih.gov/LDlinkRest/ldpair?var1=rs3&var2=rs4&pop=CEU%2BYRI%2BCHB&genome_build=grch37&json_out=false&token=faketoken123'`}
            </pre>
            <p>
                <i>Note: GET requests only support 1 SNP pair.</i>
            </p>
            <pre className="apiaccess-examples">
                {`curl -k -H "Content-Type: application/json" -X POST -d '{"snp_pairs": [["rs3", "rs4"], ["rs7837688", "rs4242384"]], "pop": "CEU+YRI+CHB","genome_build": "grch37", "json_out": true}' 'https://ldlink.nih.gov/LDlinkRest/ldpair?token=faketoken123'`}
            </pre>
            <p>
                <i>Note: POST requests can support up to 10 SNP pairs. If more than 1 SNP pair is provided, a JSON response will always be returned.</i>
            </p>
            </p>
            <p>
            <a className="help-anchor-link" href="/help#LDpop">LDpop</a>
            <br />
            <pre className="apiaccess-examples">
                {`curl -k -X GET 'https://ldlink.nih.gov/LDlinkRest/ldpop?var1=rs3&var2=rs4&pop=CEU%2BYRI%2BCHB&r2_d=r2&genome_build=grch37&token=faketoken123'`}
            </pre>
            </p>
            <p>
            <a className="help-anchor-link" href="/help#LDproxy">LDproxy</a>
            <br />
            <pre className="apiaccess-examples">
                {`curl -k -X GET 'https://ldlink.nih.gov/LDlinkRest/ldproxy?var=rs3&pop=MXL&r2_d=r2&window=500000&genome_build=grch37&token=faketoken123'`}
            </pre>
            </p>
            <p>
            <a className="help-anchor-link" href="/help#LDtrait">LDtrait</a>
            <br />
            <pre className="apiaccess-examples">
                {`curl -k -H "Content-Type: application/json" -X POST -d '{"snps": "rs3\\nrs4", "pop": "YRI", "r2_d": "r2", "r2_d_threshold": "0.1", "window": "500000", "genome_build": "grch37"}' 'https://ldlink.nih.gov/LDlinkRest/ldtrait?token=faketoken123'`}
            </pre>
            </p>
            <p>
            <a className="help-anchor-link" href="/help#SNPchip">SNPchip</a>
            <br />
            <pre className="apiaccess-examples">
                {`curl -k -H "Content-Type: application/json" -X POST -d '{"snps": "rs3\\nrs4\\nrs17795812", "platforms":"A_10X+A_250N+A_250S+A_50H+A_50X+A_AFR+A_ASI+A_CHB2+A_DMETplus+A_EAS+A_EUR+A_Exome1A+A_Exome319+A_Hu+A_Hu-CHB+A_LAT+A_Onco+A_OncoCNV+A_SNP5.0+A_SNP6.0+I_100+I_1M+I_1M-D+I_240S+I_300+I_300-D+I_550v1+I_550v3+I_610-Q+I_650Y+I_660W-Q+I_CNV-12+I_CNV370-D+I_CNV370-Q+I_CVD+I_CardioMetab+I_Core-12+I_CoreE-12v1+I_CoreE-12v1.1+I_CoreE-24v1+I_CoreE-24v1.1+I_Cyto-12v2+I_Cyto-12v2.1+I_Cyto-12v2.1f+I_Cyto850+I_Exome-12+I_Exon510S+I_Immuno-24v1+I_Immuno-24v2+I_Linkage-12+I_Linkage-24+I_ME-Global-8+I_NS-12+I_O1-Q+I_O1S-8+I_O2.5-4+I_O2.5-8+I_O2.5E-8v1+I_O2.5E-8v1.1+I_O2.5E-8v1.2+I_O2.5S-8+I_O5-4+I_O5E-4+I_OE-12+I_OE-12f+I_OE-24+I_OEE-8v1+I_OEE-8v1.1+I_OEE-8v1.2+I_OEE-8v1.3+I_OZH-8v1+I_OZH-8v1.1+I_OZH-8v1.2+I_OncoArray+I_Psyc-24v1+I_Psyc-24v1.1+I_GDA-C+I_GSA-v3C", "genome_build": "grch37"}' 'https://ldlink.nih.gov/LDlinkRest/snpchip?token=faketoken123'`}
            </pre>
            </p>
            <p>
            <a className="help-anchor-link" href="/help#SNPclip">SNPclip</a>
            <br />
            <pre className="apiaccess-examples">
                {`curl -k -H "Content-Type: application/json" -X POST -d '{"snps": "rs3\\nrs4", "pop": "YRI", "r2_threshold": "0.1", "maf_threshold": "0.01", "genome_build": "grch37"}' 'https://ldlink.nih.gov/LDlinkRest/snpclip?token=faketoken123'`}
            </pre>
            </p>
            <p>
            <strong>Note</strong>: <a className="help-anchor-link" href="/help#LDassoc">LDassoc</a> is not currently accessible via programmatic access.
            </p>
        </div>

        {/* Modals for API Access */}
        <Modal
          show={modalShow}
          onHide={() => setModalShow(false)}
          centered
          backdrop="static"
          aria-labelledby="apiaccess-modal-title"
        >
          <div
            className="modal-content"
            style={{
              borderStyle: "solid",
              borderWidth: 3,
              borderColor: modalType === "new" ? "#D6E9C6" : "#FFEEBA",
            }}
          >
            <div
              className="modal-header"
              style={{
                color: modalType === "new" ? "#3C763D" : "#856404",
                backgroundColor: modalType === "new" ? "#DFF0D8" : "#FFF3CD",
              }}
            >
              <h3 className="modal-title apiaccess" id="apiaccess-modal-title">
                {modalTitle}
              </h3>
            </div>
            <div className="modal-body" style={{ textAlign: "center" }}>
              {modalTitle && (modalTitle.startsWith("Error") || modalType === "error" || !submitted) ? (
                <span style={{ color: "#a94442", fontWeight: "bold" }}>
                  An error occurred during registration. Try again later. Contact us if you continue to experience issues.
                </span>
              ) : (
                <>
                  Your API token has been sent to the email:{" "}
                  <span className="apiaccess-user-email" style={{ fontWeight: "bold" }}>
                    {modalEmail}
                  </span>
                </>
              )}
            </div>
            <div className="modal-footer">
              <input
                type="button"
                id="apiaccess-done"
                value="Done"
                className="btn btn-primary apiaccess-done"
                onClick={() => {
                  setModalShow(false);
                  handleReset();
                }}
              />
            </div>
          </div>
        </Modal>
      </div>
      
    </Container>
  );
}