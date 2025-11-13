import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import AdminDashboard from './pages/AdminDashboard';
import ProtectedRoute from './components/ProtectedRoute';

const App = () => {
  return (
    <Router>
      <Routes>
        {/* Ruta de Login (pública) */}
        <Route path="/login" element={<Login />} />
        
        {/* Ruta del Dashboard de Admin (protegida) */}
        <Route 
          path="/admin/dashboard" 
          element={
            <ProtectedRoute>
              <AdminDashboard />
            </ProtectedRoute>
          } 
        />
        
        {/* Redirigir a login por defecto */}
        <Route path="/" element={<Navigate to="/login" />} />
        
        {/* Agrega aquí más rutas protegidas */}
        {/* 
        <Route 
          path="/productos" 
          element={
            <ProtectedRoute>
              <Productos />
            </ProtectedRoute>
          } 
        />
        */}
      </Routes>
    </Router>
  );
};

export default App;
