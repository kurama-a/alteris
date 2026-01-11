import React from "react";
import { Navigate } from "react-router-dom";
import { useCan } from "../auth/Permissions";

type RequireProps = {
  perm?: string | string[];
  children: React.ReactNode;
};

export default function Require({ perm, children }: RequireProps) {
  if (!perm) return <>{children}</>;
  const ok = useCan(perm);
  return ok ? <>{children}</> : <Navigate to="/login" replace />;
}
