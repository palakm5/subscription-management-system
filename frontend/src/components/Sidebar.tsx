import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  Package,
  Layers,
  Receipt,
  Tag,
  FileSpreadsheet,
  Repeat,
  FileText,
  CreditCard,
  UserCheck,
  User,
  Zap
} from 'lucide-react';
import { useAuth } from '../auth/AuthContext';

export const Sidebar: React.FC = () => {
  const { user, isAdmin, isStaff, isCustomer } = useAuth();

  const adminLinks = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/customers', label: 'Customers', icon: Users },
    { to: '/products', label: 'Products & Variants', icon: Package },
    { to: '/plans', label: 'Subscription Plans', icon: Layers },
    { to: '/taxes', label: 'Tax Rules', icon: Receipt },
    { to: '/discounts', label: 'Discounts', icon: Tag, adminOnly: true },
    { to: '/quotation-templates', label: 'Quote Templates', icon: FileSpreadsheet },
    { to: '/subscriptions', label: 'Subscriptions', icon: Repeat },
    { to: '/invoices', label: 'Invoices', icon: FileText },
    { to: '/payments', label: 'Payments', icon: CreditCard },
    { to: '/staff', label: 'Staff Team', icon: UserCheck, adminOnly: true },
  ];

  const customerLinks = [
    { to: '/portal/subscriptions', label: 'My Subscriptions', icon: Repeat },
    { to: '/portal/invoices', label: 'My Invoices', icon: FileText },
    { to: '/portal/profile', label: 'Account Profile', icon: User },
  ];

  const links = isCustomer ? customerLinks : adminLinks.filter((l) => !l.adminOnly || isAdmin);

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col shrink-0 min-h-screen">
      {/* Brand logo */}
      <div className="h-16 flex items-center px-6 border-b border-slate-100 gap-3">
        <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold text-base shadow-xs">
          B
        </div>
        <div>
          <span className="font-bold text-slate-900 tracking-tight text-base">Brightloop</span>
          <span className="block text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
            {isCustomer ? 'Customer Portal' : 'Billing Console'}
          </span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {links.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-50 text-blue-700 font-semibold'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                }`
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* User profile footer */}
      <div className="p-4 border-t border-slate-100 bg-slate-50/50 flex items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-slate-200 text-slate-700 font-medium flex items-center justify-center text-xs">
          {user?.email.substring(0, 2).toUpperCase()}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-semibold text-slate-800 truncate">{user?.email}</p>
          <span className="text-[11px] text-slate-500 capitalize">{user?.role}</span>
        </div>
      </div>
    </aside>
  );
};
