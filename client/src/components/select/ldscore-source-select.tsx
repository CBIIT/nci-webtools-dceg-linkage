"use client";
import Select from "react-select";
import { Form } from "react-bootstrap";
import { ldscorePopOptions, LdscorePopOption } from "./ldscore-pop-select";
import { LdScoreRunSummary } from "@/services/queries";

export type LdscoreSourceMode = "reference" | "customUpload" | "customImport" | "customSession";

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
  const window = run.windowSize ? `Window: ${run.windowSize}${run.windowUnit || ""}` : "";
  return [files, window, when].filter(Boolean).join(" — ");
}

export default function LdscoreSourceSelect({
  value,
  onChange,
  currentSessionRuns,
  priorRuns,
  priorRunsLoading,
  disabled,
  onRequestUpload,
  onRequestImport,
}: {
  value: LdscoreSourceValue;
  onChange: (value: LdscoreSourceValue) => void;
  currentSessionRuns: LdScoreRunSummary[];
  priorRuns: LdScoreRunSummary[];
  priorRunsLoading?: boolean;
  disabled?: boolean;
  onRequestUpload?: () => void;
  onRequestImport?: () => void;
}) {
  const customStyles = {
    menu: (provided: any) => ({ ...provided, zIndex: 9999 }),
    menuPortal: (provided: any) => ({ ...provided, zIndex: 9999 }),
  };

  // Both lists are already scoped to this browser session (client-side cache for instant
  // availability, and the server's 1-hour-retained registry) -- union them into one option.
  const sessionRuns = [...currentSessionRuns, ...priorRuns].filter(
    (run, index, all) => all.findIndex((other) => other.reference === run.reference) === index
  );

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
          label="Custom LD scores"
          checked={value.mode !== "reference"}
          disabled={disabled}
          onChange={() => {
            // Default to "Upload existing LD score result" regardless of prior/session
            // runs being available -- the sub-radio itself won't fire onChange here since
            // `checked` is already true as soon as mode matches, so it never gets
            // clicked by the user.
            onChange({ ...value, mode: "customImport", ldscoreReference: null });
          }}
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
        <div className="ps-4">
          <div className="mb-2">
            {/* <Form.Check
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
            /> */}
            <Form.Check
              type="radio"
              id="ldscore-source-session"
              name="ldscore-source-custom-mode"
              label={`Use a result from this session${priorRunsLoading ? " (loading...)" : sessionRuns.length ? ` (${sessionRuns.length})` : ""}`}
              checked={value.mode === "customSession"}
              disabled={disabled || (!priorRunsLoading && sessionRuns.length === 0)}
              onChange={() => onChange({ ...value, mode: "customSession", ldscoreReference: sessionRuns[0]?.reference ?? null })}
            />
            {/* Placed last so it sits directly above its own upload input, which is rendered by the parent right after this component. */}
            <Form.Check
              type="radio"
              id="ldscore-source-import"
              name="ldscore-source-custom-mode"
              label="Upload existing LD score result"
              checked={value.mode === "customImport"}
              disabled={disabled}
              onChange={() => {
                onChange({ ...value, mode: "customImport", ldscoreReference: null });
                onRequestImport?.();
              }}
            />
          </div>

          {value.mode === "customSession" && sessionRuns.length > 0 && (
            <>
              <Form.Select
                aria-label="Select an LD score run from this session"
                value={value.ldscoreReference ?? ""}
                disabled={disabled}
                onChange={(e) => onChange({ ...value, ldscoreReference: e.target.value })}
              >
                {sessionRuns.map((run) => (
                  <option key={run.reference} value={run.reference}>
                    {formatRunLabel(run)}
                  </option>
                ))}
              </Form.Select>
              <div style={{ fontSize: "0.85rem" }}>Results get deleted after one hour.</div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
