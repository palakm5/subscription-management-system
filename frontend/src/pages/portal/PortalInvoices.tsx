import React, { useEffect, useState } from 'react';
import { apiRequest } from '../../api/client';
import { useToast } from '../../components/ToastContext';
import { StatusBadge } from '../../components/StatusBadge';
import {
  FileText,
  Download,
  Calendar,
  AlertTriangle,
  CreditCard
} from 'lucide-react';

interface PortalInvoice {
  id: string;
  number: string;
  subscription_id: string;
  period_start: string;
  period_end: string;
  issue_date: string;
  due_date: string;
  status: 'draft' | 'confirmed' | 'paid' | 'cancelled';
  is_overdue: boolean;
  total: string;
  amount_paid: string;
  balance_due: string;
}

export const PortalInvoices: React.FC = () => {
  const { addToast } = useToast();
  const [invoices, setInvoices] = useState<PortalInvoice[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const loadInvoices = async () => {
    try {
      setLoading(true);
      const data = await apiRequest<{ items: PortalInvoice[]; total: number }>('/portal/invoices?page=1&page_size=50');
      setInvoices(data.items);
    } catch (err: any) {
      addToast(err.message || 'Failed to load invoices', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInvoices();
  }, []);

  const handleDownloadPdf = async (id: string, invoiceNumber: string) => {
    try {
      const blob = await apiRequest<Blob>(`/portal/invoices/${id}/pdf`);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Invoice-${invoiceNumber}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      addToast(`Downloaded PDF for ${invoiceNumber}`, 'success');
    } catch (err: any) {
      addToast(err.message || 'Failed to download invoice PDF', 'error');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">My Invoices</h1>
        <p className="text-sm text-slate-500 mt-1">
          Review your billing statements, outstanding balances, and official PDF receipts.
        </p>
      </div>

      {/* Invoices List */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/75 border-b border-slate-200 text-slate-500 text-xs font-semibold uppercase tracking-wider">
                <th className="py-3 px-4">Invoice #</th>
                <th className="py-3 px-4">Period</th>
                <th className="py-3 px-4">Due Date</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Invoice Total</th>
                <th className="py-3 px-4 text-right">Balance Due</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-400">
                    Loading your invoices...
                  </td>
                </tr>
              ) : invoices.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-400">
                    No invoices recorded for your account.
                  </td>
                </tr>
              ) : (
                invoices.map((inv) => (
                  <tr key={inv.id} className="hover:bg-slate-50/50 transition-colors">
                    <td className="py-3 px-4 font-mono font-bold text-blue-700">
                      {inv.number}
                    </td>
                    <td className="py-3 px-4 text-xs text-slate-500">
                      {inv.period_start.substring(0, 10)} to {inv.period_end.substring(0, 10)}
                    </td>
                    <td className="py-3 px-4 text-xs text-slate-700">
                      {inv.due_date.substring(0, 10)}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-1.5">
                        <StatusBadge status={inv.status} />
                        {inv.is_overdue && (
                          <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200">
                            OVERDUE
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-4 text-right font-medium text-slate-700">
                      ${parseFloat(inv.total).toFixed(2)}
                    </td>
                    <td className="py-3 px-4 text-right font-bold text-slate-900">
                      ${parseFloat(inv.balance_due).toFixed(2)}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => handleDownloadPdf(inv.id, inv.number)}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-blue-50 text-blue-700 hover:bg-blue-100 rounded-lg transition"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>Download PDF</span>
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
