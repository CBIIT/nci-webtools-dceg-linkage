import React from "react";

type ToolCardProps = {
  id: string;
  title: string;
  desc: string;
};

export default function LDToolCard({ id, title, desc }: ToolCardProps) {
  return (
    <div className="card-outside">
      <a className="card anchor-link border-0" href="#" data-dest={id}>
        <div className="text-center card-title">
          <h2 style={{ color: "white", margin: 0, fontSize: "24px" }}>{title}</h2>
        </div>
        <div className="card-body">
          <p>{desc}</p>
        </div>
      </a>
    </div>
  );
}
