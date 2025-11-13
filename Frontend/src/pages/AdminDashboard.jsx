import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  BarChart, Bar, LineChart, Line, PieChart, Pie, 
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, 
  ResponsiveContainer, Cell 
} from 'recharts';
import '../styles/AdminDashboard.css';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

const AdminDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const token = localStorage.getItem('access_token');
      
      const response = await fetch('http://localhost:8000/api/v1/analytics/dashboard', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Error al cargar datos del dashboard');
      }

      const data = await response.json();
      setDashboardData(data);
    } catch (error) {
      console.error('Error fetching dashboard:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    // Eliminar token y datos del usuario
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_email');
    
    // Redirigir al login
    navigate('/login');
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Cargando dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <h2>❌ Error</h2>
        <p>{error}</p>
        <button onClick={fetchDashboardData}>Reintentar</button>
      </div>
    );
  }

  if (!dashboardData) {
    return <div className="error-container">No hay datos disponibles</div>;
  }

  const userEmail = localStorage.getItem('user_email') || 'Admin';

  return (
    <div className="dashboard-container">
      {/* Header con usuario y logout */}
      <div className="dashboard-header">
        <h1 className="dashboard-title">📊 Dashboard de Analytics</h1>
        <div className="user-menu">
          <span className="user-email">👤 {userEmail}</span>
          <button onClick={handleLogout} className="logout-button">
            Cerrar Sesión
          </button>
        </div>
      </div>

      {/* ========== TARJETAS PRINCIPALES ========== */}
      <div className="stats-cards">
        <div className="stat-card stat-card-revenue">
          <div className="stat-icon">💰</div>
          <div className="stat-content">
            <h3>Ingresos</h3>
            <p className="stat-value">${dashboardData.sales.total_sales.toLocaleString()}</p>
            <span className="stat-label">Total de ventas</span>
          </div>
        </div>
        
        <div className="stat-card stat-card-orders">
          <div className="stat-icon">🛒</div>
          <div className="stat-content">
            <h3>Ventas</h3>
            <p className="stat-value">{dashboardData.sales.total_orders}</p>
            <span className="stat-label">Pedidos totales</span>
          </div>
        </div>
        
        <div className="stat-card stat-card-subscribers">
          <div className="stat-icon">👥</div>
          <div className="stat-content">
            <h3>Suscriptores Activos</h3>
            <p className="stat-value">{dashboardData.subscriptions.active_subscriptions}</p>
            <span className="stat-label">De {dashboardData.subscriptions.total_subscriptions} totales</span>
          </div>
        </div>
        
        <div className="stat-card stat-card-products">
          <div className="stat-icon">📦</div>
          <div className="stat-content">
            <h3>Productos</h3>
            <p className="stat-value">{dashboardData.total_products}</p>
            <span className="stat-label">{dashboardData.low_stock_products} con stock bajo</span>
          </div>
        </div>
      </div>

      {/* ========== PRODUCTO TOP ========== */}
      {dashboardData.top_product && (
        <div className="top-product-section">
          <h2>🏆 Producto Top del Momento</h2>
          <div className="top-product-card">
            <img 
              src={dashboardData.top_product.image_url || 'https://via.placeholder.com/120'} 
              alt={dashboardData.top_product.name}
              onError={(e) => e.target.src = 'https://via.placeholder.com/120'}
            />
            <div className="product-info">
              <h3>{dashboardData.top_product.name}</h3>
              <p className="product-meta">
                {dashboardData.top_product.brand} • {dashboardData.top_product.category}
              </p>
              <div className="product-stats">
                <span className="product-stat">
                  <strong>Vendidos:</strong> {dashboardData.top_product.total_sold}
                </span>
                <span className="product-stat">
                  <strong>Ingresos:</strong> ${dashboardData.top_product.total_revenue.toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========== RESUMEN HOY ========== */}
      <div className="today-summary">
        <h2>📊 Resumen de Hoy</h2>
        <div className="summary-grid">
          <div className="summary-item">
            <span className="summary-label">Ventas Totales</span>
            <span className="summary-value">
              ${dashboardData.today_summary.total_sales.toFixed(2)}
            </span>
          </div>
          <div className="summary-item">
            <span className="summary-label">Pedidos Totales</span>
            <span className="summary-value">
              {dashboardData.today_summary.total_orders}
            </span>
          </div>
          <div className="summary-item">
            <span className="summary-label">Productos Vendidos</span>
            <span className="summary-value">
              {dashboardData.today_summary.total_products_sold}
            </span>
          </div>
          <div className="summary-item">
            <span className="summary-label">Nuevos Suscriptores</span>
            <span className="summary-value">
              {dashboardData.today_summary.new_subscriptions}
            </span>
          </div>
        </div>
      </div>

      {/* ========== GRÁFICAS ========== */}
      <div className="charts-grid">
        {/* Ventas Mensuales */}
        <div className="chart-container">
          <h2>📈 Ventas Mensuales</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={dashboardData.monthly_sales}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip 
                formatter={(value) => `$${value.toLocaleString()}`}
                contentStyle={{ backgroundColor: 'white', border: '1px solid #ccc' }}
              />
              <Legend />
              <Bar dataKey="sales" fill="#8884d8" name="Ventas ($)" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Nuevos Suscriptores */}
        <div className="chart-container">
          <h2>👥 Nuevos Suscriptores</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={dashboardData.subscriber_growth}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip 
                contentStyle={{ backgroundColor: 'white', border: '1px solid #ccc' }}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="new_subscribers" 
                stroke="#82ca9d" 
                name="Nuevos Suscriptores" 
                strokeWidth={2}
                dot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Categorías Top */}
        <div className="chart-container">
          <h2>🎯 Categorías Top</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={dashboardData.category_sales}
                dataKey="total_sales"
                nameKey="category"
                cx="50%"
                cy="50%"
                outerRadius={80}
                label={(entry) => `${entry.category}: ${entry.percentage}%`}
              >
                {dashboardData.category_sales.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip 
                formatter={(value) => `$${value.toLocaleString()}`}
                contentStyle={{ backgroundColor: 'white', border: '1px solid #ccc' }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Suscriptores Activos */}
        <div className="chart-container">
          <h2>✅ Suscriptores Activos</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={dashboardData.subscriber_growth}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip 
                contentStyle={{ backgroundColor: 'white', border: '1px solid #ccc' }}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="total_active" 
                stroke="#0088FE" 
                name="Suscriptores Activos" 
                strokeWidth={2}
                dot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Productos Más Vendidos */}
        <div className="chart-container full-width">
          <h2>🔥 Productos Más Vendidos</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart 
              data={dashboardData.sales.top_selling_products.slice(0, 5)}
              layout="vertical"
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="name" type="category" width={200} />
              <Tooltip 
                contentStyle={{ backgroundColor: 'white', border: '1px solid #ccc' }}
              />
              <Legend />
              <Bar dataKey="total_sold" fill="#FF8042" name="Unidades Vendidas" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
