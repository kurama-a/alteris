import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import RequireAuth from "./components/RequireAuth";
import Require from "./components/Require";

// pages
import Login from "./pages/Login";
import Accueil from "./pages/Accueil";
import Journal from "./pages/Journal";
import Entretiens from "./pages/Entretiens";
import Juries from "./pages/Juries";
import Admin from "./pages/Admin";
import Promotions from "./pages/Promotions";
import Profil from "./pages/Profil";
import Notifications from "./pages/Notifications";
import Recherche from "./pages/Recherche";
import Aide from "./pages/Aide";

export default function App(){
  return (
    <Routes>
      <Route path="/login" element={<Login/>} />
      <Route element={
        <RequireAuth>
          <Layout/>
        </RequireAuth>
      }>
        <Route index element={<Navigate to="/accueil" replace />} />
        <Route path="/accueil" element={<Accueil/>} />
        <Route path="/journal" element={
          <Require perm={["journal:read:own","journal:read:assigned","journal:read:all"]}><Journal/></Require>
        }/>
        <Route path="/entretiens" element={
          <Require perm={["meeting:schedule:own","meeting:schedule:team","meeting:participate"]}><Entretiens/></Require>
        }/>
        <Route path="/juries" element={
          <Require perm="jury:read"><Juries/></Require>
        }/>
        <Route path="/promotions" element={
          <Require perm="promotion:manage"><Promotions/></Require>
        }/>
        <Route path="/admin" element={
          <Require perm="user:manage"><Admin/></Require>
        }/>
        <Route path="/profil" element={<Profil/>}/>
        <Route path="/notifications" element={<Notifications/>}/>
        <Route path="/recherche" element={<Recherche/>}/>
        <Route path="/help" element={<Aide/>}/>
      </Route>
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}
