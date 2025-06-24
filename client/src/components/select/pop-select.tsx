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

export default function PopSelect({ name, control }: { name: string; control: any }) {
  const popGroups: GroupedOption[] = Object.entries(populations).map(([key, group]) => ({
    label: `(${key}) ${group.label}`,
    value: key,
    options: Object.entries(group.subPopulations).map(([value, label]) => ({
      value,
      label: `(${value}) ${label}`,
    })),
  }));
  console.log("Pop groups:", popGroups);
  const popOptions: any[] = [{ label: "(ALL) All Populations", value: "ALL" }, ...popGroups];

  const Group = (props: any) => {
    const onClick = () => props.selectProps.onChange(props.options);
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
      render={({ field }) => (
        <Select
          {...field}
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
      )}
    />
  );
}
