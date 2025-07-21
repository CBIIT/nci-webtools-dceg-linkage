import { GoogleMap, Marker, InfoWindow } from "@react-google-maps/api";
import React from "react";

// icon type: allow custom SVG path icons or standard icons
export interface MapMarker {
  position: { lat: number; lng: number };
  icon?: string | google.maps.Icon | google.maps.Symbol | undefined;
  label?: google.maps.MarkerLabel;
  title?: string;
  onClick?: () => void;
  infoWindowContent?: React.ReactNode;
  infoWindowOpen?: boolean;
}

export interface PopMapProps {
  mapOptions: google.maps.MapOptions;
  containerStyle?: React.CSSProperties;
  markers: MapMarker[];
  children?: React.ReactNode;
}

const defaultContainerStyle = { width: "100%", height: "400px" };

const PopMap: React.FC<PopMapProps> = ({
  mapOptions,
  containerStyle,
  markers,
  children,
}) => {
  return (
    <GoogleMap mapContainerStyle={containerStyle || defaultContainerStyle} options={mapOptions}>
      {markers.map((marker, i) => (
        <React.Fragment key={i}>
          <Marker
            position={marker.position}
            // Only pass icon if it is a string, Icon, or Symbol and has a 'url' if required
            icon={marker.icon && typeof marker.icon === 'object' && 'url' in marker.icon && !marker.icon.url ? undefined : marker.icon}
            label={marker.label}
            title={marker.title}
            onClick={marker.onClick}
          />
          {marker.infoWindowOpen && marker.infoWindowContent && (
            <InfoWindow position={marker.position} onCloseClick={marker.onClick}>
              <div>{marker.infoWindowContent}</div>
            </InfoWindow>
          )}
        </React.Fragment>
      ))}
      {children}
    </GoogleMap>
  );
};

// Utility to select color from a palette based on a value between 0 and 1
export function getColorByValue(value: number, palette: string[]) {
  const idx = Math.round(Math.max(0, Math.min(1, value)) * (palette.length - 1));
  return palette[idx] || palette[0];
}

export function getMarkerColor(type: "LD" | "MAF", value: number | string, LD_COLORS: string[], MAF_COLORS: string[]) {
  if (value === "NA" || value === undefined || value === null) return "#E9F3F9";
  const num = typeof value === "number" ? value : Number(value);
  if (isNaN(num)) return "#E9F3F9";
  return type === "LD" ? getColorByValue(num, LD_COLORS) : getColorByValue(num, MAF_COLORS);
}

export function colorMarkerLD(LD: "r2" | "dprime", location: any, LD_COLORS: string[], MAF_COLORS: string[]) {
  const value = LD === "r2" ? location[7] : location[8];
  return getMarkerColor("LD", value, LD_COLORS, MAF_COLORS);
}

export function colorMarkerMAF(minorAllele: string, location: any, LD_COLORS: string[], MAF_COLORS: string[]) {
  const alleleData = location[5]?.replace(/[\s\%]/g, "").split(/[\,\:]/);
  if (!alleleData || alleleData.length < 4) return "#FFFFFF";
  const alleleDataHash: Record<string, number> = {
    [alleleData[0]]: parseFloat(alleleData[1]),
    [alleleData[2]]: parseFloat(alleleData[3]),
  };
  const MAF = (alleleDataHash[minorAllele] ?? 0) / 100.0;
  return getMarkerColor("MAF", MAF, LD_COLORS, MAF_COLORS);
}

export function getMinorAllele(variantIndex: number, aaData: any[]) {
  // variantIndex should be 2 or 3
  const getAlleleString = (row: any): string => {
    if (variantIndex === 2) return row[2];
    if (variantIndex === 3) return row[3];
    throw new Error("Invalid variantIndex for getMinorAllele");
  };
  const alleles = getAlleleString(aaData[0])
    .replace(/[\s\%]/g, "")
    .split(/[\,\:]/);
  const allele1 = alleles[0];
  const allele2 = alleles[2];
  let allele1PopSize = 0;
  let allele2PopSize = 0;
  const pop_groups = ["ALL", "AFR", "AMR", "EAS", "EUR", "SAS"];
  for (let i = 0; i < aaData.length; i++) {
    if (!pop_groups.includes(aaData[i][0])) {
      const alleleData = getAlleleString(aaData[i])
        .replace(/[\s\%]/g, "")
        .split(/[\,\:]/);
      const allele1Freq = parseFloat(alleleData[1]);
      const allele2Freq = parseFloat(alleleData[3]);
      if (allele1Freq === allele2Freq) {
        allele1PopSize += aaData[i][1];
        allele2PopSize += aaData[i][1];
      } else if (allele1Freq < allele2Freq) {
        allele1PopSize += aaData[i][1];
      } else {
        allele2PopSize += aaData[i][1];
      }
    }
  }
  if (allele1PopSize === allele2PopSize) {
    return allele1 < allele2 ? allele1 : allele2;
  } else if (allele1PopSize > allele2PopSize) {
    return allele1;
  } else {
    return allele2;
  }
}

export default PopMap;
