import React, { useEffect, useState } from 'react';
import { apiRequest } from '../../api/client';
import { useToast } from '../../components/ToastContext';
import { Modal } from '../../components/Modal';
import { StatusBadge } from '../../components/StatusBadge';
import {
  Tag,
  Plus,
  Edit2,
  Trash2,
  Percent,
  DollarSign,
  Calendar,
  Layers,
  Repeat
} from 'lucide-react';

interface Discount {
  id: string;
  name: string;
  type: 'fixed' | 'percent';
  value: string;
  min_purchase?: string;
  min_quantity?: number;
  start_date?: string;
  end_date?: string;
  usage_limit?: number;
  times_used: number;
  scope: 'product' | 'subscription';
  product_ids: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export const Discounts: React.FC = () => {
  const { addToast } = useToast();
  const [discounts, setDiscounts] = useState<Discount[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingDiscount, setEditingDiscount] = useState<Discount | null>(null);
  const [form, setForm] = useState({
    name: '',
    type: 'percent' as 'fixed' | 'percent',
    value: '10.00',
    min_purchase: '',
    min_quantity: '',
    start_date: '',
    end_date: '',
    usage_limit: '',
    scope: 'subscription' as 'product' | 'subscription',
    is_active: true,
  });

  const loadDiscounts = async () => {
    try {
      setLoading(true);
      const data = await apiRequest<any>('/discounts?page=1&page_size=50');
      const items = Array.isArray(data) ? data : (data?.items || []);
      setDiscounts(items);
    } catch (err: any) {
      addToast(err.message || 'Failed to load discounts', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDiscounts();
  }, []);

  const handleOpenCreate = () => {
    setEditingDiscount(null);
    setForm({
      name: '',
      type: 'percent',
      value: '10.00',
      min_purchase: '',
      min_quantity: '',
      start_date: '',
      end_date: '',
      usage_limit: '',
      scope: 'subscription',
      is_active: true,
    });
    setIsModalOpen(true);
  };

  const handleOpenEdit = (d: Discount) => {
    setEditingDiscount(d);
    setForm({
      name: d.name,
      type: d.type,
      value: d.value,
      min_purchase: d.min_purchase || '',
      min_quantity: d.min_quantity?.toString() || '',
      start_date: d.start_date ? d.start_date.substring(0, 10) : '',
      end_date: d.end_date ? d.end_date.substring(0, 10) : '',
      usage_limit: d.usage_limit?.toString() || '',
      scope: d.scope,
      is_active: d.is_active,
    });
    setIsModalOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload: any = {
        name: form.name,
        type: form.type,
        value: form.value,
        min_purchase: form.min_purchase ? form.min_purchase : null,
        min_quantity: form.min_quantity ? parseInt(form.min_quantity) : null,
        start_date: form.start_date ? form.start_date : null,
        end_date: form.end_date ? form.end_date : null,
        usage_limit: form.usage_limit ? parseInt(form.usage_limit) : null,
        scope: form.scope,
        is_active: form.is_active,
      };

      if (editingDiscount) {
        await apiRequest(`/discounts/${editingDiscount.id}`, {
          method: 'PUT',
          body: JSON.stringify(payload),
        });
        addToast('Discount updated successfully', 'success');
      } else {
        await apiRequest('/discounts', {
          method: 'POST',
          body: JSON.stringify(payload),
        });
        addToast('Discount created successfully', 'success');
      }
      setIsModalOpen(false);
      loadDiscounts();
    } catch (err: any) {
      addToast(err.message || 'Failed to save discount', 'error');
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!window.confirm(`Delete discount "${name}"?`)) return;
    try {
      await apiRequest(`/discounts/${id}`, { method: 'DELETE' });
      addToast('Discount deleted', 'success');
      loadDiscounts();
    } catch (err: any) {
      addToast(err.message || 'Failed to delete discount', 'error');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Discounts & Promotions</h1>
          <p className="text-sm text-slate-500 mt-1">
            Configure automated subscription or line-item discounts with threshold and usage controls.
          </p>
        </div>
        <button
          onClick={handleOpenCreate}
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition shadow-xs"
        >
          <Plus className="w-4 h-4" />
          <span>New Discount</span>
        </button>
      </div>

      {/* Discounts Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/75 border-b border-slate-200 text-slate-500 text-xs font-semibold uppercase tracking-wider">
                <th className="py-3 px-4">Discount Name</th>
                <th className="py-3 px-4">Scope</th>
                <th className="py-3 px-4 text-right">Value</th>
                <th className="py-3 px-4 text-center">Limits & Conditions</th>
                <th className="py-3 px-4 text-center">Usage</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-400">
                    Loading discounts...
                  </td>
                </tr>
              ) : discounts.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-400">
                    No discounts configured.
                  </td>
                </tr>
              ) : (
                discounts.map((d) => (
                  <tr key={d.id} className="hover:bg-slate-50/50 transition-colors">
                    <td className="py-3 px-4 font-semibold text-slate-900">
                      {d.name}
                      {(d.start_date || d.end_date) && (
                        <span className="block text-xs font-normal text-slate-400">
                          {d.start_date?.substring(0, 10) || 'Immediate'} to {d.end_date?.substring(0, 10) || 'Indefinite'}
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-700 capitalize">
                        {d.scope === 'subscription' ? <Repeat className="w-3 h-3" /> : <Layers className="w-3 h-3" />}
                        {d.scope}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right font-semibold text-slate-900">
                      {d.type === 'percent' ? `${parseFloat(d.value).toFixed(2)}%` : `$${parseFloat(d.value).toFixed(2)}`}
                    </td>
                    <td className="py-3 px-4 text-center text-xs text-slate-500">
                      {d.min_purchase && <div>Min Spend: ${parseFloat(d.min_purchase).toFixed(2)}</div>}
                      {d.min_quantity && <div>Min Qty: {d.min_quantity}</div>}
                      {!d.min_purchase && !d.min_quantity && <span className="text-slate-400">No minimums</span>}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span className="text-xs font-semibold text-slate-700">
                        {d.times_used} {d.usage_limit ? `/ ${d.usage_limit}` : 'used'}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={d.is_active ? 'active' : 'inactive'} />
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="inline-flex items-center gap-2">
                        <button
                          onClick={() => handleOpenEdit(d)}
                          className="p-1.5 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-md transition"
                          title="Edit Discount"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(d.id, d.name)}
                          className="p-1.5 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-md transition"
                          title="Delete Discount"
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

      {/* Discount Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingDiscount ? 'Edit Discount' : 'Create Discount'}
      >
        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Discount Name *
            </label>
            <input
              type="text"
              required
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
              placeholder="e.g. Q4 Growth Promo 15%"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Type *
              </label>
              <select
                value={form.type}
                onChange={(e) => setForm({ ...form, type: e.target.value as any })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm bg-white"
              >
                <option value="percent">Percentage (%)</option>
                <option value="fixed">Fixed Dollar ($)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Discount Value *
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                required
                value={form.value}
                onChange={(e) => setForm({ ...form, value: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Scope *
              </label>
              <select
                value={form.scope}
                onChange={(e) => setForm({ ...form, scope: e.target.value as any })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm bg-white"
              >
                <option value="subscription">Subscription Subtotal</option>
                <option value="product">Specific Products Only</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Usage Limit (Count)
              </label>
              <input
                type="number"
                min="1"
                value={form.usage_limit}
                onChange={(e) => setForm({ ...form, usage_limit: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                placeholder="Leave blank for unlimited"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Min Purchase Amount ($)
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={form.min_purchase}
                onChange={(e) => setForm({ ...form, min_purchase: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Min Line Quantity
              </label>
              <input
                type="number"
                min="1"
                value={form.min_quantity}
                onChange={(e) => setForm({ ...form, min_quantity: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Start Date
              </label>
              <input
                type="date"
                value={form.start_date}
                onChange={(e) => setForm({ ...form, start_date: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                End Date
              </label>
              <input
                type="date"
                value={form.end_date}
                onChange={(e) => setForm({ ...form, end_date: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
              />
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
              {editingDiscount ? 'Save Changes' : 'Create Discount'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
