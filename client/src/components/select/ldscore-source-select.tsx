"use client";
import Select from "react-select";
import { Form } from "react-bootstrap";
import { ldscorePopOptions, LdscorePopOption } from "./ldscore-pop-select";
import { LdScoreRunSummary } from "@/services/queries";

export type LdscoreSourceMode = "reference" | "customUpload" | "customSession" | "customPrior";

export interface LdscoreSourceValue {
  mode: LdscoreSourceMode;
  pop: LdscorePopOption | null;
  ldscoreReference: string | null;
}

export const defaultLdscoreSourceValue: LdscoreSourceValue = {
  mode: "reference",
  pop: null,
  ldscoreReference: null,
};

function formatRunLabel(run: LdScoreRunSummary): string {
  const when = run.createdAt ? new Date(run.createdAt).toLocaleString() : "";
  const files = run.sourceFilenames?.length ? run.sourceFilenames.join(", ") : run.label;
  return [files, when].filter(Boolean).join(" — ");
}

export default function LdscoreSourceSelect({
  value,
  onChange,
  currentSessionRuns,
  priorRuns,
  priorRunsLoading,
  disabled,
  onRequestUpload,
}: {
  value: LdscoreSourceValue;
  onChange: (value: LdscoreSourceValue) => void;
  currentSessionRuns: LdScoreRunSummary[];
  priorRuns: LdScoreRunSummary[];
  priorRunsLoading?: boolean;
  disabled?: boolean;
  onRequestUpload?: () => void;
}) {
  const customStyles = {
    menu: (provided: any) => ({ ...provided, zIndex: 9999 }),
    menuPortal: (provided: any) => ({ ...provided, zIndex: 9999 }),
  };

  return (
    <div>
      <div className="mb-2">
        <Form.Check
          type="radio"
          id="ldscore-source-reference"
          name="ldscore-source-mode"
          label="Reference population LD scores"
          checked={value.mode === "reference"}
          disabled={disabled}
          onChange={() => onChange({ ...value, mode: "reference" })}
        />
        <Form.Check
          type="radio"
          id="ldscore-source-custom"
          name="ldscore-source-mode"
          label="Custom LD score"
          checked={value.mode !== "reference"}
          disabled={disabled}
          onChange={() =>
            onChange({
              ...value,
              mode: currentSessionRuns.length > 0 ? "customSession" : priorRuns.length > 0 ? "customPrior" : "customUpload",
            })
          }
        />
      </div>

      {value.mode === "reference" && (
        <Select
          inputId="ldscore-source-pop"
          options={ldscorePopOptions}
          value={value.pop}
          onChange={(pop) => onChange({ ...value, pop: pop as LdscorePopOption | null })}
          isMulti={false}
          classNamePrefix="react-select"
          placeholder="Select population..."
          isDisabled={disabled}
          styles={customStyles}
          menuPortalTarget={typeof window !== "undefined" ? document.body : null}
          menuPosition="fixed"
        />
      )}

      {value.mode !== "reference" && (
        <div className="ps-1">
          <div className="mb-2">
            <Form.Check
              type="radio"
              id="ldscore-source-upload"
              name="ldscore-source-custom-mode"
              label="Upload new *.bed/*.bim/*.fam files"
              checked={value.mode === "customUpload"}
              disabled={disabled}
              onChange={() => {
                onChange({ ...value, mode: "customUpload", ldscoreReference: null });
                onRequestUpload?.();
              }}
            />
            <Form.Check
              type="radio"
              id="ldscore-source-session"
              name="ldscore-source-custom-mode"
              label={`Use a result from this session${currentSessionRuns.length ? ` (${currentSessionRuns.length})` : ""}`}
              checked={value.mode === "customSession"}
              disabled={disabled || currentSessionRuns.length === 0}
              onChange={() => onChange({ ...value, mode: "customSession", ldscoreReference: currentSessionRuns[0]?.reference ?? null })}
            />
            <Form.Check
              type="radio"
              id="ldscore-source-prior"
              name="ldscore-source-custom-mode"
              label={`Use a prior run${priorRunsLoading ? " (loading...)" : priorRuns.length ? ` (${priorRuns.length})` : ""}`}
              checked={value.mode === "customPrior"}
              disabled={disabled || (!priorRunsLoading && priorRuns.length === 0)}
              onChange={() => onChange({ ...value, mode: "customPrior", ldscoreReference: priorRuns[0]?.reference ?? null })}
            />
          </div>

          {value.mode === "customSession" && currentSessionRuns.length > 0 && (
            <Form.Select
              aria-label="Select an LD score run from this session"
              value={value.ldscoreReference ?? ""}
              disabled={disabled}
              onChange={(e) => onChange({ ...value, ldscoreReference: e.target.value })}
            >
              {currentSessionRuns.map((run) => (
                <option key={run.reference} value={run.reference}>
                  {formatRunLabel(run)}
                </option>
              ))}
            </Form.Select>
          )}

          {value.mode === "customPrior" && priorRuns.length > 0 && (
            <Form.Select
              aria-label="Select a prior LD score run"
              value={value.ldscoreReference ?? ""}
              disabled={disabled}
              onChange={(e) => onChange({ ...value, ldscoreReference: e.target.value })}
            >
              {priorRuns.map((run) => (
                <option key={run.reference} value={run.reference}>
                  {formatRunLabel(run)}
                </option>
              ))}
            </Form.Select>
          )}
        </div>
      )}
    </div>
  );
}
