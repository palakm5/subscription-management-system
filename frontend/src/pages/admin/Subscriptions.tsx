import React, { useEffect, useState } from 'react';
import { apiRequest } from '../../api/client';
import { useToast } from '../../components/ToastContext';
import { Modal } from '../../components/Modal';
import { StatusBadge } from '../../components/StatusBadge';
import {
  Repeat,
  Plus,
  Search,
  Eye,
  CheckCircle2,
  XCircle,
  PauseCircle,
  PlayCircle,
  RefreshCw,
  FileCheck,
  Calendar,
  Layers,
  ArrowRight
} from 'lucide-react';

interface SubscriptionLine {
  line_id: string;
  product_id: string;
  product_name: string;
  variant_id?: string;
  variant_label?: string;
  quantity: number;
  unit_price: string;
  tax_ids: string[];
  amount: string;
}

interface StatusHistory {
  from?: string;
  to: string;
  by: string;
  at: string;
}

interface Subscription {
  id: string;
  number: string;
  customer_id: string;
  plan_id: string;
  template_id?: string;
  status: 'draft' | 'quotation' | 'confirmed' | 'active' | 'paused' | 'closed';
  start_date: string;
  expiry_date: string;
  payment_terms: number;
  quotation_valid_until?: string;
  next_invoice_date?: string;
  lines: SubscriptionLine[];
  discount_ids: string[];
  status_history: StatusHistory[];
  created_at: string;
  updated_at: string;
}

interface Customer {
  id: string;
  name: string;
  company?: string;
}

interface Plan {
  id: string;
  name: string;
  billing_period: string;
  price: string;
  pausable: boolean;
  closable: boolean;
  renewable: boolean;
}

interface Product {
  id: string;
  name: string;
  sales_price: string;
  variants: { id: string; attribute: string; value: string; extra_price: string }[];
}

interface Template {
  id: string;
  name: string;
  plan_id: string;
}

