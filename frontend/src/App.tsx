import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './auth/AuthContext';
import { ToastProvider } from './components/ToastContext';
import { Layout } from './components/Layout';

// Auth Pages
import { Login } from './pages/auth/Login';
import { Signup } from './pages/auth/Signup';
import { ForgotPassword } from './pages/auth/ForgotPassword';
import { ResetPassword } from './pages/auth/ResetPassword';

// Admin & Staff Pages
import { Dashboard } from './pages/admin/Dashboard';
import { Customers } from './pages/admin/Customers';
import { Products } from './pages/admin/Products';
import { Plans } from './pages/admin/Plans';
import { Taxes } from './pages/admin/Taxes';
import { Discounts } from './pages/admin/Discounts';
import { QuotationTemplates } from './pages/admin/QuotationTemplates';
import { Subscriptions } from './pages/admin/Subscriptions';
import { Invoices } from './pages/admin/Invoices';
import { Payments } from './pages/admin/Payments';
import { StaffManagement } from './pages/admin/StaffManagement';

// Customer Portal Pages
import { PortalSubscriptions } from './pages/portal/PortalSubscriptions';
import { PortalInvoices } from './pages/portal/PortalInvoices';
import { PortalProfile } from './pages/portal/PortalProfile';

const RoleBasedHome: React.FC = () => {
  const { isCustomer } = useAuth();
  if (isCustomer) {
    return <Navigate to="/portal/subscriptions" replace />;
  }
  return <Dashboard />;
};

const AdminOnlyRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAdmin } = useAuth();
  if (!isAdmin) {
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
};

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <ToastProvider>
        <AuthProvider>
          <Routes>
            {/* Public Auth Routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password" element={<ResetPassword />} />

            {/* Authenticated Application Shell */}
            <Route element={<Layout />}>
              {/* Home route dynamically routes based on role */}
              <Route path="/" element={<RoleBasedHome />} />

              {/* Admin & Staff Management Routes */}
              <Route path="/customers" element={<Customers />} />
              <Route path="/products" element={<Products />} />
              <Route path="/plans" element={<Plans />} />
              <Route path="/taxes" element={<Taxes />} />
              <Route
                path="/discounts"
                element={
                  <AdminOnlyRoute>
                    <Discounts />
                  </AdminOnlyRoute>
                }
              />
              <Route path="/quotation-templates" element={<QuotationTemplates />} />
              <Route path="/subscriptions" element={<Subscriptions />} />
              <Route path="/invoices" element={<Invoices />} />
              <Route path="/payments" element={<Payments />} />
              <Route
                path="/staff"
                element={
                  <AdminOnlyRoute>
                    <StaffManagement />
                  </AdminOnlyRoute>
                }
              />

              {/* Customer Self-Service Portal Routes */}
              <Route path="/portal/subscriptions" element={<PortalSubscriptions />} />
              <Route path="/portal/invoices" element={<PortalInvoices />} />
              <Route path="/portal/profile" element={<PortalProfile />} />
            </Route>

            {/* Catch-all fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AuthProvider>
      </ToastProvider>
    </BrowserRouter>
  );
};

export default App;
