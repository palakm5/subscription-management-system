import React, { useEffect, useState } from 'react';
import { apiRequest } from '../../api/client';
import { useToast } from '../../components/ToastContext';
import { Modal } from '../../components/Modal';
import { StatusBadge } from '../../components/StatusBadge';
import {
  FileText,
  Search,
  Eye,
  Download,
  Send,
  CreditCard,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Play,
  RotateCw
} from 'lucide-react';

interface TaxBreakdown {
  tax_id: string;
  name: string;
  rate: string;
  amount: string;
}

interface InvoiceLine {
  product_name: string;
  variant_label?: string;
  quantity: number;
  unit_price: string;
  discount_amount: string;
  tax_breakdown: TaxBreakdown[];
  line_total: string;
}

interface Invoice {
  id: string;
  number: string;
  subscription_id: string;
  customer_id: string;
  customer_snapshot: {
    name: string;
    billing_address?: {
      line1?: string;
      city?: string;
      state?: string;
      zip?: string;
      country?: string;
    };
    tax_id?: string;
  };
  period_start: string;
  period_end: string;
  issue_date: string;
  due_date: string;
  status: 'draft' | 'confirmed' | 'paid' | 'cancelled';
  is_overdue: boolean;
  lines: InvoiceLine[];
  subtotal: string;
  discount_total: string;
  tax_total: string;
  total: string;
  amount_paid: string;
  balance_due: string;
  applied_discounts: { discount_id: string; name: string; amount: string }[];
  sent_at?: string;
  created_at: string;
  updated_at: string;
}

