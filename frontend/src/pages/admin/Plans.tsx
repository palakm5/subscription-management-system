import React, { useEffect, useState } from 'react';
import { apiRequest } from '../../api/client';
import { useToast } from '../../components/ToastContext';
import { Modal } from '../../components/Modal';
import { StatusBadge } from '../../components/StatusBadge';
import {
  Layers,
  Plus,
  Edit2,
  Trash2,
  Check,
  X,
  Calendar,
  DollarSign
} from 'lucide-react';

interface Plan {
  id: string;
  name: string;
  price: string;
  billing_period: 'daily' | 'weekly' | 'monthly' | 'yearly';
  min_quantity: number;
  available_from?: string;
  available_to?: string;
  auto_close: boolean;
  closable: boolean;
  pausable: boolean;
  renewable: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export const Plans: React.FC = () => {
  const { addToast } = useToast();
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingPlan, setEditingPlan] = useState<Plan | null>(null);
  const [form, setForm] = useState({
    name: '',
    price: '0.00',
    billing_period: 'monthly',
    min_quantity: 1,
    available_from: '',
    available_to: '',
    auto_close: false,
    closable: true,
    pausable: true,
    renewable: true,
    is_active: true,
  });

  const loadPlans = async () => {
    try {
      setLoading(true);
      const data = await apiRequest<{ items: Plan[]; total: number }>('/plans?page=1&page_size=50');
      setPlans(data.items);
    } catch (err: any) {
      addToast(err.message || 'Failed to load plans', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPlans();
  }, []);

  const handleOpenCreate = () => {
    setEditingPlan(null);
    setForm({
      name: '',
      price: '0.00',
      billing_period: 'monthly',
      min_quantity: 1,
      available_from: '',
      available_to: '',
      auto_close: false,
      closable: true,
      pausable: true,
      renewable: true,
      is_active: true,
    });
    setIsModalOpen(true);
  };

  const handleOpenEdit = (p: Plan) => {
    setEditingPlan(p);
    setForm({
      name: p.name,
      price: p.price,
      billing_period: p.billing_period,
      min_quantity: p.min_quantity,
      available_from: p.available_from ? p.available_from.substring(0, 10) : '',
      available_to: p.available_to ? p.available_to.substring(0, 10) : '',
      auto_close: p.auto_close,
      closable: p.closable,
      pausable: p.pausable,
      renewable: p.renewable,
      is_active: p.is_active,
    });
    setIsModalOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload: any = {
        ...form,
        available_from: form.available_from || null,
        available_to: form.available_to || null,
      };

      if (editingPlan) {
        await apiRequest(`/plans/${editingPlan.id}`, {
          method: 'PUT',
          body: JSON.stringify(payload),
        });
        addToast('Plan updated successfully', 'success');
      } else {
        await apiRequest('/plans', {
          method: 'POST',
          body: JSON.stringify(payload),
        });
        addToast('Plan created successfully', 'success');
      }
      setIsModalOpen(false);
      loadPlans();
    } catch (err: any) {
      addToast(err.message || 'Failed to save plan', 'error');
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!window.confirm(`Delete plan "${name}"?`)) return;
    try {
      await apiRequest(`/plans/${id}`, { method: 'DELETE' });
      addToast('Plan deleted', 'success');
      loadPlans();
    } catch (err: any) {
      addToast(err.message || 'Failed to delete plan', 'error');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Subscription Plans</h1>
          <p className="text-sm text-slate-500 mt-1">
            Configure cadence, minimum quantities, and lifecycle rules (auto-close, pausing, renewals).
          </p>
        </div>
        <button
          onClick={handleOpenCreate}
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition shadow-xs"
        >
          <Plus className="w-4 h-4" />
          <span>New Plan</span>
        </button>
      </div>

      {/* Plans Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/75 border-b border-slate-200 text-slate-500 text-xs font-semibold uppercase tracking-wider">
                <th className="py-3 px-4">Plan Name</th>
                <th className="py-3 px-4">Billing Period</th>
                <th className="py-3 px-4 text-right">Base Price</th>
                <th className="py-3 px-4 text-center">Min Qty</th>
                <th className="py-3 px-4 text-center">Lifecycle Flags</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-400">
                    Loading subscription plans...
                  </td>
                </tr>
              ) : plans.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-400">
                    No plans found.
                  </td>
                </tr>
              ) : (
                plans.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-50/50 transition-colors">
                    <td className="py-3 px-4 font-semibold text-slate-900">
                      {p.name}
                      {(p.available_from || p.available_to) && (
                        <span className="block text-xs font-normal text-slate-400">
                          {p.available_from?.substring(0, 10) || 'Any'} to {p.available_to?.substring(0, 10) || 'Any'}
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-700 capitalize">
                        {p.billing_period}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right font-semibold text-slate-900">
                      ${parseFloat(p.price).toFixed(2)}
                    </td>
                    <td className="py-3 px-4 text-center text-slate-600 font-medium">
                      {p.min_quantity}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center justify-center gap-1.5 flex-wrap">
                        <span
                          title={p.pausable ? 'Pausable: Allowed' : 'Pausable: Disabled'}
                          className={`px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase ${
                            p.pausable ? 'bg-indigo-50 text-indigo-700' : 'bg-slate-100 text-slate-400'
                          }`}
                        >
                          Pausable
                        </span>
                        <span
                          title={p.closable ? 'Closable: Allowed' : 'Closable: Disabled'}
                          className={`px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase ${
                            p.closable ? 'bg-amber-50 text-amber-700' : 'bg-slate-100 text-slate-400'
                          }`}
                        >
                          Closable
                        </span>
                        <span
                          title={p.renewable ? 'Renewable: Allowed' : 'Renewable: Disabled'}
                          className={`px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase ${
                            p.renewable ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-400'
                          }`}
                        >
                          Renewable
                        </span>
                        {p.auto_close && (
                          <span
                            title="Auto Close at Expiry"
                            className="px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase bg-purple-50 text-purple-700"
                          >
                            Auto-Close
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={p.is_active ? 'active' : 'inactive'} />
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="inline-flex items-center gap-2">
                        <button
                          onClick={() => handleOpenEdit(p)}
                          className="p-1.5 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-md transition"
                          title="Edit Plan"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(p.id, p.name)}
                          className="p-1.5 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-md transition"
                          title="Delete Plan"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Plan Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingPlan ? 'Edit Subscription Plan' : 'Create Subscription Plan'}
      >
        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Plan Name *
            </label>
            <input
              type="text"
              required
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
              placeholder="e.g. Monthly Standard License"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Base Price ($) *
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                required
                value={form.price}
                onChange={(e) => setForm({ ...form, price: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Billing Cadence *
              </label>
              <select
                value={form.billing_period}
                onChange={(e) => setForm({ ...form, billing_period: e.target.value as any })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm bg-white"
              >
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
                <option value="yearly">Yearly</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Min Line Quantity *
              </label>
              <input
                type="number"
                min="1"
                required
                value={form.min_quantity}
                onChange={(e) => setForm({ ...form, min_quantity: parseInt(e.target.value) || 1 })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Status
              </label>
              <select
                value={form.is_active ? 'true' : 'false'}
                onChange={(e) => setForm({ ...form, is_active: e.target.value === 'true' })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm bg-white"
              >
                <option value="true">Active</option>
                <option value="false">Inactive</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Available From
              </label>
              <input
                type="date"
                value={form.available_from}
                onChange={(e) => setForm({ ...form, available_from: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Available To
              </label>
              <input
                type="date"
                value={form.available_to}
                onChange={(e) => setForm({ ...form, available_to: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
              />
            </div>
          </div>

          <div className="border-t border-slate-100 pt-3 space-y-2">
            <span className="block text-xs font-bold text-slate-800 uppercase tracking-wider mb-2">
              Plan Lifecycle Rules
            </span>
            <div className="grid grid-cols-2 gap-2 text-sm text-slate-700">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.pausable}
                  onChange={(e) => setForm({ ...form, pausable: e.target.checked })}
                  className="rounded text-blue-600 focus:ring-blue-500"
                />
                <span>Allow Pausing</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.closable}
                  onChange={(e) => setForm({ ...form, closable: e.target.checked })}
                  className="rounded text-blue-600 focus:ring-blue-500"
                />
                <span>Allow Early Close</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.renewable}
                  onChange={(e) => setForm({ ...form, renewable: e.target.checked })}
                  className="rounded text-blue-600 focus:ring-blue-500"
                />
                <span>Allow Renewal</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.auto_close}
                  onChange={(e) => setForm({ ...form, auto_close: e.target.checked })}
                  className="rounded text-blue-600 focus:ring-blue-500"
                />
                <span>Auto-Close at Expiry</span>
              </label>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setIsModalOpen(false)}
              className="px-4 py-2 border border-slate-200 text-slate-600 rounded-lg text-sm font-medium hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition shadow-xs"
            >
              {editingPlan ? 'Save Changes' : 'Create Plan'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
