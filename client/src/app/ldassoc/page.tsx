"use client";
import { Suspense } from "react";
import { ErrorBoundary } from "next/dist/client/components/error-boundary";
import Alert from "react-bootstrap/Alert";
import Loading from "@/components/loading";
import { Container } from "react-bootstrap";
import LDAssocForm from "./form";
import LdAssocResults from "./results";
export default function LdAssoc() {
  return (
    <Container fluid="md" className="border rounded bg-white my-3 p-3">
      <ErrorBoundary errorComponent={() => <Alert variant="warning">Error loading Form</Alert>}>
        <Suspense fallback={<Loading message="Loading..." />}>
          <LDAssocForm />
          <LdAssocResults />
        </Suspense>
      </ErrorBoundary>
    </Container>
  );
}
