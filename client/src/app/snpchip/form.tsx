"use client";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { Row, Col, Form, Button, ButtonGroup, ToggleButton } from "react-bootstrap";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter, usePathname } from "next/navigation";
import { upload, ldassoc, ldassocExample } from "@/services/queries";
import PopSelect, { PopOption } from "@/components/select/pop-select";
import CalculateLoading from "@/components/calculateLoading";
import { useStore } from "@/store";

export interface FormData {
  pop: PopOption[];
  filename: string;
  reference: string;
  columns: {
    chromosome: string;
    position: string;
    pvalue: string;
  };
  calculateRegion: "" | "region" | "gene" | "variant";
  gene: {
    name: string;
    basepair: string;
    index: string;
  };
  region: {
    start: string;
    end: string;
    index: string;
  };
  variant: {
    index: string;
    basepair: string;
  };
  genome_build: "grch37" | "grch38" | "grch38_high_coverage";
  dprime: boolean;
  transcript: boolean;
  annotate: "forge" | "regulome" | "no";
  useEx: boolean;
}

export default function SNPChipForm() {
  const { register, handleSubmit } = useForm<FormData>();
  const onSubmit = (data: FormData) => {
    // Handle form submission
  };

  return (
    <><SNPChipForm /></>
  );
};