import Select, { components } from "react-select";
import { Controller } from "react-hook-form";

export interface Populations {
  [key: string]: {
    fullName: string;
    subPopulations: {
      [subKey: string]: string;
    };
  };
}

export const populations: Populations = {
  AFR: {
    fullName: "African",
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
    fullName: "Ad Mixed American",
    subPopulations: {
      MXL: "Mexican Ancestry from Los Angeles, USA",
      PUR: "Puerto Ricans from Puerto Rico",
      CLM: "Colombians from Medellin, Colombia",
      PEL: "Peruvians from Lima, Peru",
    },
  },
  EAS: {
    fullName: "East Asian",
    subPopulations: {
      CHB: "Han Chinese in Bejing, China",
      JPT: "Japanese in Tokyo, Japan",
      CHS: "Southern Han Chinese",
      CDX: "Chinese Dai in Xishuangbanna, China",
      KHV: "Kinh in Ho Chi Minh City, Vietnam",
    },
  },
  EUR: {
    fullName: "European",
    subPopulations: {
      CEU: "Utah Residents from North and West Europe",
      TSI: "Toscani in Italia",
      FIN: "Finnish in Finland",
      GBR: "British in England and Scotland",
      IBS: "Iberian population in Spain",
    },
  },
  SAS: {
    fullName: "South Asian",
    subPopulations: {
      GIH: "Gujarati Indian from Houston, Texas",
      PJL: "Punjabi from Lahore, Pakistan",
      BEB: "Bengali from Bangladesh",
      STU: "Sri Lankan Tamil from the UK",
      ITU: "Indian Telugu from the UK",
    },
  },
};

export default function PopSelect({ name, control }) {
  interface PopOption {
    readonly value: string;
    readonly label: string;
  }

  interface GroupedOption {
    readonly label: string;
    readonly options: readonly PopOption[];
  }

  const popGroups: readonly GroupedOption[] = Object.entries(populations).map(([key, group]) => ({
    label: `(${key}) ${group.fullName}`,
    options: Object.entries(group.subPopulations).map(([value, label]) => ({
      value,
      label: `(${value}) ${label}`,
    })),
  }));
  const popOptions: any[] = [{ label: "(ALL) All Populations", value: "ALL" }, ...popGroups];

  const GroupHeading = (props: any) => {
    const { data, selectProps } = props;
    const handleClick = (e: React.MouseEvent) => {
      e.stopPropagation();
      const groupOptions = data.options;
      const currentValue = selectProps.value || [];
      // Add only options not already selected
      const newValue = [
        ...currentValue,
        ...groupOptions.filter((opt: any) => !currentValue.some((v: any) => v.value === opt.value)),
      ];
      selectProps.onChange(newValue, { action: "select-option", option: groupOptions });
    };

    return (
      <div onClick={handleClick} className="custom-group-heading" style={{ cursor: "pointer" }}>
        <components.GroupHeading {...props} />
      </div>
    );
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
  };

  const formatGroupLabel = (data: GroupedOption) => (
    <div
      className="text-primary"
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        fontSize: ".9rem",
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

  function handleChange(selected: any[], previous: any[], cb: Function) {
    // If "ALL" is selected, deselect all others
    const prevHasAll = Array.isArray(previous) && previous.some((opt) => opt.value === "ALL");
    const currHasAll = Array.isArray(selected) && selected.some((opt) => opt.value === "ALL");

    if (currHasAll && !prevHasAll) {
      cb([{ label: "(ALL) All Populations", value: "ALL" }]);
      return;
    }

    // If "ALL" was previously selected and now something else is selected, remove "ALL"
    if (!currHasAll && prevHasAll) {
      const filtered = selected.filter((opt) => opt.value !== "ALL");
      cb(filtered);
      return;
    }

    // If both present, remove "ALL"
    if (currHasAll && selected.length > 1) {
      const filtered = selected.filter((opt) => opt.value !== "ALL");
      cb(filtered);
      return;
    }

    cb(selected);
  }

  return (
    <Controller
      name={name}
      control={control}
      render={({ field }) => (
        <Select
          {...field}
          isMulti
          options={popOptions}
          closeMenuOnSelect={false}
          components={{ GroupHeading }}
          className="basic-multi-select"
          classNamePrefix="select"
          value={field.value || []}
          styles={customStyles}
          formatGroupLabel={formatGroupLabel}
          onChange={(selected) => handleChange(selected, field.value, field.onChange)}
        />
      )}
    />
  );
}
