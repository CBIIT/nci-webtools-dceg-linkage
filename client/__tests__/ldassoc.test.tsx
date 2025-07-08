import { render, screen, waitFor } from "@testing-library/react";
import LdAssoc from "../src/app/ldassoc/page";
import "@testing-library/jest-dom";

// Mock child components
jest.mock("../src/app/ldassoc/form", () => () => <div data-testid="ldassoc-form">LDAssocForm</div>);
jest.mock("@/components/calculateLoading", () => () => <div data-testid="calculate-loading">CalculateLoading</div>);
jest.mock("@/components/toolBanner", () => () => <div data-testid="tool-banner">ToolBanner</div>);

// Mock next/navigation
const useSearchParams = jest.fn();
jest.mock("next/navigation", () => ({
  useSearchParams: () => useSearchParams(),
}));

// Mock ErrorBoundary to just render its children
jest.mock("next/dist/client/components/error-boundary", () => ({
  ErrorBoundary: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

describe("LdAssoc Page", () => {
  beforeEach(() => {
    useSearchParams.mockClear();
  });

  test("should render form and banner without results when 'ref' is not in search params", () => {
    useSearchParams.mockReturnValue({
      get: jest.fn().mockReturnValue(null),
    });

    render(<LdAssoc />);

    expect(screen.getByTestId("tool-banner")).toBeInTheDocument();
    expect(screen.getByTestId("ldassoc-form")).toBeInTheDocument();
    expect(screen.queryByTestId("ldassoc-results")).not.toBeInTheDocument();
    expect(screen.queryByTestId("calculate-loading")).not.toBeInTheDocument();
  });

  test("should render only essential components when 'ref' is empty string", () => {
    useSearchParams.mockReturnValue({
      get: jest.fn().mockReturnValue(""),
    });

    render(<LdAssoc />);

    expect(screen.getByTestId("tool-banner")).toBeInTheDocument();
    expect(screen.getByTestId("ldassoc-form")).toBeInTheDocument();
    expect(screen.queryByTestId("ldassoc-results")).not.toBeInTheDocument();
    expect(screen.queryByTestId("calculate-loading")).not.toBeInTheDocument();
  });

  test("should render tool banner with correct props", () => {
    useSearchParams.mockReturnValue({
      get: jest.fn().mockReturnValue(null),
    });

    render(<LdAssoc />); 

    const banner = screen.getByTestId("tool-banner");
    expect(banner).toBeInTheDocument();
    expect(banner).toBeVisible();
  });

  test("should render container with correct bootstrap classes", () => {
    useSearchParams.mockReturnValue({
      get: jest.fn().mockReturnValue(null),
    });

    const { container } = render(<LdAssoc />);
    
    const mainContainer = container.querySelector('.container-md');
    expect(mainContainer).toBeInTheDocument();
    
    const row = container.querySelector('.border.rounded.bg-white.my-3.p-3.shadow-sm');
    expect(row).toBeInTheDocument();
  });

  test("should handle undefined ref parameter", () => {
    useSearchParams.mockReturnValue({
      get: jest.fn().mockReturnValue(undefined),
    });

    render(<LdAssoc />);

    expect(screen.getByTestId("tool-banner")).toBeInTheDocument();
    expect(screen.getByTestId("ldassoc-form")).toBeInTheDocument();
    expect(screen.queryByTestId("ldassoc-results")).not.toBeInTheDocument();
    expect(screen.queryByTestId("calculate-loading")).not.toBeInTheDocument();
  });
});
   
