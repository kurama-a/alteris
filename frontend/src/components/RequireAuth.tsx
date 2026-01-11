import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../auth/Permissions";

type RequireAuthProps = {
  children: React.ReactElement;
};

export default function RequireAuth({ children }: RequireAuthProps) {
  const { me, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return null;
  }

  if (!me) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}
