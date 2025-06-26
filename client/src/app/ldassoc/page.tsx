"use client";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { ErrorBoundary } from "next/dist/client/components/error-boundary";
import Alert from "react-bootstrap/Alert";
import Loading from "@/components/loading";
import { Container } from "react-bootstrap";
import LDAssocForm from "./form";
import LdAssocResults from "./results";
export default function LdAssoc() {
  const searchParams = useSearchParams();
  const ref = searchParams.get("ref");

  return (
    <Container fluid="md" className="border rounded bg-white my-3 p-3">
      <LDAssocForm />
      <ErrorBoundary errorComponent={() => <Alert variant="warning">Error loading results</Alert>}>
        <Suspense fallback={<Loading message="Loading..." />}>{ref && <LdAssocResults ref={ref} />}</Suspense>
      </ErrorBoundary>
    </Container>
  );
}
