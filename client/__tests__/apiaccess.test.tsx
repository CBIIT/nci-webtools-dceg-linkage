"use client";
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import ApiAccessPage from "../src/app/apiaccess/page";

// Mock next/image
jest.mock("next/image", () => ({
  __esModule: true,
  default: (props: any) => {
    // eslint-disable-next-line @next/next/no-img-element
    return <img {...props} alt={props.alt} />;
  },
}));

global.fetch = jest.fn();

describe("ApiAccessPage", () => {
  beforeEach(() => {
    (fetch as jest.Mock).mockClear();
    render(<ApiAccessPage />);
  });

  it("renders the form correctly", () => {
    expect(screen.getByLabelText(/First name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Last name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Institution/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Register/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Reset/i })).toBeInTheDocument();
  });

  it("allows users to fill out the form", () => {
    fireEvent.change(screen.getByLabelText(/First name/i), { target: { value: "John" } });
    fireEvent.change(screen.getByLabelText(/Last name/i), { target: { value: "Doe" } });
    fireEvent.change(screen.getByLabelText(/Email/i), { target: { value: "john.doe@example.com" } });
    fireEvent.change(screen.getByLabelText(/Institution/i), { target: { value: "Test University" } });

    expect(screen.getByLabelText(/First name/i)).toHaveValue("John");
    expect(screen.getByLabelText(/Last name/i)).toHaveValue("Doe");
    expect(screen.getByLabelText(/Email/i)).toHaveValue("john.doe@example.com");
    expect(screen.getByLabelText(/Institution/i)).toHaveValue("Test University");
  });

  it("handles successful registration for a new user", async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        registered: true,
        blocked: false,
        email: "john.doe@example.com",
        message: "Registration Successful",
      }),
    });

    fireEvent.change(screen.getByLabelText(/First name/i), { target: { value: "John" } });
    fireEvent.change(screen.getByLabelText(/Last name/i), { target: { value: "Doe" } });
    fireEvent.change(screen.getByLabelText(/Email/i), { target: { value: "john.doe@example.com" } });
    fireEvent.change(screen.getByLabelText(/Institution/i), { target: { value: "Test University" } });

    fireEvent.click(screen.getByRole("button", { name: /Register/i }));

    await waitFor(() => {
      expect(screen.getByRole("status")).toBeInTheDocument(); // Spinner
    });

    await waitFor(() => {
      expect(screen.getByText("Registration Successful")).toBeInTheDocument();
    });

    expect(screen.getByText(/Your API token has been sent to the email:/i)).toBeInTheDocument();
    expect(screen.getByText("john.doe@example.com")).toBeInTheDocument();
  });

  it("handles registration for an existing user", async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        registered: true,
        blocked: false,
        email: "jane.doe@example.com",
        message: "You have already registered.",
      }),
    });

    fireEvent.change(screen.getByLabelText(/First name/i), { target: { value: "Jane" } });
    fireEvent.change(screen.getByLabelText(/Last name/i), { target: { value: "Doe" } });
    fireEvent.change(screen.getByLabelText(/Email/i), { target: { value: "jane.doe@example.com" } });
    fireEvent.change(screen.getByLabelText(/Institution/i), { target: { value: "Another University" } });

    fireEvent.click(screen.getByRole("button", { name: /Register/i }));

    await waitFor(() => {
      expect(screen.getByText("You have already registered.")).toBeInTheDocument();
    });
  });

  it("handles registration failure from the API", async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      text: async () => "Registration failed.",
    });

    fireEvent.change(screen.getByLabelText(/First name/i), { target: { value: "John" } });
    fireEvent.change(screen.getByLabelText(/Last name/i), { target: { value: "Doe" } });
    fireEvent.change(screen.getByLabelText(/Email/i), { target: { value: "john.doe@example.com" } });
    fireEvent.change(screen.getByLabelText(/Institution/i), { target: { value: "Test University" } });

    fireEvent.click(screen.getByRole("button", { name: /Register/i }));

    await waitFor(() => {
      expect(screen.getByText("Registration failed.")).toBeInTheDocument();
    });
  });

  it("resets the form when reset button is clicked", () => {
    fireEvent.change(screen.getByLabelText(/First name/i), { target: { value: "John" } });
    fireEvent.change(screen.getByLabelText(/Last name/i), { target: { value: "Doe" } });
    fireEvent.change(screen.getByLabelText(/Email/i), { target: { value: "john.doe@example.com" } });
    fireEvent.change(screen.getByLabelText(/Institution/i), { target: { value: "Test University" } });

    fireEvent.click(screen.getByRole("button", { name: /Reset/i }));

    expect(screen.getByLabelText(/First name/i)).toHaveValue("");
    expect(screen.getByLabelText(/Last name/i)).toHaveValue("");
    expect(screen.getByLabelText(/Email/i)).toHaveValue("");
    expect(screen.getByLabelText(/Institution/i)).toHaveValue("");
  });

  it("handles network failure", async () => {
    (fetch as jest.Mock).mockRejectedValueOnce(new Error("Network error"));

    fireEvent.change(screen.getByLabelText(/First name/i), { target: { value: "John" } });
    fireEvent.change(screen.getByLabelText(/Last name/i), { target: { value: "Doe" } });
    fireEvent.change(screen.getByLabelText(/Email/i), { target: { value: "john.doe@example.com" } });
    fireEvent.change(screen.getByLabelText(/Institution/i), { target: { value: "Test University" } });

    fireEvent.click(screen.getByRole("button", { name: /Register/i }));

    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });
  });

  it("resets the form when done button is clicked in modal", async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        registered: true,
        blocked: false,
        email: "john.doe@example.com",
        message: "Registration Successful",
      }),
    });

    fireEvent.change(screen.getByLabelText(/First name/i), { target: { value: "John" } });
    fireEvent.change(screen.getByLabelText(/Last name/i), { target: { value: "Doe" } });
    fireEvent.change(screen.getByLabelText(/Email/i), { target: { value: "john.doe@example.com" } });
    fireEvent.change(screen.getByLabelText(/Institution/i), { target: { value: "Test University" } });

    fireEvent.click(screen.getByRole("button", { name: /Register/i }));

    await waitFor(() => {
      expect(screen.getByText("Registration Successful")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /Done/i }));

    expect(screen.getByLabelText(/First name/i)).toHaveValue("");
    expect(screen.getByLabelText(/Last name/i)).toHaveValue("");
    expect(screen.getByLabelText(/Email/i)).toHaveValue("");
    expect(screen.getByLabelText(/Institution/i)).toHaveValue("");
  });

  it("handles registration error from the API in modal", async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        registered: false,
        blocked: false,
        email: "john.doe@example.com",
        message: "Error: Registration failed.",
      }),
    });

    fireEvent.change(screen.getByLabelText(/First name/i), { target: { value: "John" } });
    fireEvent.change(screen.getByLabelText(/Last name/i), { target: { value: "Doe" } });
    fireEvent.change(screen.getByLabelText(/Email/i), { target: { value: "john.doe@example.com" } });
    fireEvent.change(screen.getByLabelText(/Institution/i), { target: { value: "Test University" } });

    fireEvent.click(screen.getByRole("button", { name: /Register/i }));

    await waitFor(() => {
      expect(screen.getByText("Error: Registration failed.")).toBeInTheDocument();
    });

    expect(screen.getByText(/An error occurred during registration/i)).toBeInTheDocument();
  });
});