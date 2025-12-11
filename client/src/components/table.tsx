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
  responsive?: boolean;
  initialSort?: { id: string; desc: boolean }[];
};

export default function Table({ responsive = true, title = "", data, columns, initialSort, ...props }: TableProps) {
  const [pagination, setPagination] = useState({ pageIndex: 0, pageSize: 10 });
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    onPaginationChange: setPagination,
    getFilteredRowModel: getFilteredRowModel(),
    initialState: {
      sorting: initialSort,
    },
    state: {
      pagination,
    },
  });

  return (
    <Container className="mb-3" tabIndex={0}>
      <Row className="justify-content-between mb-2">
        <Col sm="auto">
          <h5>{title}</h5>
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
      <BsTable responsive={responsive} hover {...props}>
        <thead title="Shift-click column headers to sort by multiple levels">
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
                          asc: <i className="bi bi-chevron-up" />,
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
      <Row className="justify-content-between">
        <Col sm="auto">
          <select
            title="Select page size"
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
        <Col sm="auto">
          {(() => {
            const { pageIndex, pageSize } = table.getState().pagination;
            const totalRows = table.getFilteredRowModel().rows.length;
            const startRow = pageIndex * pageSize + 1;
            const endRow = Math.min((pageIndex + 1) * pageSize, totalRows);

            return totalRows > 0 ? `Showing ${startRow} to ${endRow} of ${totalRows} entries` : "No entries to show";
          })()}
        </Col>
        <Col sm="auto">
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
          Page{" "}
          <strong>
            {table.getState().pagination.pageIndex + 1} of {table.getPageCount()}
          </strong>
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
      </Row>
    </Container>
  );
}
