import React from "react";
import { Navigate } from "react-router-dom";
import { useCan } from "../auth/Permissions";

export default function Require({ perm, children }:{ perm?: string; children: React.ReactNode }) {
  if (!perm) return <>{children}</>;
  const ok = useCan(perm);
  return ok ? <>{children}</> : <Navigate to="/login" replace />;
}