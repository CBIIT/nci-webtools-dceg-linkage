import Select, { components } from "react-select";
import { Controller } from "react-hook-form";
import "./select.scss";

export interface PopOption {
  value: string;
  label: string;
}

export interface GroupedOption {
  label: string;
  options: PopOption[];
}

export interface Populations {
  [key: string]: {
    label: string;
    subPopulations: {
      [subKey: string]: string;
    };
  };
}

export const populations: Populations = {
  AFR: {
    label: "African",
    subPopulations: {
      YRI: "Yoruba in Ibadan, Nigera",
      LWK: "Luhya in Webuye, Kenya",
      GWD: "Gambian in Western Gambia",
      MSL: "Mende in Sierra Leone",
      ESN: "Esan in Nigera",
      ASW: "Americans of African Ancestry in SW USA",
      ACB: "African Carribbeans in Barbados",
    },
  },
  AMR: {
    label: "Ad Mixed American",
    subPopulations: {
      MXL: "Mexican Ancestry from Los Angeles, USA",
      PUR: "Puerto Ricans from Puerto Rico",
      CLM: "Colombians from Medellin, Colombia",
      PEL: "Peruvians from Lima, Peru",
    },
  },
  EAS: {
    label: "East Asian",
    subPopulations: {
      CHB: "Han Chinese in Bejing, China",
      JPT: "Japanese in Tokyo, Japan",
      CHS: "Southern Han Chinese",
      CDX: "Chinese Dai in Xishuangbanna, China",
      KHV: "Kinh in Ho Chi Minh City, Vietnam",
    },
  },
  EUR: {
    label: "European",
    subPopulations: {
      CEU: "Utah Residents from North and West Europe",
      TSI: "Toscani in Italia",
      FIN: "Finnish in Finland",
      GBR: "British in England and Scotland",
      IBS: "Iberian population in Spain",
    },
  },
  SAS: {
    label: "South Asian",
    subPopulations: {
      GIH: "Gujarati Indian from Houston, Texas",
      PJL: "Punjabi from Lahore, Pakistan",
      BEB: "Bengali from Bangladesh",
      STU: "Sri Lankan Tamil from the UK",
      ITU: "Indian Telugu from the UK",
    },
  },
};

// Helper to convert params.pop to array of { value, label }
/**
 * Converts a population parameter (string or array) to an array of objects with value and label.
 *
 * @param pop - Population parameter, either a string (e.g. "YRI+LWK") or an array of objects.
 * @returns Array of objects: [{ value: string, label: string }]
 */
export function getOptionsFromKeys(pop: string | any[]): any[] {
  if (typeof pop === "string") {
    const codes = pop.split("+");
    return codes.flatMap((code) => {
      // If code is a population group (e.g., AFR), return all its subPopulations
      if (populations[code]) {
        return Object.entries(populations[code].subPopulations).map(([subCode, subLabel]) => ({
          value: subCode,
          label: `(${subCode}) ${subLabel}`,
        }));
      } else {
        // Otherwise, treat as subPopulation code
        const group = Object.values(populations).find((g) => g.subPopulations[code]);
        const label = group ? `(${code}) ${group.subPopulations[code]}` : code;
        return { value: code, label };
      }
    });
  } else {
    return pop;
  }
}

/**
 * Returns a string representing the selected population groups or individual population codes.
 *
 * This function determines which population groups are fully selected based on the provided
 * selection. If all sub-populations of a group are selected, the group key is included in the result.
 * Otherwise, any remaining selected codes that are not part of a fully selected group are included individually.
 * The result is a string of group keys and/or individual codes, joined by "+".
 *
 * @param selected - An array of selected population options.
 * @param populationsObj - An optional object containing all population groups and their sub-populations.
 *                         Defaults to the global `populations` object if not provided.
 * @returns A string of selected group keys and/or individual codes, joined by "+".
 */
