import Select from "react-select";
import { Controller } from "react-hook-form";

export interface LdscorePopOption {
  value: string;
  label: string;
}

const ldscorePopOptions: LdscorePopOption[] = [
  { value: "EUR", label: "(EUR) European" },
  { value: "EAS", label: "(EAS) East Asian" },
  { value: "AFR", label: "(AFR) African American" },
  { value: "ASJ", label: "(ASJ) Ashkenazi Jewish" },
  { value: "EST", label: "(EST) Estonian" },
  { value: "FIN", label: "(FIN) Finnish European" },
  { value: "AMR", label: "(AMR) Latino / Admixed American" },
  { value: "NFE", label: "(NFE) Non-Finnish European" },
  { value: "NWE", label: "(NWE) North-Western European" },
  { value: "SEU", label: "(SEU) Southern European" },
];

export default function LdscorePopSelect({ name, control, rules }: { name: string; control: any; rules?: any }) {
  return (
    <Controller
      name={name}
      control={control}
      rules={rules}
      render={({ field }) => (
        <div title="Select Population">
         
          <Select
            {...field}
            inputId={name}
            options={ldscorePopOptions}
            isMulti={false}
            classNamePrefix="react-select"
            placeholder="Select..."
          />
        </div>
      )}
    />
  );
}
