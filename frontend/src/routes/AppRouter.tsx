import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from '../pages/LoginPage';
import ApprentiDashboard from '../pages/ApprentiDashboard';
import TuteurDashboard from '../pages/TuteurDashboard';

const AppRouter: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/apprenti" element={<ApprentiDashboard />} />
        <Route path="/tuteur" element={<TuteurDashboard />} />
        {/* Redirection par défaut */}
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </BrowserRouter>
  );
};

export default AppRouter;