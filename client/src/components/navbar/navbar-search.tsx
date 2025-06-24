"use client";
import Form from "react-bootstrap/Form";
import Button from "react-bootstrap/Button";
import InputGroup from "react-bootstrap/InputGroup";

export default function NavbarSearch() {
  function handleSubmit(event: any) {
    event.preventDefault();

    const form = event.target;
    const site = window.location.host;
    const search = form.elements.q.value;
    const query = `site:${site} ${search}`;

    const searchParams = new URLSearchParams();
    searchParams.append("q", query);

    const searchUrl = `${form.action}?${searchParams}`;
    window.open(searchUrl, "_blank");
  }

  return (
    <Form
      className="d-flex align-items-stretch mb-4 mb-md-0"
      role="search"
      action="https://www.google.com/search"
      onSubmit={handleSubmit}>
      <InputGroup style={{ borderBottom: "3px white solid" }}>
        <Form.Control
          className="search-control"
          type="search"
          placeholder="Search"
          aria-label="search"
          name="q"
          style={{ backgroundColor: "transparent" }}
        />
        <Button
          variant="outline-secondary"
          className="search-control-button"
          type="submit"
          style={{ backgroundColor: "transparent" }}>
          <i className="bi bi-search"></i>
          <span className="visually-hidden">submit</span>
        </Button>
      </InputGroup>
    </Form>
  );
}
