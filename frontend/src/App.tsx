import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import Require from "./components/Require";

// pages
import Login from "./pages/Login";
import Accueil from "./pages/Accueil";
import Journal from "./pages/Journal";
import Documents from "./pages/Documents";
import Entretiens from "./pages/Entretiens";
import Juries from "./pages/Juries";
import Admin from "./pages/Admin";
import Profile from "./pages/Profile";
import Notifications from "./pages/Notifications";
import Recherche from "./pages/Recherche";
import Aide from "./pages/Aide";

export default function App(){
  return (
    <Routes>
      <Route path="/login" element={<Login/>} />
      <Route element={<Layout/>}>
        <Route index element={<Navigate to="/accueil" replace />} />
        <Route path="/accueil" element={<Accueil/>} />
        <Route path="/journal" element={
          <Require perm="journal:read:own"><Journal/></Require>
        }/>
        <Route path="/documents" element={
          <Require perm="doc:read"><Documents/></Require>
        }/>
        <Route path="/entretiens" element={
          <Require perm="meeting:schedule:own"><Entretiens/></Require>
        }/>
        <Route path="/juries" element={
          <Require perm="jury:read"><Juries/></Require>
        }/>
        <Route path="/admin" element={
          <Require perm="user:manage"><Admin/></Require>
        }/>
        <Route path="/profil" element={<Profile/>}/>
        <Route path="/notifications" element={<Notifications/>}/>
        <Route path="/recherche" element={<Recherche/>}/>
        <Route path="/help" element={<Aide/>}/>
      </Route>
    </Routes>
  );
}
