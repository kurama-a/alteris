// src/main.tsx
import React from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { PermissionsProvider } from "./auth/Permissions";

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <PermissionsProvider>
        <App />
      </PermissionsProvider>
    </BrowserRouter>
  </React.StrictMode>
);
