import React from "react";
import { Link, Outlet } from "react-router-dom";
import { useMe, useCan } from "../auth/Permissions";

export default function Layout(){
  const me = useMe();
  const canAdmin = useCan("user:manage");
  return (
    <div style={{display:"grid",gridTemplateColumns:"220px 1fr",minHeight:"100vh"}}>
      <aside style={{padding:16,borderRight:"1px solid #ddd"}}>
        <h3>SIGL</h3>
        <nav style={{display:"grid",gap:8}}>
          <Link to="/accueil">Accueil</Link>
          <Link to="/journal">Journal</Link>
          <Link to="/documents">Documents</Link>
          <Link to="/entretiens">Entretiens</Link>
          <Link to="/juries">Juries</Link>
          {canAdmin && <Link to="/admin">Admin</Link>}
          <Link to="/profil">Profil</Link>
          <Link to="/notifications">Notifications</Link>
          <Link to="/recherche">Recherche</Link>
          <Link to="/help">Aide</Link>
        </nav>
        <div style={{marginTop:16, fontSize:12}}>Utilisateur: {me.id}</div>
      </aside>
      <main style={{padding:24}}>
        <Outlet />
      </main>
    </div>
  );
}