export const Subscriptions: React.FC = () => {
  const { addToast } = useToast();
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [search, setSearch] = useState<string>('');
  const [page, setPage] = useState<number>(1);
  const [total, setTotal] = useState<number>(0);

  // Aux data
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);

  // Selected subscription for detail view
  const [selectedSub, setSelectedSub] = useState<Subscription | null>(null);

  // Create Modal
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [createType, setCreateType] = useState<'scratch' | 'template'>('scratch');
  const [createForm, setCreateForm] = useState({
    customer_id: '',
    plan_id: '',
    template_id: '',
    start_date: new Date().toISOString().substring(0, 10),
    payment_terms: 15,
    lines: [
      { product_id: '', variant_id: '', quantity: 1, unit_price: '' }
    ],
  });

  const loadSubscriptions = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: '20',
        ...(statusFilter !== 'all' ? { status: statusFilter } : {}),
        ...(search ? { q: search } : {}),
      });
      const data = await apiRequest<{ items: Subscription[]; total: number }>(`/subscriptions?${params.toString()}`);
      setSubscriptions(data.items);
      setTotal(data.total);
    } catch (err: any) {
      addToast(err.message || 'Failed to load subscriptions', 'error');
    } finally {
      setLoading(false);
    }
  };

  const loadAuxData = async () => {
    try {
      const [custRes, planRes, prodRes, tmplRes] = await Promise.all([
        apiRequest<{ items: Customer[]; total: number }>('/customers?page=1&page_size=100'),
        apiRequest<{ items: Plan[]; total: number }>('/plans?page=1&page_size=50'),
        apiRequest<{ items: Product[]; total: number }>('/products?page=1&page_size=100'),
        apiRequest<{ items: Template[]; total: number }>('/quotation-templates?page=1&page_size=50'),
      ]);
      setCustomers(custRes.items);
      setPlans(planRes.items);
      setProducts(prodRes.items);
      setTemplates(tmplRes.items);

      if (custRes.items.length > 0 && planRes.items.length > 0) {
        setCreateForm((prev) => ({
          ...prev,
          customer_id: custRes.items[0].id,
          plan_id: planRes.items[0].id,
          lines: [{ product_id: prodRes.items[0]?.id || '', variant_id: '', quantity: 1, unit_price: '' }],
        }));
      }
    } catch (err: any) {
      console.error('Failed to load aux metadata', err);
    }
  };

  useEffect(() => {
    loadAuxData();
  }, []);

  useEffect(() => {
    loadSubscriptions();
  }, [page, statusFilter, search]);

  const handleTransition = async (targetStatus: string) => {
    if (!selectedSub) return;
    try {
      const updated = await apiRequest<Subscription>(`/subscriptions/${selectedSub.id}/transition`, {
        method: 'POST',
        body: JSON.stringify({ to: targetStatus }),
      });
      setSelectedSub(updated);
      addToast(`Subscription moved to ${targetStatus}`, 'success');
      loadSubscriptions();
    } catch (err: any) {
      addToast(err.message || 'Transition rejected', 'error');
    }
  };

  const handleRenew = async () => {
    if (!selectedSub) return;
    try {
      const renewed = await apiRequest<Subscription>(`/subscriptions/${selectedSub.id}/renew`, {
        method: 'POST',
      });
      addToast(`Subscription renewed as ${renewed.number}`, 'success');
      setSelectedSub(renewed);
      loadSubscriptions();
    } catch (err: any) {
      addToast(err.message || 'Renewal failed', 'error');
    }
  };

  const handleCreateSubscription = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      let payload: any = {
        customer_id: createForm.customer_id,
        start_date: createForm.start_date,
        payment_terms: createForm.payment_terms,
      };

      if (createType === 'template') {
        payload.template_id = createForm.template_id;
      } else {
        payload.plan_id = createForm.plan_id;
        payload.lines = createForm.lines.map((l) => ({
          product_id: l.product_id,
          variant_id: l.variant_id || null,
          quantity: l.quantity,
          unit_price: l.unit_price ? parseFloat(l.unit_price) : null,
        }));
      }

      const res = await apiRequest<Subscription>('/subscriptions', {
        method: 'POST',
        body: JSON.stringify(payload),
      });

      addToast(`Subscription ${res.number} created`, 'success');
      setIsCreateModalOpen(false);
      loadSubscriptions();
    } catch (err: any) {
      addToast(err.message || 'Failed to create subscription', 'error');
    }
  };

  const getCustomerName = (customerId: string) => {
    const c = customers.find((cust) => cust.id === customerId);
    return c ? (c.company ? `${c.name} (${c.company})` : c.name) : customerId;
  };

  const getPlan = (planId: string) => {
    return plans.find((p) => p.id === planId);
  };

  const currentPlan = selectedSub ? getPlan(selectedSub.plan_id) : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Subscriptions</h1>
          <p className="text-sm text-slate-500 mt-1">
            Manage subscription lifecycles, quotation flows, renewals, and recurring intervals.
          </p>
        </div>
        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition shadow-xs"
        >
          <Plus className="w-4 h-4" />
          <span>New Subscription</span>
        </button>
      </div>

      {/* Filter Tabs & Search */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs space-y-4">
        <div className="flex items-center gap-2 overflow-x-auto pb-1">
          {['all', 'draft', 'quotation', 'confirmed', 'active', 'paused', 'closed'].map((st) => (
            <button
              key={st}
              onClick={() => {
                setStatusFilter(st);
                setPage(1);
              }}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider transition ${
                statusFilter === st
                  ? 'bg-blue-600 text-white shadow-xs'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {st}
            </button>
          ))}
        </div>

        <div className="flex items-center justify-between gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search by number (e.g. SUB-000001)..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 border border-slate-200 rounded-lg text-sm"
            />
          </div>
          <span className="text-xs text-slate-500 font-medium">Total: {total}</span>
        </div>
      </div>

      {/* Subscriptions Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/75 border-b border-slate-200 text-slate-500 text-xs font-semibold uppercase tracking-wider">
                <th className="py-3 px-4">Sub Number</th>
                <th className="py-3 px-4">Customer</th>
                <th className="py-3 px-4">Plan</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Period Dates</th>
                <th className="py-3 px-4">Next Invoice</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-400">
                    Loading subscriptions...
                  </td>
                </tr>
              ) : subscriptions.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-400">
                    No subscriptions found.
                  </td>
                </tr>
              ) : (
                subscriptions.map((s) => (
                  <tr key={s.id} className="hover:bg-slate-50/50 transition-colors">
                    <td className="py-3 px-4 font-mono font-bold text-blue-700">
                      {s.number}
                    </td>
                    <td className="py-3 px-4 text-slate-900 font-medium truncate max-w-xs">
                      {getCustomerName(s.customer_id)}
                    </td>
                    <td className="py-3 px-4 text-slate-600">
                      {getPlan(s.plan_id)?.name || s.plan_id}
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={s.status} />
                    </td>
                    <td className="py-3 px-4 text-xs text-slate-500">
                      {s.start_date.substring(0, 10)} → {s.expiry_date.substring(0, 10)}
                    </td>
                    <td className="py-3 px-4 text-xs font-medium text-slate-700">
                      {s.next_invoice_date ? s.next_invoice_date.substring(0, 10) : '—'}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => setSelectedSub(s)}
                        className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-md transition"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Manage</span>
                      </button>
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

      {/* Subscription Detail / Lifecycle Modal */}
      <Modal
        isOpen={!!selectedSub}
        onClose={() => setSelectedSub(null)}
        title={selectedSub ? `Subscription ${selectedSub.number}` : ''}
        maxWidth="max-w-3xl"
      >
        {selectedSub && (
          <div className="space-y-6">
            {/* Meta bar */}
            <div className="flex flex-wrap items-center justify-between gap-4 p-4 bg-slate-50 rounded-xl border border-slate-200">
              <div>
                <span className="text-xs text-slate-500">Customer</span>
                <p className="font-semibold text-slate-900">{getCustomerName(selectedSub.customer_id)}</p>
              </div>
              <div>
                <span className="text-xs text-slate-500">Plan</span>
                <p className="font-semibold text-slate-900">{currentPlan?.name || selectedSub.plan_id}</p>
              </div>
              <div>
                <span className="text-xs text-slate-500">Cadence</span>
                <p className="font-semibold text-slate-900 capitalize">{currentPlan?.billing_period || '—'}</p>
              </div>
              <div>
                <span className="text-xs text-slate-500">Status</span>
                <div className="mt-0.5"><StatusBadge status={selectedSub.status} /></div>
              </div>
            </div>

            {/* Lifecycle Action Bar */}
            <div className="p-4 rounded-xl border border-blue-100 bg-blue-50/50 flex items-center justify-between flex-wrap gap-3">
              <div>
                <h4 className="text-xs font-bold text-blue-900 uppercase tracking-wider">
                  Available Lifecycle Transitions
                </h4>
                <p className="text-xs text-blue-700">
                  Current state: <strong className="uppercase">{selectedSub.status}</strong>
                </p>
              </div>

              <div className="flex items-center gap-2 flex-wrap">
                {selectedSub.status === 'draft' && (
                  <>
                    <button
                      onClick={() => handleTransition('quotation')}
                      className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold transition"
                    >
                      Generate Quotation
                    </button>
                    <button
                      onClick={() => handleTransition('closed')}
                      className="px-3 py-1.5 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded-lg text-xs font-semibold transition"
                    >
                      Close Draft
                    </button>
                  </>
                )}

                {selectedSub.status === 'quotation' && (
                  <>
                    <button
                      onClick={() => handleTransition('confirmed')}
                      className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold transition"
                    >
                      Confirm Quote
                    </button>
                    <button
                      onClick={() => handleTransition('draft')}
                      className="px-3 py-1.5 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded-lg text-xs font-semibold transition"
                    >
                      Return to Draft
                    </button>
                    <button
                      onClick={() => handleTransition('closed')}
                      className="px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-semibold transition"
                    >
                      Close
                    </button>
                  </>
                )}

                {selectedSub.status === 'confirmed' && (
                  <>
                    <button
                      onClick={() => handleTransition('active')}
                      className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold transition"
                    >
                      Activate Subscription
                    </button>
                    <button
                      onClick={() => handleTransition('closed')}
                      className="px-3 py-1.5 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded-lg text-xs font-semibold transition"
                    >
                      Close
                    </button>
                  </>
                )}

                {selectedSub.status === 'active' && (
                  <>
                    {currentPlan?.pausable && (
                      <button
                        onClick={() => handleTransition('paused')}
                        className="px-3 py-1.5 bg-amber-500 hover:bg-amber-600 text-white rounded-lg text-xs font-semibold transition"
                      >
                        Pause Subscription
                      </button>
                    )}
                    {currentPlan?.closable && (
                      <button
                        onClick={() => handleTransition('closed')}
                        className="px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-semibold transition"
                      >
                        Close Early
                      </button>
                    )}
                  </>
                )}

                {selectedSub.status === 'paused' && (
                  <>
                    <button
                      onClick={() => handleTransition('active')}
                      className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold transition"
                    >
                      Resume Subscription
                    </button>
                    <button
                      onClick={() => handleTransition('closed')}
                      className="px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-semibold transition"
                    >
                      Close
                    </button>
                  </>
                )}

                {selectedSub.status === 'closed' && currentPlan?.renewable && (
                  <button
                    onClick={handleRenew}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold transition"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span>Renew Subscription</span>
                  </button>
                )}
              </div>
            </div>

            {/* Lines Snapshot */}
            <div>
              <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2">
                Subscription Line Items
              </h4>
              <div className="rounded-xl border border-slate-200 overflow-hidden">
                <table className="w-full text-left border-collapse text-sm">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 text-xs font-semibold uppercase">
                      <th className="py-2.5 px-3">Product</th>
                      <th className="py-2.5 px-3">Variant</th>
                      <th className="py-2.5 px-3 text-center">Qty</th>
                      <th className="py-2.5 px-3 text-right">Unit Price</th>
                      <th className="py-2.5 px-3 text-right">Amount</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {selectedSub.lines.map((l) => (
                      <tr key={l.line_id}>
                        <td className="py-2.5 px-3 font-medium text-slate-800">{l.product_name}</td>
                        <td className="py-2.5 px-3 text-slate-500">{l.variant_label || '—'}</td>
                        <td className="py-2.5 px-3 text-center">{l.quantity}</td>
                        <td className="py-2.5 px-3 text-right text-slate-600">${parseFloat(l.unit_price).toFixed(2)}</td>
                        <td className="py-2.5 px-3 text-right font-semibold text-slate-900">${parseFloat(l.amount).toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Status History Timeline */}
            <div>
              <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2">
                Status History Audit Trail
              </h4>
              <div className="space-y-2">
                {selectedSub.status_history?.map((h, i) => (
                  <div key={i} className="flex items-center justify-between text-xs p-2.5 bg-slate-50 rounded-lg border border-slate-200">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-slate-700 capitalize">{h.from || 'Initial'}</span>
                      <ArrowRight className="w-3 h-3 text-slate-400" />
                      <span className="font-bold text-blue-700 capitalize">{h.to}</span>
                    </div>
                    <div className="text-slate-400">
                      By: <span className="text-slate-600">{h.by}</span> on {new Date(h.at).toLocaleString()}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </Modal>

      {/* New Subscription Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Create Subscription / Quotation"
        maxWidth="max-w-2xl"
      >
        <form onSubmit={handleCreateSubscription} className="space-y-4">
          {/* Customer */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Customer *
            </label>
            <select
              required
              value={createForm.customer_id}
              onChange={(e) => setCreateForm({ ...createForm, customer_id: e.target.value })}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm bg-white"
            >
              {customers.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} {c.company ? `(${c.company})` : ''}
                </option>
              ))}
            </select>
          </div>

          {/* Creation Mode Toggle */}
          <div className="flex items-center gap-4 border-y border-slate-100 py-3">
            <span className="text-xs font-bold text-slate-700 uppercase">Configuration:</span>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="radio"
                name="createMode"
                checked={createType === 'scratch'}
                onChange={() => setCreateType('scratch')}
              />
              <span>Custom Plan & Lines</span>
            </label>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="radio"
                name="createMode"
                checked={createType === 'template'}
                onChange={() => setCreateType('template')}
              />
              <span>From Quotation Template</span>
            </label>
          </div>

          {createType === 'template' ? (
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Select Quotation Template *
              </label>
              <select
                required
                value={createForm.template_id}
                onChange={(e) => setCreateForm({ ...createForm, template_id: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm bg-white"
              >
                <option value="">Select a template...</option>
                {templates.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </select>
            </div>
          ) : (
            <>
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                  Subscription Plan *
                </label>
                <select
                  required
                  value={createForm.plan_id}
                  onChange={(e) => setCreateForm({ ...createForm, plan_id: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm bg-white"
                >
                  {plans.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} (${parseFloat(p.price).toFixed(2)} / {p.billing_period})
                    </option>
                  ))}
                </select>
              </div>

              {/* Product Lines */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-700 uppercase">Line Items</span>
                  <button
                    type="button"
                    onClick={() =>
                      setCreateForm({
                        ...createForm,
                        lines: [
                          ...createForm.lines,
                          { product_id: products[0]?.id || '', variant_id: '', quantity: 1, unit_price: '' },
                        ],
                      })
                    }
                    className="text-xs text-blue-600 hover:text-blue-700 font-semibold"
                  >
                    + Add Product Line
                  </button>
                </div>

                {createForm.lines.map((l, idx) => {
                  const prod = products.find((p) => p.id === l.product_id);
                  return (
                    <div key={idx} className="flex items-center gap-2 bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                      <div className="flex-1">
                        <select
                          value={l.product_id}
                          onChange={(e) => {
                            const newLines = [...createForm.lines];
                            newLines[idx].product_id = e.target.value;
                            newLines[idx].variant_id = '';
                            setCreateForm({ ...createForm, lines: newLines });
                          }}
                          className="w-full px-2 py-1.5 border border-slate-200 rounded text-xs bg-white"
                        >
                          {products.map((p) => (
                            <option key={p.id} value={p.id}>
                              {p.name} (${parseFloat(p.sales_price).toFixed(2)})
                            </option>
                          ))}
                        </select>
                      </div>

                      {prod && prod.variants && prod.variants.length > 0 && (
                        <div className="w-36">
                          <select
                            value={l.variant_id}
                            onChange={(e) => {
                              const newLines = [...createForm.lines];
                              newLines[idx].variant_id = e.target.value;
                              setCreateForm({ ...createForm, lines: newLines });
                            }}
                            className="w-full px-2 py-1.5 border border-slate-200 rounded text-xs bg-white"
                          >
                            <option value="">No Variant</option>
                            {prod.variants.map((v) => (
                              <option key={v.id} value={v.id}>
                                {v.value} (+${parseFloat(v.extra_price).toFixed(2)})
                              </option>
                            ))}
                          </select>
                        </div>
                      )}

                      <div className="w-20">
                        <input
                          type="number"
                          min="1"
                          value={l.quantity}
                          onChange={(e) => {
                            const newLines = [...createForm.lines];
                            newLines[idx].quantity = parseInt(e.target.value) || 1;
                            setCreateForm({ ...createForm, lines: newLines });
                          }}
                          className="w-full px-2 py-1.5 border border-slate-200 rounded text-xs text-center bg-white"
                          placeholder="Qty"
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Start Date
              </label>
              <input
                type="date"
                required
                value={createForm.start_date}
                onChange={(e) => setCreateForm({ ...createForm, start_date: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Payment Terms (Days)
              </label>
              <input
                type="number"
                min="0"
                required
                value={createForm.payment_terms}
                onChange={(e) => setCreateForm({ ...createForm, payment_terms: parseInt(e.target.value) || 0 })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setIsCreateModalOpen(false)}
              className="px-4 py-2 border border-slate-200 text-slate-600 rounded-lg text-sm font-medium hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition shadow-xs"
            >
              Create Subscription
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
