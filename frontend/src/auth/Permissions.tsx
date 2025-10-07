import React from "react";

export type Perm = string;
export type Me = { id: string; roles: string[]; perms: Perm[] };
type Ctx = { me: Me };

const Ctx = React.createContext<Ctx | null>(null);
export const PermissionsProvider = ({ me, children }:{ me:Me; children:React.ReactNode}) =>
  <Ctx.Provider value={{ me }}>{children}</Ctx.Provider>;

export function useMe(){ const c=React.useContext(Ctx); if(!c) throw new Error("No ctx"); return c.me; }
export function useCan(perm: Perm){ const { perms } = useMe(); return perms.includes(perm); }
