import Spinner from "react-bootstrap/Spinner";

type LoadingProps = {
  message?: string;
};

export default function Loading({ message }: LoadingProps) {
  // You can add any UI inside Loading, including a Skeleton.
  return (
    <div className="shadow border rounded bg-white p-3 loader text-center">
      <Spinner variant="primary" animation="border" role="status" />
      <div>{message || "Loading"}</div>
    </div>
  );
}
