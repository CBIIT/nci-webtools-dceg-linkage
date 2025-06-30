"use client";
import React, { useState } from "react";
import { Container, Row, Col, Form, Button, Alert } from "react-bootstrap";
import Image from "next/image";

export default function ApiAccessPage() {
  const [form, setForm] = useState({
    firstname: "",
    lastname: "",
    email: "",
    institution: "",
  });
  const [submitted, setSubmitted] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.id.replace("apiaccess-", "")]: e.target.value });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: handle API registration logic here
    setSubmitted(true);
  };

  const handleReset = () => {
    setForm({ firstname: "", lastname: "", email: "", institution: "" });
    setSubmitted(false);
  };

  return (
    <Container className="py-4">
      <div className="text-center">
        <h2>
          <Image
            src="/images/LDlink_logo_small_clear.png"
            alt="LDlink"
            style={{ verticalAlign: "bottom" }}
            width={91}
            height={36}
          />{" "}
          API Access
        </h2>
      </div>
      <p>
        LDlink modules are also accessible via command line from a terminal. This programmatic access facilitates researchers
        who are interested in performing batch queries. The syntax is similar to the web address link created
        for queries on the webpage. Generally text output is returned that is the same as the file a user would
        download from the online site. Please register below for an access token required for your API call. Once registered, your access token will be emailed to you.
      </p>
      <Row className="justify-content-center">
        <Col sm={7} className="text-center">
          <i>
            Interested in accessing LDlink&apos;s API using R? <br />
            Check out the new LDlinkR package now available on{" "}
            <a href="https://cran.r-project.org/web/packages/LDlinkR/index.html" title="LDlinkR CRAN" target="_blank" rel="noopener noreferrer">
              CRAN
            </a>.
          </i>
        </Col>
      </Row>
      <hr />
      <Row className="justify-content-center">
        <Col md={8}>
          <Form id="apiaccessForm" onSubmit={handleSubmit} onReset={handleReset}>
            <Row>
              <Col sm={6}>
                <Form.Group controlId="apiaccess-firstname" className="mb-3">
                  <Form.Label>
                    First name<span style={{ color: "red" }}>*</span>
                  </Form.Label>
                  <Form.Control
                    type="text"
                    placeholder="First name"
                    value={form.firstname}
                    onChange={handleChange}
                    required
                  />
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
                    value={form.lastname}
                    onChange={handleChange}
                    required
                  />
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
                value={form.email}
                onChange={handleChange}
                required
              />
            </Form.Group>
            <Form.Group controlId="apiaccess-institution" className="mb-3">
              <Form.Label>
                Institution<span style={{ color: "red" }}>*</span>
              </Form.Label>
              <Form.Control
                type="text"
                placeholder="Institution"
                value={form.institution}
                onChange={handleChange}
                required
              />
            </Form.Group>
            <div className="mb-3">
              <Button type="submit" className="btn btn-default calculate me-2">
                Register
              </Button>
              <Button type="reset" className="btn btn-default">
                Reset
              </Button>
            </div>
          </Form>
          {submitted && (
            <Alert variant="success">
              Thank you for registering! Your API token will be sent to your email.
            </Alert>
          )}
          <Alert variant="info" className="mt-3">
            <b>Important:</b> API access is limited to sequential requests only. Please wait until calculation results are returned before making another request.
            Contact <a href="mailto:NCILDlinkWebAdmin@mail.nih.gov?subject=LDlink" target="_top" title="Support">support</a> if you plan to make large volumes of API requests.
          </Alert>
        </Col>
      </Row>
      <hr />
      <p>
        Examples of command line arguments are listed below for each module. Replace the example token in <code>token=faketoken123</code> with your own registered token.
      </p>
      <div>
        <p>
          <a className="help-anchor-link" href="#LDexpress">LDexpress</a>
          <br />
          <pre className="apiaccess-examples">
            curl -k -H &quot;Content-Type: application/json&quot; -X POST -d
            &#123;&quot;snps&quot;: &quot;rs3\nrs4&quot;, &quot;pop&quot;: &quot;YRI+CEU&quot;, &quot;tissues&quot;: &quot;Adipose_Subcutaneous+Adipose_Visceral_Omentum&quot;, &quot;r2_d&quot;: &quot;r2&quot;, &quot;r2_d_threshold&quot;: &quot;0.1&quot;, &quot;p_threshold&quot;: &quot;0.1&quot;, &quot;window&quot;: &quot;500000&quot;, &quot;genome_build&quot;: &quot;grch37&quot;&#125; &apos;https://ldlink.nih.gov/LDlinkRest/ldexpress?token=faketoken123&apos;
          </pre>
        </p>
        {/* Repeat for other modules as in your HTML */}
        <p>
          <strong>Note</strong>: <a className="help-anchor-link" href="#LDassoc">LDassoc</a> is not currently accessible via programmatic access.
        </p>
      </div>
    </Container>
  );
}