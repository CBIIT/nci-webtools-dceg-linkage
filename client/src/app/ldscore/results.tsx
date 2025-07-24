"use client";
import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Container, Row, Col, Alert, Spinner } from "react-bootstrap";

export default function LdScoreResults() {
  const searchParams = useSearchParams();
  const ref = searchParams.get("ref");

  const { data, isLoading, error } = useQuery({
    queryKey: ["ldscore", ref],
    enabled: !!ref,
  });

  if (isLoading) {
    return (
      <Container>
        <Row>
          <Col className="text-center">
            <Spinner animation="border" role="status">
              <span className="visually-hidden">Loading...</span>
            </Spinner>
            <p>Processing LDscore calculation...</p>
          </Col>
        </Row>
      </Container>
    );
  }

  if (error) {
    return (
      <Container>
        <Alert variant="danger">
          <Alert.Heading>Error</Alert.Heading>
          <p>Failed to load LDscore results.</p>
        </Alert>
      </Container>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <Container>
      <Row className="border rounded bg-white my-3 p-3 shadow-sm">
        <Col>
          <h5>LDscore Results</h5>
          <div className="mt-3">
            {/* Results will be displayed here */}
            <p>Results for reference: {ref}</p>
            <pre>{JSON.stringify(data, null, 2)}</pre>
          </div>
        </Col>
      </Row>
    </Container>
  );
}
