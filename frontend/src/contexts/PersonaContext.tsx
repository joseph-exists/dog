// src/contexts/PersonaContext.tsx
// TODO: add decision process to readme and development guide
// Client-State to Persist
// Selected Persona ID: This is the most critical piece of state we need to persist.
// When a user selects a persona, we need to store this selection so it remains available throughout the application.
// Selection Status: We need to track whether a user has completed the persona selection process.
// UI State: Any animation states, expanded/collapsed states, or other UI-related states that improve user experience.

// I'm not sure if I'm going to keep tanstack, so went with react context instead -
// cleaner separation of concerns
// handles persistence across refresh more cleanly
// appears to work more fluidly with GSAP

import React, { createContext, useContext, useState, useEffect, useMemo } from "react";

interface PersonaContextType {
  selectedPersonaId: string | null;
  selectionComplete: boolean;
  selectPersona: (personaId: string) => void;
  clearSelection: () => void;
}

const PersonaContext = createContext<PersonaContextType | undefined>(undefined);

interface PersonaProviderProps {
  children: React.ReactNode;
}

export const PersonaProvider = ({ children }: PersonaProviderProps) => {
  const [selectedPersonaId, setSelectedPersonaId] = useState<string | null>(
    () => {
      // Initialize from localStorage
      return localStorage.getItem("selectedPersonaId");
    },
  );

  const [selectionComplete, setSelectionComplete] = useState<boolean>(() => {
    return localStorage.getItem("personaSelectionComplete") === "true";
  });

  // Update localStorage when state changes
  useEffect(() => {
    if (selectedPersonaId) {
      localStorage.setItem("selectedPersonaId", selectedPersonaId);
    } else {
      localStorage.removeItem("selectedPersonaId");
    }
  }, [selectedPersonaId]);

  useEffect(() => {
    if (selectionComplete) {
      localStorage.setItem("personaSelectionComplete", "true");
    } else {
      localStorage.removeItem("personaSelectionComplete");
    }
  }, [selectionComplete]);

  const selectPersona = (personaId: string) => {
    setSelectedPersonaId(personaId);
    setSelectionComplete(true);
  };

  const clearSelection = () => {
    setSelectedPersonaId(null);
    setSelectionComplete(false);
  };

  const contextValue = useMemo(() => ({
    selectedPersonaId,
    selectionComplete,
    selectPersona,
    clearSelection,
  }), [selectedPersonaId, selectionComplete]);

  return (
    <PersonaContext.Provider value={contextValue}>
      {children}
    </PersonaContext.Provider>
  );
};

export const usePersona = () => {
  const context = useContext(PersonaContext);
  if (context === undefined) {
    throw new Error("usePersona must be used within a PersonaProvider");
  }
  return context;
};
