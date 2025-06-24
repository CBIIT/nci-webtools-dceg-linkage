"use client";
import { Row, Col, Container, Form, Button } from "react-bootstrap";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { createColumnHelper } from "@tanstack/react-table";
import Table from "@/components/table";

export default function LdAssocResults() {
    type Person = {
      name: string;
      value: number;
    };

    const columnHelper = createColumnHelper<Person>();

    const data = [
      { name: "Test", value: 1 },
      { name: "Test2", value: 2 },
    ];
    const columns = [
      columnHelper.accessor("name", {
        header: "Name",
        cell: (info) => info.getValue(),
      }),
      columnHelper.accessor("value", {
        header: "Value",
        cell: (info) => info.getValue(),
      }),
    ];


  return (
    <Container fluid="md">
      <Table title="title" data={data} columns={columns} />
    </Container>
  );
}
