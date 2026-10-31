import React, { useEffect, useState } from 'react';
import { apiRequest } from '../../api/client';
import { useToast } from '../../components/ToastContext';
import { Modal } from '../../components/Modal';
import { StatusBadge } from '../../components/StatusBadge';
import {
  Receipt,
  Plus,
  Edit2,
  Trash2,
  Percent,
  DollarSign
} from 'lucide-react';

interface Tax {
  id: string;
  name: string;
  type: 'percent' | 'fixed';
  rate: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export const Taxes: React.FC = () => {
  const { addToast } = useToast();
  const [taxes, setTaxes] = useState<Tax[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingTax, setEditingTax] = useState<Tax | null>(null);
  const [form, setForm] = useState({
    name: '',
    type: 'percent' as 'percent' | 'fixed',
    rate: '0.00',
    is_active: true,
  });

  const loadTaxes = async () => {
    try {
      setLoading(true);
      const data = await apiRequest<any>('/taxes?page=1&page_size=50');
      const items = Array.isArray(data) ? data : (data?.items || []);
      setTaxes(items);
    } catch (err: any) {
      addToast(err.message || 'Failed to load taxes', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTaxes();
  }, []);

  const handleOpenCreate = () => {
    setEditingTax(null);
    setForm({
      name: '',
      type: 'percent',
      rate: '0.00',
      is_active: true,
    });
    setIsModalOpen(true);
  };

  const handleOpenEdit = (t: Tax) => {
    setEditingTax(t);
    setForm({
      name: t.name,
      type: t.type,
      rate: t.rate,
      is_active: t.is_active,
    });
    setIsModalOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingTax) {
        await apiRequest(`/taxes/${editingTax.id}`, {
          method: 'PUT',
          body: JSON.stringify(form),
        });
        addToast('Tax rule updated successfully', 'success');
      } else {
        await apiRequest('/taxes', {
          method: 'POST',
          body: JSON.stringify(form),
        });
        addToast('Tax rule created successfully', 'success');
      }
      setIsModalOpen(false);
      loadTaxes();
    } catch (err: any) {
      addToast(err.message || 'Failed to save tax rule', 'error');
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!window.confirm(`Delete tax rule "${name}"?`)) return;
    try {
      await apiRequest(`/taxes/${id}`, { method: 'DELETE' });
      addToast('Tax rule deleted', 'success');
      loadTaxes();
    } catch (err: any) {
      addToast(err.message || 'Failed to delete tax rule', 'error');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Tax Rules</h1>
          <p className="text-sm text-slate-500 mt-1">
            Define system taxes (percentage or fixed) automatically computed on line items.
          </p>
        </div>
        <button
          onClick={handleOpenCreate}
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition shadow-xs"
        >
          <Plus className="w-4 h-4" />
          <span>New Tax Rule</span>
        </button>
      </div>

      {/* Tax Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/75 border-b border-slate-200 text-slate-500 text-xs font-semibold uppercase tracking-wider">
                <th className="py-3 px-4">Tax Name</th>
                <th className="py-3 px-4">Calculation Type</th>
                <th className="py-3 px-4 text-right">Rate</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {loading ? (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-slate-400">
                    Loading tax rules...
                  </td>
                </tr>
              ) : taxes.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-slate-400">
                    No tax rules configured.
                  </td>
                </tr>
              ) : (
                taxes.map((t) => (
                  <tr key={t.id} className="hover:bg-slate-50/50 transition-colors">
                    <td className="py-3 px-4 font-semibold text-slate-900">{t.name}</td>
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-700 capitalize">
                        {t.type === 'percent' ? <Percent className="w-3 h-3 text-slate-500" /> : <DollarSign className="w-3 h-3 text-slate-500" />}
                        {t.type}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right font-semibold text-slate-900">
                      {t.type === 'percent' ? `${parseFloat(t.rate).toFixed(2)}%` : `$${parseFloat(t.rate).toFixed(2)}`}
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={t.is_active ? 'active' : 'inactive'} />
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="inline-flex items-center gap-2">
                        <button
                          onClick={() => handleOpenEdit(t)}
                          className="p-1.5 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-md transition"
                          title="Edit Tax Rule"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(t.id, t.name)}
                          className="p-1.5 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-md transition"
                          title="Delete Tax Rule"
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

      {/* Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingTax ? 'Edit Tax Rule' : 'Create Tax Rule'}
      >
        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Tax Name *
            </label>
            <input
              type="text"
              required
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
              placeholder="e.g. Standard VAT (20%) or Service Cess ($5.00)"
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
                <option value="fixed">Fixed Amount ($)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Rate Value *
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                required
                value={form.rate}
                onChange={(e) => setForm({ ...form, rate: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
              />
            </div>
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
              {editingTax ? 'Save Changes' : 'Create Tax Rule'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
