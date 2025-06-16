import { useState } from "react";
import BsTable from "react-bootstrap/Table";
import { Container, Row, Col } from "react-bootstrap";
import {
  flexRender,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";

export default function Table({ data, columns, ...props }) {
  const [pagination, setPagination] = useState({ pageIndex: 0, pageSize: 10 });
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    onPaginationChange: setPagination,
    state: {
      pagination,
    },
  });

  return (
    <Container className="mb-3" tabIndex={0} style={{ maxHeight: "650px" }}>
      <Row>
        <BsTable striped bordered {...props}>
          <thead>
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th key={header.id} colSpan={header.colSpan}>
                    {header.isPlaceholder ? null : (
                      <>
                        <div
                          {...{
                            className: header.column.getCanSort() ? "cursor-pointer select-none" : "",
                            onClick: header.column.getToggleSortingHandler(),
                          }}>
                          {flexRender(header.column.columnDef.header, header.getContext())}
                          {{
                            asc: <i className="bi bi-chevron-down" />,
                            desc: <i className="bi bi-chevron-down" />,
                          }[header.column.getIsSorted() as string] ?? <i className="bi bi-chevron-expand" />}
                        </div>
                      </>
                    )}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr key={row.id}>
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </BsTable>
      </Row>
      <Row className="align-items-center">
        <Col sm="auto">
          Page{" "}
          <strong>
            {table.getState().pagination.pageIndex + 1} of {table.getPageCount()}
          </strong>
        </Col>
        <Col>
          <button
            className="border rounded p-1 mx-1"
            onClick={() => table.setPageIndex(0)}
            disabled={!table.getCanPreviousPage()}>
            {"<<"}
          </button>
          <button
            className="border rounded p-1 mx-1"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}>
            {"<"}
          </button>
          <button
            className="border rounded p-1 mx-1"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}>
            {">"}
          </button>
          <button
            className="border rounded p-1 mx-1"
            onClick={() => table.setPageIndex(table.getPageCount() - 1)}
            disabled={!table.getCanNextPage()}>
            {">>"}
          </button>
        </Col>
        <Col sm="auto">
          Show{" "}
          <select
            value={table.getState().pagination.pageSize}
            onChange={(e) => {
              table.setPageSize(Number(e.target.value));
            }}>
            {[10, 25, 50, 100].map((pageSize) => (
              <option key={pageSize} value={pageSize}>
                {pageSize}
              </option>
            ))}
          </select>{" "}
          entries
        </Col>
      </Row>
    </Container>
  );
}
