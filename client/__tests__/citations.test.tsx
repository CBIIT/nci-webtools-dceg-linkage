import { render, screen } from "@testing-library/react";
import CitationPage from "../src/app/citations/page";
import "@testing-library/jest-dom";

// Mock next/image component
jest.mock("next/image", () => ({
  __esModule: true,
  default: (props: any) => <img {...props} />,
}));

describe("CitationPage", () => {
  beforeEach(() => {
    render(<CitationPage />);
  });

  test("renders without crashing", () => {
    expect(screen.getByRole("heading", { level: 2 })).toBeInTheDocument();
  });

  test("renders container with correct className", () => {
    const container = document.querySelector(".container");
    expect(container).toHaveClass("py-4");
  });

  test("renders LDlink logo image with correct props", () => {
    const image = screen.getByRole("img");
    expect(image).toHaveAttribute("src", "/images/LDlink_logo_small_clear.png");
    expect(image).toHaveAttribute("alt", "LDlink");
    expect(image).toHaveAttribute("width", "91");
    expect(image).toHaveAttribute("height", "36");
  });

  test("displays correct heading text", () => {
    const heading = screen.getByRole("heading", { level: 2 });
    expect(heading).toHaveTextContent(/Citations/);
  });

  test("displays introduction text", () => {
    expect(screen.getByText(/Thank you for using LDlink!/)).toBeInTheDocument();
  });

  test("renders all citation links with correct attributes", () => {
    const links = screen.getAllByRole("link");
    expect(links).toHaveLength(6);

    links.forEach(link => {
      expect(link).toHaveAttribute("target", "_blank");
      expect(link).toHaveAttribute("rel", "noopener noreferrer");
    });
  });

  test("renders specific citation links", () => {
    const ldlinkCitation = screen.getByTitle("LDlink PubMed link");
    expect(ldlinkCitation).toHaveAttribute("href", "http://www.ncbi.nlm.nih.gov/pubmed/?term=26139635");

    const ldexpressCitation = screen.getByTitle("LDexpress");
    expect(ldexpressCitation).toHaveAttribute("href", "https://doi.org/10.1186/s12859-021-04531-8");
  });

  test("renders journal names in italics", () => {
    const italicizedText = screen.getAllByText(/Bioinformatics|BMC Bioinformatics|Front. Genet|Cancer Research/, {
      selector: "i",
    });
    expect(italicizedText.length).toBeGreaterThan(0);
  });
});