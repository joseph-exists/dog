// tests/components/PersonaCard.test.tsx
import { render, screen, fireEvent } from "@testing-library/react";
import { PersonaCard } from "@/components/Common/PersonaCard";

// Mock persona data
const mockPersona = {
  id: "1",
  name: "Test Persona",
  description: "A test persona description",
  general_domain: "Testing",
  specific_domain: "Unit Testing",
  created_at: "2023-01-01T00:00:00Z"
};

describe("PersonaCard", () => {
  test("renders persona information correctly", () => {
    render(<PersonaCard persona={mockPersona} />);

    expect(screen.getByText("Test Persona")).toBeInTheDocument();
    expect(screen.getByText("A test persona description")).toBeInTheDocument();
    expect(screen.getByText("Testing")).toBeInTheDocument();
    expect(screen.getByText("Specific Domain: Unit Testing")).toBeInTheDocument();
  });

  test("triggers selection when clicked if selectable", () => {
    const onSelectMock = jest.fn();

    render(
      <PersonaCard
        persona={mockPersona}
        isSelectable={true}
        onSelect={onSelectMock}
      />
    );

    fireEvent.click(screen.getByText("Select Persona"));
    expect(onSelectMock).toHaveBeenCalledTimes(1);
  });

  test("shows selected state when isSelected is true", () => {
    render(
      <PersonaCard
        persona={mockPersona}
        isSelectable={true}
        isSelected={true}
      />
    );

    expect(screen.getByText("Selected")).toBeInTheDocument();
  });
});

// tests/components/PersonaSelection.test.tsx
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { PersonaSelection } from "@/components/Personas/PersonaSelection";
import { PersonasService } from "@/client";

// Mock the PersonasService
jest.mock("@/client", () => ({
  PersonasService: {
    readPersonas: jest.fn(),
  },
}));

// Create a new QueryClient for each test
const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

describe("PersonaSelection", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("shows loading state initially", () => {
    (PersonasService.readPersonas as jest.Mock).mockReturnValueOnce(
      new Promise(() => {})
    );

    render(
      <QueryClientProvider client={createTestQueryClient()}>
        <PersonaSelection />
      </QueryClientProvider>
    );

    expect(screen.getByRole("status")).toBeInTheDocument(); // spinner
  });

  test("shows personas when data is loaded", async () => {
    (PersonasService.readPersonas as jest.Mock).mockResolvedValueOnce({
      data: [
        {
          id: "1",
          name: "Persona 1",
          description: "Description 1",
          general_domain: "Domain 1",
          created_at: "2023-01-01T00:00:00Z"
        },
        {
          id: "2",
          name: "Persona 2",
          description: "Description 2",
          general_domain: "Domain 2",
          created_at: "2023-01-01T00:00:00Z"
        },
      ],
      count: 2
    });

    render(
      <QueryClientProvider client={createTestQueryClient()}>
        <PersonaSelection />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText("Persona 1")).toBeInTheDocument();
      expect(screen.getByText("Persona 2")).toBeInTheDocument();
    });
  });

  test("handles persona selection correctly", async () => {
    (PersonasService.readPersonas as jest.Mock).mockResolvedValueOnce({
      data: [
        {
          id: "1",
          name: "Persona 1",
          description: "Description 1",
          general_domain: "Domain 1",
          created_at: "2023-01-01T00:00:00Z"
        },
        {
          id: "2",
          name: "Persona 2",
          description: "Description 2",
          general_domain: "Domain 2",
          created_at: "2023-01-01T00:00:00Z"
        },
      ],
      count: 2
    });

    render(
      <QueryClientProvider client={createTestQueryClient()}>
        <PersonaSelection />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText("Persona 1")).toBeInTheDocument();
    });

    // Select the first persona
    fireEvent.click(screen.getAllByText("Select Persona")[0]);

    // Confirm selection is disabled until selection made
    expect(screen.getByText("Confirm Selection")).toBeEnabled();
  });
});
