import React, { useEffect, useState } from 'react';
import { apiRequest } from '../../api/client';
import { useToast } from '../../components/ToastContext';
import { Modal } from '../../components/Modal';
import {
  FileSpreadsheet,
  Plus,
  Edit2,
  Trash2,
  Layers,
  Clock,
  Package
} from 'lucide-react';

interface TemplateLine {
  product_id: string;
  variant_id?: string;
  quantity: number;
}

interface QuotationTemplate {
  id: string;
  name: string;
  validity_days: number;
  plan_id: string;
  lines: TemplateLine[];
  created_at: string;
  updated_at: string;
}

interface Product {
  id: string;
  name: string;
  sales_price: string;
  variants: { id: string; attribute: string; value: string; extra_price: string }[];
}

interface Plan {
  id: string;
  name: string;
  billing_period: string;
  price: string;
}

export const QuotationTemplates: React.FC = () => {
  const { addToast } = useToast();
  const [templates, setTemplates] = useState<QuotationTemplate[]>([]);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<QuotationTemplate | null>(null);
  const [form, setForm] = useState({
    name: '',
    validity_days: 30,
    plan_id: '',
    lines: [] as TemplateLine[],
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const [tmplRes, planRes, prodRes] = await Promise.all([
        apiRequest<{ items: QuotationTemplate[]; total: number }>('/quotation-templates?page=1&page_size=50'),
        apiRequest<{ items: Plan[]; total: number }>('/plans?page=1&page_size=50'),
        apiRequest<{ items: Product[]; total: number }>('/products?page=1&page_size=100'),
      ]);
      setTemplates(tmplRes.items);
      setPlans(planRes.items);
      setProducts(prodRes.items);
    } catch (err: any) {
      addToast(err.message || 'Failed to load templates data', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleOpenCreate = () => {
    setEditingTemplate(null);
    setForm({
      name: '',
      validity_days: 30,
      plan_id: plans[0]?.id || '',
      lines: products[0] ? [{ product_id: products[0].id, quantity: 1 }] : [],
    });
    setIsModalOpen(true);
  };

  const handleOpenEdit = (t: QuotationTemplate) => {
    setEditingTemplate(t);
    setForm({
      name: t.name,
      validity_days: t.validity_days,
      plan_id: t.plan_id,
      lines: t.lines && t.lines.length > 0 ? t.lines : [],
    });
    setIsModalOpen(true);
  };

  const handleAddLine = () => {
    if (products.length === 0) return;
    setForm({
      ...form,
      lines: [...form.lines, { product_id: products[0].id, quantity: 1 }],
    });
  };

  const handleRemoveLine = (idx: number) => {
    const updated = [...form.lines];
    updated.splice(idx, 1);
    setForm({ ...form, lines: updated });
  };

  const handleUpdateLine = (idx: number, field: keyof TemplateLine, val: any) => {
    const updated = [...form.lines];
    updated[idx] = { ...updated[idx], [field]: val };
    setForm({ ...form, lines: updated });
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.plan_id) {
      addToast('Please select a subscription plan', 'error');
      return;
    }
    if (form.lines.length === 0) {
      addToast('Please add at least one line item', 'error');
      return;
    }

    try {
      if (editingTemplate) {
        await apiRequest(`/quotation-templates/${editingTemplate.id}`, {
          method: 'PUT',
          body: JSON.stringify(form),
        });
        addToast('Template updated successfully', 'success');
      } else {
        await apiRequest('/quotation-templates', {
          method: 'POST',
          body: JSON.stringify(form),
        });
        addToast('Template created successfully', 'success');
      }
      setIsModalOpen(false);
      loadData();
    } catch (err: any) {
      addToast(err.message || 'Failed to save quotation template', 'error');
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!window.confirm(`Delete quotation template "${name}"?`)) return;
    try {
      await apiRequest(`/quotation-templates/${id}`, { method: 'DELETE' });
      addToast('Template deleted', 'success');
      loadData();
    } catch (err: any) {
      addToast(err.message || 'Failed to delete template', 'error');
    }
  };

  const getPlanName = (planId: string) => {
    return plans.find((p) => p.id === planId)?.name || planId;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Quotation Templates</h1>
          <p className="text-sm text-slate-500 mt-1">
            Pre-configured bundles with plans, products, and validity periods for one-click quotations.
          </p>
        </div>
        <button
          onClick={handleOpenCreate}
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition shadow-xs"
        >
          <Plus className="w-4 h-4" />
          <span>New Template</span>
        </button>
      </div>

      {/* Templates Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/75 border-b border-slate-200 text-slate-500 text-xs font-semibold uppercase tracking-wider">
                <th className="py-3 px-4">Template Name</th>
                <th className="py-3 px-4">Base Subscription Plan</th>
                <th className="py-3 px-4 text-center">Validity</th>
                <th className="py-3 px-4 text-center">Lines Count</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {loading ? (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-slate-400">
                    Loading quotation templates...
                  </td>
                </tr>
              ) : templates.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-slate-400">
                    No quotation templates found.
                  </td>
                </tr>
              ) : (
                templates.map((t) => (
                  <tr key={t.id} className="hover:bg-slate-50/50 transition-colors">
                    <td className="py-3 px-4 font-semibold text-slate-900">{t.name}</td>
                    <td className="py-3 px-4 text-slate-600">{getPlanName(t.plan_id)}</td>
                    <td className="py-3 px-4 text-center">
                      <span className="inline-flex items-center gap-1 text-xs font-medium text-slate-700">
                        <Clock className="w-3.5 h-3.5 text-slate-400" />
                        {t.validity_days} days
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span className="px-2 py-0.5 rounded text-xs font-semibold bg-slate-100 text-slate-700">
                        {t.lines?.length || 0} items
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="inline-flex items-center gap-2">
                        <button
                          onClick={() => handleOpenEdit(t)}
                          className="p-1.5 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-md transition"
                          title="Edit Template"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(t.id, t.name)}
                          className="p-1.5 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-md transition"
                          title="Delete Template"
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

      {/* Template Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingTemplate ? 'Edit Quotation Template' : 'Create Quotation Template'}
        maxWidth="max-w-2xl"
      >
        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Template Name *
            </label>
            <input
              type="text"
              required
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
              placeholder="e.g. Standard SaaS Onboarding Package"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Associated Plan *
              </label>
              <select
                required
                value={form.plan_id}
                onChange={(e) => setForm({ ...form, plan_id: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm bg-white"
              >
                {plans.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} (${parseFloat(p.price).toFixed(2)} / {p.billing_period})
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Quote Validity (Days) *
              </label>
              <input
                type="number"
                min="1"
                required
                value={form.validity_days}
                onChange={(e) => setForm({ ...form, validity_days: parseInt(e.target.value) || 30 })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
              />
            </div>
          </div>

          {/* Lines */}
          <div className="border-t border-slate-100 pt-4 space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Pre-configured Product Lines
              </h4>
              <button
                type="button"
                onClick={handleAddLine}
                className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-md transition"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Line</span>
              </button>
            </div>

            <div className="space-y-2">
              {form.lines.map((line, idx) => {
                const prod = products.find((p) => p.id === line.product_id);
                return (
                  <div key={idx} className="flex items-center gap-2 bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                    <div className="flex-1">
                      <select
                        value={line.product_id}
                        onChange={(e) => handleUpdateLine(idx, 'product_id', e.target.value)}
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
                      <div className="w-40">
                        <select
                          value={line.variant_id || ''}
                          onChange={(e) => handleUpdateLine(idx, 'variant_id', e.target.value || undefined)}
                          className="w-full px-2 py-1.5 border border-slate-200 rounded text-xs bg-white"
                        >
                          <option value="">No Variant</option>
                          {prod.variants.map((v) => (
                            <option key={v.id} value={v.id}>
                              {v.attribute}: {v.value} (+${parseFloat(v.extra_price).toFixed(2)})
                            </option>
                          ))}
                        </select>
                      </div>
                    )}

                    <div className="w-20">
                      <input
                        type="number"
                        min="1"
                        value={line.quantity}
                        onChange={(e) => handleUpdateLine(idx, 'quantity', parseInt(e.target.value) || 1)}
                        className="w-full px-2 py-1.5 border border-slate-200 rounded text-xs bg-white text-center"
                        placeholder="Qty"
                      />
                    </div>

                    <button
                      type="button"
                      onClick={() => handleRemoveLine(idx)}
                      className="p-1 text-slate-400 hover:text-red-600 rounded transition"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                );
              })}
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
              {editingTemplate ? 'Save Changes' : 'Create Template'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
