import { useState } from "react";
import BsTable from "react-bootstrap/Table";
import { Container, Row, Col } from "react-bootstrap";
import {
  flexRender,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  useReactTable,
} from "@tanstack/react-table";

type TableProps = {
  title?: string;
  data: any[];
  columns: any[];
};

export default function Table({ title = "", data, columns, ...props }: TableProps) {
  const [pagination, setPagination] = useState({ pageIndex: 0, pageSize: 10 });
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    onPaginationChange: setPagination,
    getFilteredRowModel: getFilteredRowModel(),
    state: {
      pagination,
    },
  });

  return (
    <Container className="mb-3" tabIndex={0} style={{ maxHeight: "650px" }}>
      <Row className="justify-content-between mb-2">
        <Col sm="auto">
          <h4 className="text-primary-emphasis">{title}</h4>
        </Col>
        <Col />
        <Col sm="auto">
          <input
            value={table.getState().globalFilter ?? ""}
            onChange={(e) => table.setGlobalFilter(String(e.target.value))}
            placeholder="Search..."
          />
        </Col>
      </Row>
      <Row>
        <Col>
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
        </Col>
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
