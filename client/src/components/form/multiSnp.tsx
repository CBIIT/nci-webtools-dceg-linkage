import Form from "react-bootstrap/Form";
import { rsChrMultilineRegex } from "@/services/utils";

/**
 * MultiSnp - A form component for entering multiple SNP identifiers or genomic coordinates
 *
 * @param name - The form field name for react-hook-form registration
 * @param register - The react-hook-form register function for form validation
 * @param errors - The form errors object from react-hook-form
 * @returns A textarea form control with validation for RS numbers or genomic coordinates
 */
export default function MultiSnp({ name, register, errors }: { name: string; register: any; errors: any }) {
  return (
    <Form.Group controlId={name} className="mb-3" style={{ maxWidth: "300px" }}>
      <Form.Label>RS Numbers or Genomic Coordinates</Form.Label>
      <Form.Control
        as="textarea"
        rows={2}
        {...register(name, {
          required: "This field is required",
          pattern: {
            value: rsChrMultilineRegex,
            message:
              "Please match the format requested: rs followed by 1 or more digits (ex: rs12345), no spaces permitted - or - chr(0-22, X, Y):##### (ex: chr1:12345)",
          },
        })}
        title="Enter list of RS numbers or Genomic Coordinates (one per line)"
      />
      <Form.Text className="text-danger">{errors?.[name]?.message}</Form.Text>
    </Form.Group>
  );
}
