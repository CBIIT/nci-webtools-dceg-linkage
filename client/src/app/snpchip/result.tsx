import { useQueryClient } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";
import { FormData } from "./types";

export default function Result() {
  const queryClient = useQueryClient();
  const searchParams = useSearchParams();
  const reference = searchParams.get("ref") || "";
  const result = queryClient.getQueryData(["snpchip-form-data", reference]) as FormData | undefined;

  if (!reference) {
    return <div className="mt-4"><em>No calculation has been run yet.</em></div>;
  }

  if (!result) {
    return <div className="mt-4"><em>No result found for reference: {reference}</em></div>;
  }

  // Show summary of submitted form and result
  return (
    <div className="mt-4">
      <h2>Results</h2>
      <div className="mb-3">
        <strong>Reference:</strong> {reference}
      </div>
      <div className="mb-3">
        <strong>Submitted SNPs:</strong> {result?.snps}
      </div>
      <div className="mb-3">
        <strong>Selected Platforms:</strong> {result?.platforms?.join(", ")}
      </div>
      <div className="mb-3">
        <strong>Genome Build:</strong> {result?.genome_build}
      </div>
      {/* Render additional result data here */}
      <pre>{JSON.stringify(result, null, 2)}</pre>
    </div>
  );
}
