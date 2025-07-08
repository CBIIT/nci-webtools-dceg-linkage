"use client";
import { useEffect, useRef } from "react";
import Image from "next/image";
import { Row, Col, Container, Dropdown } from "react-bootstrap";
import { useQuery, useSuspenseQuery } from "@tanstack/react-query";
import { createColumnHelper } from "@tanstack/react-table";
import Table from "@/components/table";
import { fetchOutput, fetchOutputStatus } from "@/services/queries";
import { embed } from "@bokeh/bokehjs";
import { FormData } from "./form";

export default function SNPChipResults({ ref }: { ref: string }) {
};