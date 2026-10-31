import React, { useEffect, useState } from 'react';
import { apiRequest } from '../../api/client';
import { useToast } from '../../components/ToastContext';
import {
  CreditCard,
  Search,
  Calendar,
  Filter,
  DollarSign
} from 'lucide-react';

interface Payment {
  id: string;
  invoice_id: string;
  customer_id: string;
  method: string;
  amount: string;
  paid_on: string;
  note?: string;
  recorded_by: string;
  created_at: string;
  updated_at: string;
}

export const Payments: React.FC = () => {
  const { addToast } = useToast();
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [methodFilter, setMethodFilter] = useState<string>('all');
  const [fromDate, setFromDate] = useState<string>('');
  const [toDate, setToDate] = useState<string>('');
  const [page, setPage] = useState<number>(1);
  const [total, setTotal] = useState<number>(0);

  const loadPayments = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: '20',
        ...(methodFilter !== 'all' ? { method: methodFilter } : {}),
        ...(fromDate ? { from: fromDate } : {}),
        ...(toDate ? { to: toDate } : {}),
      });

      const data = await apiRequest<{ items: Payment[]; total: number }>(`/payments?${params.toString()}`);
      setPayments(data.items);
      setTotal(data.total);
    } catch (err: any) {
      addToast(err.message || 'Failed to load payments', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPayments();
  }, [page, methodFilter, fromDate, toDate]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Payment Ledger</h1>
        <p className="text-sm text-slate-500 mt-1">
          Immutable audit record of all customer transactions, payment methods, and ledger allocations.
        </p>
      </div>

      {/* Filter Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <div>
            <label className="block text-[11px] font-semibold text-slate-500 uppercase mb-0.5">Method</label>
            <select
              value={methodFilter}
              onChange={(e) => {
                setMethodFilter(e.target.value);
                setPage(1);
              }}
              className="px-3 py-1.5 border border-slate-200 rounded-lg text-xs bg-white text-slate-700"
            >
              <option value="all">All Methods</option>
              <option value="bank_transfer">Bank Transfer</option>
              <option value="card">Card</option>
              <option value="upi">UPI</option>
              <option value="cash">Cash</option>
              <option value="cheque">Cheque</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-500 uppercase mb-0.5">From Date</label>
            <input
              type="date"
              value={fromDate}
              onChange={(e) => {
                setFromDate(e.target.value);
                setPage(1);
              }}
              className="px-2.5 py-1.5 border border-slate-200 rounded-lg text-xs bg-white text-slate-700"
            />
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-500 uppercase mb-0.5">To Date</label>
            <input
              type="date"
              value={toDate}
              onChange={(e) => {
                setToDate(e.target.value);
                setPage(1);
              }}
              className="px-2.5 py-1.5 border border-slate-200 rounded-lg text-xs bg-white text-slate-700"
            />
          </div>

          {(methodFilter !== 'all' || fromDate || toDate) && (
            <div className="self-end pb-0.5">
              <button
                onClick={() => {
                  setMethodFilter('all');
                  setFromDate('');
                  setToDate('');
                  setPage(1);
                }}
                className="px-2.5 py-1.5 text-xs text-blue-600 hover:text-blue-800 font-medium"
              >
                Clear Filters
              </button>
            </div>
          )}
        </div>

        <span className="text-xs text-slate-500 font-medium">Total Entries: {total}</span>
      </div>

      {/* Payments Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/75 border-b border-slate-200 text-slate-500 text-xs font-semibold uppercase tracking-wider">
                <th className="py-3 px-4">Payment ID</th>
                <th className="py-3 px-4">Invoice Ref</th>
                <th className="py-3 px-4">Method</th>
                <th className="py-3 px-4">Paid On</th>
                <th className="py-3 px-4">Recorded By</th>
                <th className="py-3 px-4">Note</th>
                <th className="py-3 px-4 text-right">Amount</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-400">
                    Loading payment ledger...
                  </td>
                </tr>
              ) : payments.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-400">
                    No payment records found.
                  </td>
                </tr>
              ) : (
                payments.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-50/50 transition-colors">
                    <td className="py-3 px-4 font-mono text-xs text-slate-500">
                      {p.id.substring(0, 10)}...
                    </td>
                    <td className="py-3 px-4 font-mono text-xs text-blue-700 font-semibold">
                      {p.invoice_id}
                    </td>
                    <td className="py-3 px-4 capitalize">
                      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-700">
                        <CreditCard className="w-3 h-3 text-slate-500" />
                        {p.method.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-xs text-slate-600">
                      {p.paid_on.substring(0, 10)}
                    </td>
                    <td className="py-3 px-4 text-xs text-slate-500">
                      {p.recorded_by}
                    </td>
                    <td className="py-3 px-4 text-xs text-slate-500 max-w-xs truncate">
                      {p.note || '—'}
                    </td>
                    <td className="py-3 px-4 text-right font-bold text-emerald-700">
                      +${parseFloat(p.amount).toFixed(2)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="p-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
          <div>Page {page} of {Math.max(1, Math.ceil(total / 20))}</div>
          <div className="flex gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
              className="px-3 py-1 border border-slate-200 rounded disabled:opacity-50"
            >
              Previous
            </button>
            <button
              disabled={page * 20 >= total}
              onClick={() => setPage(page + 1)}
              className="px-3 py-1 border border-slate-200 rounded disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
