"use client";
import Table from "@/components/table";
import { createColumnHelper } from "@tanstack/react-table";
import PopSelect from "@/components/select/pop-select";
import { useForm } from "react-hook-form";
import { Row, Col, Container, Form, Button } from "react-bootstrap";

export default function LdAssoc(props) {
  //   type Person = {
  //     name: string;
  //     value: number;
  //   };

  //   const columnHelper = createColumnHelper<Person>();

  //   const data = [
  //     { name: "Test", value: 1 },
  //     { name: "Test2", value: 2 },
  //   ];
  //   const columns = [
  //     columnHelper.accessor("name", {
  //       header: "Name",
  //       cell: (info) => info.getValue(),
  //     }),
  //     columnHelper.accessor("value", {
  //       header: "Value",
  //       cell: (info) => info.getValue(),
  //     }),
  //   ];

  const { control, register, handleSubmit, reset } = useForm();

  const onSubmit = (data) => {
    console.log(data);
  };

  function onReset(event) {
    event.preventDefault();
    // router.push("/cansurv", { shallow: false });
    // reset(defaultForm);
    // resetStore();
    // queryClient.invalidateQueries();
  }

  return (
    <Container>
      {/* <Table title="title" data={data} columns={columns} /> */}
      <Form onSubmit={handleSubmit(onSubmit)} onReset={onReset}>
        <Form.Group controlId="file" className="mb-3">
          <Form.Label>File</Form.Label>
          <Form.Control type="text" placeholder="Enter name" {...register("name")} />
        </Form.Group>
        <Form.Group controlId="pop" className="mb-3">
          <PopSelect name="pop" control={control} />
        </Form.Group>

        <div className="text-end">
          <Button type="reset" variant="outline-danger" className="me-1">
            Reset
          </Button>
          <Button type="submit" variant="primary">
            Submit
          </Button>
        </div>
      </Form>
    </Container>
  );
}
