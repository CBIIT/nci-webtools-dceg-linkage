import Form from "react-bootstrap/Form";
import { useStore } from "@/store";

export default function GenomeSelect() {
  const genome_build = useStore((state) => state.genome_build);
  const setGenomeBuild = useStore((state) => state.setGenomeBuild);

  return (
    <Form.Group controlId="genome_build" className="mb-3">
      <Form.Label>Genome Build (1000G)</Form.Label>
      <Form.Select value={genome_build} onChange={(e) => setGenomeBuild(e.target.value)}>
        <option value="grch37">GRCh37</option>
        <option value="grch38">GRCh38</option>
        <option value="grch38_high_coverage">GRCh38 High Coverage</option>
      </Form.Select>
    </Form.Group>
  );
}