export const Invoices: React.FC = () => {
  const { addToast } = useToast();
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<string>('all');
  const [search, setSearch] = useState<string>('');
  const [page, setPage] = useState<number>(1);
  const [total, setTotal] = useState<number>(0);
  const [runningBilling, setRunningBilling] = useState<boolean>(false);

  // Detail Modal
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);

  // Payment Modal
  const [isPaymentModalOpen, setIsPaymentModalOpen] = useState(false);
  const [paymentForm, setPaymentForm] = useState({
    method: 'bank_transfer',
    amount: '0.00',
    paid_on: new Date().toISOString().substring(0, 10),
    note: '',
  });

  const loadInvoices = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: '20',
        ...(search ? { q: search } : {}),
      });

      if (activeTab === 'overdue') {
        params.append('overdue', 'true');
      } else if (activeTab !== 'all') {
        params.append('status', activeTab);
      }

      const data = await apiRequest<{ items: Invoice[]; total: number }>(`/invoices?${params.toString()}`);
      setInvoices(data.items);
      setTotal(data.total);
    } catch (err: any) {
      addToast(err.message || 'Failed to load invoices', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInvoices();
  }, [page, activeTab, search]);

  const handleRunBilling = async () => {
    try {
      setRunningBilling(true);
      const res = await apiRequest<{
        processed: number;
        created: number;
        skipped_duplicates: number;
        errors: number;
      }>('/billing/run', { method: 'POST' });

      addToast(
        `Billing run complete: ${res.created} invoices generated, ${res.skipped_duplicates} duplicate periods prevented`,
        'success'
      );
      loadInvoices();
    } catch (err: any) {
      addToast(err.message || 'Billing run failed', 'error');
    } finally {
      setRunningBilling(false);
    }
  };

  const handleConfirmInvoice = async (id: string) => {
    try {
      const updated = await apiRequest<Invoice>(`/invoices/${id}/confirm`, { method: 'POST' });
      setSelectedInvoice(updated);
      addToast('Invoice confirmed', 'success');
      loadInvoices();
    } catch (err: any) {
      addToast(err.message || 'Failed to confirm invoice', 'error');
    }
  };

  const handleCancelInvoice = async (id: string) => {
    if (!window.confirm('Cancel this invoice? This cannot be undone.')) return;
    try {
      const updated = await apiRequest<Invoice>(`/invoices/${id}/cancel`, { method: 'POST' });
      setSelectedInvoice(updated);
      addToast('Invoice cancelled', 'success');
      loadInvoices();
    } catch (err: any) {
      addToast(err.message || 'Failed to cancel invoice', 'error');
    }
  };

  const handleSendEmail = async (id: string) => {
    try {
      await apiRequest(`/invoices/${id}/send`, { method: 'POST' });
      addToast('Invoice email dispatched', 'success');
      if (selectedInvoice && selectedInvoice.id === id) {
        setSelectedInvoice({ ...selectedInvoice, sent_at: new Date().toISOString() });
      }
      loadInvoices();
    } catch (err: any) {
      addToast(err.message || 'Failed to send invoice', 'error');
    }
  };

  const handleDownloadPdf = async (id: string, invoiceNumber: string) => {
    try {
      const blob = await apiRequest<Blob>(`/invoices/${id}/pdf`);
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
      addToast(err.message || 'Failed to download PDF', 'error');
    }
  };

  const handleOpenPayment = (inv: Invoice) => {
    setPaymentForm({
      method: 'bank_transfer',
      amount: parseFloat(inv.balance_due).toFixed(2),
      paid_on: new Date().toISOString().substring(0, 10),
      note: '',
    });
    setIsPaymentModalOpen(true);
  };

  const handleRecordPayment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedInvoice) return;
    try {
      const res = await apiRequest(`/invoices/${selectedInvoice.id}/payments`, {
        method: 'POST',
        body: JSON.stringify({
          method: paymentForm.method,
          amount: parseFloat(paymentForm.amount),
          paid_on: paymentForm.paid_on,
          note: paymentForm.note || null,
        }),
      });

      addToast(`Payment of $${paymentForm.amount} recorded`, 'success');
      setIsPaymentModalOpen(false);

      // Reload invoice details
      const updated = await apiRequest<Invoice>(`/invoices/${selectedInvoice.id}`);
      setSelectedInvoice(updated);
      loadInvoices();
    } catch (err: any) {
      addToast(err.message || 'Failed to record payment', 'error');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Invoices</h1>
          <p className="text-sm text-slate-500 mt-1">
            Automated recurring billings, derived overdue balances, payments, and PDF generation.
          </p>
        </div>
        <button
          onClick={handleRunBilling}
          disabled={runningBilling}
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition shadow-xs disabled:opacity-50"
        >
          <RotateCw className={`w-4 h-4 ${runningBilling ? 'animate-spin' : ''}`} />
          <span>{runningBilling ? 'Billing in progress...' : 'Run Billing Now'}</span>
        </button>
      </div>

      {/* Filter Tabs & Search */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs space-y-4">
        <div className="flex items-center gap-2 overflow-x-auto pb-1">
          {[
            { id: 'all', label: 'All Invoices' },
            { id: 'confirmed', label: 'Outstanding (Confirmed)' },
            { id: 'paid', label: 'Paid' },
            { id: 'overdue', label: 'Overdue' },
            { id: 'draft', label: 'Draft' },
            { id: 'cancelled', label: 'Cancelled' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => {
                setActiveTab(tab.id);
                setPage(1);
              }}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold tracking-wider transition ${
                activeTab === tab.id
                  ? 'bg-blue-600 text-white shadow-xs'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="flex items-center justify-between gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search by invoice number (e.g. INV-000001)..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 border border-slate-200 rounded-lg text-sm"
            />
          </div>
          <span className="text-xs text-slate-500 font-medium">Total: {total}</span>
        </div>
      </div>

      {/* Invoices Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/75 border-b border-slate-200 text-slate-500 text-xs font-semibold uppercase tracking-wider">
                <th className="py-3 px-4">Invoice #</th>
                <th className="py-3 px-4">Customer</th>
                <th className="py-3 px-4">Billing Period</th>
                <th className="py-3 px-4">Due Date</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Total</th>
                <th className="py-3 px-4 text-right">Balance Due</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-400">
                    Loading invoices...
                  </td>
                </tr>
              ) : invoices.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-400">
                    No invoices found.
                  </td>
                </tr>
              ) : (
                invoices.map((inv) => (
                  <tr key={inv.id} className="hover:bg-slate-50/50 transition-colors">
                    <td className="py-3 px-4 font-mono font-bold text-blue-700">
                      {inv.number}
                    </td>
                    <td className="py-3 px-4 font-medium text-slate-900 truncate max-w-xs">
                      {inv.customer_snapshot.name}
                    </td>
                    <td className="py-3 px-4 text-xs text-slate-500">
                      {inv.period_start.substring(0, 10)} → {inv.period_end.substring(0, 10)}
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
                    <td className="py-3 px-4 text-right font-medium text-slate-800">
                      ${parseFloat(inv.total).toFixed(2)}
                    </td>
                    <td className="py-3 px-4 text-right font-bold text-slate-900">
                      ${parseFloat(inv.balance_due).toFixed(2)}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="inline-flex items-center gap-2">
                        <button
                          onClick={() => setSelectedInvoice(inv)}
                          className="p-1.5 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-md transition"
                          title="View Invoice"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDownloadPdf(inv.id, inv.number)}
                          className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-md transition"
                          title="Download PDF"
                        >
                          <Download className="w-4 h-4" />
                        </button>
                      </div>
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

      {/* Invoice Detail Modal */}
      <Modal
        isOpen={!!selectedInvoice}
        onClose={() => setSelectedInvoice(null)}
        title={selectedInvoice ? `Invoice ${selectedInvoice.number}` : ''}
        maxWidth="max-w-3xl"
      >
        {selectedInvoice && (
          <div className="space-y-6">
            {/* Header info */}
            <div className="flex flex-wrap items-start justify-between gap-4 p-4 bg-slate-50 rounded-xl border border-slate-200">
              <div>
                <span className="text-xs text-slate-500">Billed To</span>
                <p className="font-bold text-slate-900">{selectedInvoice.customer_snapshot.name}</p>
                {selectedInvoice.customer_snapshot.billing_address && (
                  <p className="text-xs text-slate-500">
                    {selectedInvoice.customer_snapshot.billing_address.line1},{' '}
                    {selectedInvoice.customer_snapshot.billing_address.city}
                  </p>
                )}
                {selectedInvoice.customer_snapshot.tax_id && (
                  <p className="text-xs text-slate-400">Tax ID: {selectedInvoice.customer_snapshot.tax_id}</p>
                )}
              </div>
              <div className="text-right">
                <span className="text-xs text-slate-500">Status</span>
                <div className="flex items-center justify-end gap-1.5 mt-0.5">
                  <StatusBadge status={selectedInvoice.status} />
                  {selectedInvoice.is_overdue && (
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200">
                      OVERDUE
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-500 mt-2">
                  Due: <strong>{selectedInvoice.due_date.substring(0, 10)}</strong>
                </p>
              </div>
            </div>

            {/* Action Bar */}
            <div className="flex items-center justify-between p-3 bg-slate-50 rounded-xl border border-slate-200 flex-wrap gap-2">
              <div className="flex items-center gap-2">
                {selectedInvoice.status === 'draft' && (
                  <button
                    onClick={() => handleConfirmInvoice(selectedInvoice.id)}
                    className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold transition"
                  >
                    Confirm Invoice
                  </button>
                )}

                {(selectedInvoice.status === 'draft' || selectedInvoice.status === 'confirmed') && (
                  <button
                    onClick={() => handleCancelInvoice(selectedInvoice.id)}
                    className="px-3 py-1.5 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded-lg text-xs font-semibold transition"
                  >
                    Cancel Invoice
                  </button>
                )}

                <button
                  onClick={() => handleSendEmail(selectedInvoice.id)}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>{selectedInvoice.sent_at ? 'Resend Email' : 'Send Email'}</span>
                </button>

                <button
                  onClick={() => handleDownloadPdf(selectedInvoice.id, selectedInvoice.number)}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download PDF</span>
                </button>
              </div>

              {selectedInvoice.status === 'confirmed' && parseFloat(selectedInvoice.balance_due) > 0 && (
                <button
                  onClick={() => handleOpenPayment(selectedInvoice)}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold transition shadow-xs"
                >
                  <CreditCard className="w-3.5 h-3.5" />
                  <span>Record Payment</span>
                </button>
              )}
            </div>

            {/* Line items snapshot */}
            <div className="rounded-xl border border-slate-200 overflow-hidden">
              <table className="w-full text-left border-collapse text-sm">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 text-xs font-semibold uppercase">
                    <th className="py-2.5 px-3">Item Description</th>
                    <th className="py-2.5 px-3 text-center">Qty</th>
                    <th className="py-2.5 px-3 text-right">Unit Price</th>
                    <th className="py-2.5 px-3 text-right">Discount</th>
                    <th className="py-2.5 px-3 text-right">Total</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {selectedInvoice.lines.map((l, i) => (
                    <tr key={i}>
                      <td className="py-2.5 px-3">
                        <span className="font-semibold text-slate-900">{l.product_name}</span>
                        {l.variant_label && (
                          <span className="block text-xs text-slate-500">{l.variant_label}</span>
                        )}
                        {l.tax_breakdown?.map((t, ti) => (
                          <span key={ti} className="inline-block text-[10px] text-slate-400 mr-2">
                            {t.name}: ${parseFloat(t.amount).toFixed(2)}
                          </span>
                        ))}
                      </td>
                      <td className="py-2.5 px-3 text-center">{l.quantity}</td>
                      <td className="py-2.5 px-3 text-right text-slate-600">${parseFloat(l.unit_price).toFixed(2)}</td>
                      <td className="py-2.5 px-3 text-right text-slate-500">
                        {parseFloat(l.discount_amount) > 0 ? `-$${parseFloat(l.discount_amount).toFixed(2)}` : '—'}
                      </td>
                      <td className="py-2.5 px-3 text-right font-semibold text-slate-900">
                        ${parseFloat(l.line_total).toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Totals Summary */}
            <div className="flex justify-end">
              <div className="w-72 space-y-2 text-sm bg-slate-50 p-4 rounded-xl border border-slate-200">
                <div className="flex justify-between text-slate-600">
                  <span>Subtotal:</span>
                  <span>${parseFloat(selectedInvoice.subtotal).toFixed(2)}</span>
                </div>
                {parseFloat(selectedInvoice.discount_total) > 0 && (
                  <div className="flex justify-between text-emerald-700 font-medium">
                    <span>Discount:</span>
                    <span>-${parseFloat(selectedInvoice.discount_total).toFixed(2)}</span>
                  </div>
                )}
                <div className="flex justify-between text-slate-600">
                  <span>Taxes:</span>
                  <span>+${parseFloat(selectedInvoice.tax_total).toFixed(2)}</span>
                </div>
                <div className="flex justify-between font-bold text-slate-900 pt-2 border-t border-slate-200 text-base">
                  <span>Total:</span>
                  <span>${parseFloat(selectedInvoice.total).toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-emerald-700 text-xs font-semibold">
                  <span>Amount Paid:</span>
                  <span>${parseFloat(selectedInvoice.amount_paid).toFixed(2)}</span>
                </div>
                <div className="flex justify-between font-bold text-blue-700 text-base pt-1 border-t border-slate-200">
                  <span>Balance Due:</span>
                  <span>${parseFloat(selectedInvoice.balance_due).toFixed(2)}</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </Modal>

      {/* Record Payment Modal */}
      <Modal
        isOpen={isPaymentModalOpen}
        onClose={() => setIsPaymentModalOpen(false)}
        title="Record Payment"
      >
        <form onSubmit={handleRecordPayment} className="space-y-4">
          <div className="p-3 bg-blue-50 rounded-lg text-xs text-blue-800">
            Recording payment for invoice <strong>{selectedInvoice?.number}</strong>. Current balance due is{' '}
            <strong>${selectedInvoice?.balance_due}</strong>.
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Payment Method *
            </label>
            <select
              value={paymentForm.method}
              onChange={(e) => setPaymentForm({ ...paymentForm, method: e.target.value })}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm bg-white"
            >
              <option value="bank_transfer">Bank Transfer</option>
              <option value="card">Credit / Debit Card</option>
              <option value="upi">UPI</option>
              <option value="cash">Cash</option>
              <option value="cheque">Cheque</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Amount ($) *
              </label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                max={selectedInvoice ? parseFloat(selectedInvoice.balance_due) : undefined}
                required
                value={paymentForm.amount}
                onChange={(e) => setPaymentForm({ ...paymentForm, amount: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Payment Date *
              </label>
              <input
                type="date"
                required
                value={paymentForm.paid_on}
                onChange={(e) => setPaymentForm({ ...paymentForm, paid_on: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Internal Note / Reference
            </label>
            <input
              type="text"
              placeholder="e.g. Wire transfer ref #98321"
              value={paymentForm.note}
              onChange={(e) => setPaymentForm({ ...paymentForm, note: e.target.value })}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
            />
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setIsPaymentModalOpen(false)}
              className="px-4 py-2 border border-slate-200 text-slate-600 rounded-lg text-sm font-medium hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-medium transition shadow-xs"
            >
              Save Payment
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
