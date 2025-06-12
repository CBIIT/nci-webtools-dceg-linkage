// components/ToolCard.tsx
type ToolCardProps = {
  id: string;
  title: string;
  description: string;
};

export default function ToolCard({ id, title, description }: ToolCardProps) {
  return (
    <div className="col-md-4" style={{ marginBottom: 30 }}>
      <a className="card anchor-link" href={`#${id}-tab`} data-dest={id}>
        <div className="text-center card-title">
          <h2 style={{ color: "white", fontSize: 24, margin: 0 }}>{title}</h2>
        </div>
        <div className="card-body" style={{ color: "white" }}>
          <p>{description}</p>
        </div>
      </a>
    </div>
  );
}
