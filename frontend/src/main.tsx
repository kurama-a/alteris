// src/main.tsx
import React from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { PermissionsProvider } from "./auth/Permissions";

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <PermissionsProvider me={{ id:"1", roles:["Apprentis"], perms:[
        "journal:read:own","journal:create:own","doc:read","doc:create","meeting:schedule:own","jury:read"
      ]}}>
        <App />
      </PermissionsProvider>
    </BrowserRouter>
  </React.StrictMode>
);
