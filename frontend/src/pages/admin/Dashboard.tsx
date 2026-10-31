import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  TrendingUp,
  DollarSign,
  AlertTriangle,
  Repeat,
  ArrowUpRight,
  RefreshCw,
  Clock,
  ChevronRight
} from 'lucide-react';
import { apiRequest } from '../../api/client';
import { StatusBadge } from '../../components/StatusBadge';

export const Dashboard: React.FC = () => {
  const [summary, setSummary] = useState<any>(null);
  const [revenuePoints, setRevenuePoints] = useState<any[]>([]);
  const [overdueInvoices, setOverdueInvoices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const [sumRes, revRes, overdueRes] = await Promise.all([
        apiRequest('/reports/summary'),
        apiRequest('/reports/revenue?group_by=month'),
        apiRequest('/reports/overdue-invoices?page=1&page_size=5'),
      ]);
      setSummary(sumRes);
      setRevenuePoints(revRes.points || []);
      setOverdueInvoices(overdueRes.items || []);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const maxRevenue = Math.max(...revenuePoints.map((p) => parseFloat(p.revenue) || 1), 1);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Executive Billing Dashboard</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Real-time financial performance, recurring subscriber health, and collection metrics
          </p>
        </div>
        <button
          onClick={fetchDashboardData}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 transition-colors shadow-2xs self-start sm:self-auto cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Metrics</span>
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Active Subscriptions */}
        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Active Subscriptions
            </span>
            <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
              <Repeat className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-slate-900 tracking-tight">
              {summary ? summary.active_subscriptions.toLocaleString() : '—'}
            </span>
            <span className="block text-[11px] text-slate-400 mt-1">Live active contracts</span>
          </div>
        </div>

        {/* Total Revenue */}
        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Total Revenue
            </span>
            <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-slate-900 tracking-tight">
              ${summary ? parseFloat(summary.revenue_total).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0.00'}
            </span>
            <span className="block text-[11px] text-emerald-600 font-medium mt-1">
              MTD: ${summary ? parseFloat(summary.revenue_mtd).toLocaleString('en-US', { minimumFractionDigits: 2 }) : '0.00'}
            </span>
          </div>
        </div>

        {/* Outstanding Receivables */}
        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Outstanding Balance
            </span>
            <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
              <DollarSign className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-slate-900 tracking-tight">
              ${summary ? parseFloat(summary.outstanding_amount).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0.00'}
            </span>
            <span className="block text-[11px] text-slate-400 mt-1">Confirmed unpaid invoices</span>
          </div>
        </div>

        {/* Overdue Invoices */}
        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Overdue Receivables
            </span>
            <div className="w-8 h-8 rounded-lg bg-rose-50 text-rose-600 flex items-center justify-center">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-rose-600 tracking-tight">
              ${summary ? parseFloat(summary.overdue_amount).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0.00'}
            </span>
            <span className="block text-[11px] text-rose-500 font-medium mt-1">
              {summary ? summary.overdue_count.toLocaleString() : 0} overdue accounts
            </span>
          </div>
        </div>
      </div>

      {/* Revenue Trend & Overdue List */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Revenue by Month Chart */}
        <div className="lg:col-span-2 bg-white rounded-xl p-5 border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-bold text-slate-900">Revenue Collections by Month</h2>
              <p className="text-xs text-slate-500">Historical realized revenue cashflow</p>
            </div>
            <span className="text-xs font-medium text-slate-400">Past 12 Months</span>
          </div>

          {revenuePoints.length === 0 ? (
            <div className="h-48 flex items-center justify-center text-xs text-slate-400">
              No historical revenue points available yet.
            </div>
          ) : (
            <div className="h-56 flex items-end gap-2 pt-6 pb-2 px-2 border-b border-slate-100">
              {revenuePoints.slice(-12).map((pt, idx) => {
                const val = parseFloat(pt.revenue) || 0;
                const heightPct = Math.max(Math.round((val / maxRevenue) * 100), 4);
                return (
                  <div key={idx} className="flex-1 flex flex-col items-center gap-1 group relative">
                    {/* Tooltip */}
                    <div className="absolute -top-8 hidden group-hover:block bg-slate-800 text-white text-[10px] py-1 px-2 rounded-md whitespace-nowrap z-10 shadow-md">
                      ${val.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </div>
                    <div
                      className="w-full bg-blue-500 hover:bg-blue-600 rounded-t-sm transition-all duration-300"
                      style={{ height: `${heightPct}%` }}
                    />
                    <span className="text-[10px] text-slate-500 rotate-0 font-medium mt-1 truncate max-w-full">
                      {pt.month.slice(5)}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Overdue Accounts Table */}
        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-2xs flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-bold text-slate-900">Immediate Overdue Invoices</h2>
              <p className="text-xs text-slate-500">Invoices exceeding credit terms</p>
            </div>
            <Link
              to="/invoices?overdue=true"
              className="text-xs font-semibold text-blue-600 hover:text-blue-700 inline-flex items-center gap-0.5"
            >
              <span>View All</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="flex-1 overflow-y-auto space-y-3">
            {overdueInvoices.length === 0 ? (
              <div className="h-40 flex items-center justify-center text-xs text-slate-400">
                No overdue invoices found. All collections current!
              </div>
            ) : (
              overdueInvoices.map((inv) => (
                <Link
                  key={inv.id}
                  to={`/invoices`}
                  className="block p-3 rounded-lg border border-slate-100 bg-slate-50/50 hover:bg-slate-100/70 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-800">{inv.number}</span>
                    <span className="text-xs font-bold text-rose-600">
                      ${(parseFloat(inv.total) - parseFloat(inv.amount_paid)).toFixed(2)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between mt-1 text-[11px] text-slate-500">
                    <span className="truncate max-w-[130px]">{inv.customer_snapshot.name}</span>
                    <span className="text-rose-500 font-medium">Due {inv.due_date}</span>
                  </div>
                </Link>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