export function getSelectedPopulationGroups(selected: PopOption[], populationsObj: Populations = populations): string {
  const selectedCodes = new Set(selected.map((opt) => opt.value));
  const groupKeys: string[] = [];
  const coveredCodes = new Set<string>();

  // Check for fully selected groups
  for (const [key, group] of Object.entries(populationsObj)) {
    const subCodes = Object.keys(group.subPopulations);
    const allSelected = subCodes.every((code) => selectedCodes.has(code));
    if (allSelected) {
      groupKeys.push(key);
      subCodes.forEach((code) => coveredCodes.add(code));
    }
  }

  // Add any remaining selected codes not covered by a full group
  for (const code of selectedCodes) {
    if (!coveredCodes.has(code)) {
      groupKeys.push(code);
    }
  }

  return groupKeys.join("+");
}

export default function PopSelect({ name, control, rules }: { name: string; control: any; rules?: any }) {
  const popGroups: GroupedOption[] = Object.entries(populations).map(([key, group]) => ({
    label: `(${key}) ${group.label}`,
    value: key,
    options: Object.entries(group.subPopulations).map(([value, label]) => ({
      value,
      label: `(${value}) ${label}`,
    })),
  }));

  const popOptions: any[] = [{ label: "(ALL) All Populations", value: "ALL" }, ...popGroups];

  const Group = (props: any) => {
    const onClick = () => {
      // Find all options within this group
      const groupOptions = props.options;
      const currentValues = props.selectProps.value || [];

      // Check if all options in this group are already selected
      const allSelected = groupOptions.every((opt: any) => currentValues.some((sel: any) => sel.value === opt.value));

      // If all selected, deselect the group, otherwise select all in group
      const newSelection = allSelected
        ? currentValues.filter((sel: any) => !groupOptions.some((opt: any) => opt.value === sel.value))
        : [
            ...currentValues,
            ...groupOptions.filter((opt: any) => !currentValues.some((sel: any) => sel.value === opt.value)),
          ];

      props.selectProps.onChange(newSelection);
    };
    return <components.Group {...props} headingProps={{ ...props.headingProps, onClick }} />;
  };

  const customStyles = {
    option: (provided: any, state: any) => {
      // Indent only group options, not the "ALL" option
      const isGroupOption = state.data && state.data.value !== "ALL";
      return {
        ...provided,
        paddingLeft: isGroupOption ? 32 : provided.paddingLeft,
      };
    },
    menu: (provided: any) => ({ ...provided, zIndex: 9999 }),
  };

  const formatGroupLabel = (data: GroupedOption) => (
    <div
      className="text-primary"
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        fontSize: ".9rem",
        cursor: "pointer",
      }}>
      <span>{data.label}</span>
      <span
        style={{
          backgroundColor: "#EBECF0",
          borderRadius: "2em",
          color: "#172B4D",
          display: "inline-block",
          fontSize: 12,
          fontWeight: "normal",
          lineHeight: "1",
          minWidth: 1,
          padding: "0.16666666666667em 0.5em",
          textAlign: "center",
        }}>
        {data.options.length}
      </span>
    </div>
  );

  function handleChange(selected: any[], previous: any[], onchange: any) {
    // If "ALL" is selected, deselect all others
    const prevHasAll = Array.isArray(previous) && previous.some((opt) => opt.value === "ALL");
    const currHasAll = Array.isArray(selected) && selected.some((opt) => opt.value === "ALL");

    if (currHasAll && !prevHasAll) {
      onchange([{ label: "(ALL) All Populations", value: "ALL" }]);
      return;
    }

    // If "ALL" was previously selected and now something else is selected, remove "ALL"
    if (!currHasAll && prevHasAll) {
      const filtered = selected.filter((opt) => opt.value !== "ALL");
      onchange(filtered);
      return;
    }

    // If both present, remove "ALL"
    if (currHasAll && selected.length > 1) {
      const filtered = selected.filter((opt) => opt.value !== "ALL");
      onchange(filtered);
      return;
    }

    onchange(selected);
  }

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
            isMulti
            options={popOptions}
            closeMenuOnSelect={false}
            components={{ Group }}
            className="basic-multi-select"
            classNamePrefix="select"
            value={field.value || []}
            styles={customStyles}
            formatGroupLabel={formatGroupLabel}
            onChange={(selected) => handleChange(Array.from(selected), field.value, field.onChange)}
          />
        </div>
      )}
    />
  );
}
