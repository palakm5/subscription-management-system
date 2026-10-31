import React, { useEffect, useState } from 'react';
import { apiRequest, ApiException } from '../../api/client';
import { useToast } from '../../components/ToastContext';
import { Modal } from '../../components/Modal';
import { StatusBadge } from '../../components/StatusBadge';
import {
  Package,
  Plus,
  Search,
  Layers,
  Edit2,
  Trash2,
  ChevronRight,
  Sparkles
} from 'lucide-react';

interface Variant {
  id: string;
  attribute: string;
  value: string;
  extra_price: string;
}

interface Product {
  id: string;
  name: string;
  type: string;
  sales_price: string;
  cost_price: string;
  notes?: string;
  tax_ids: string[];
  is_active: boolean;
  variants: Variant[];
  created_at: string;
  updated_at: string;
}

export const Products: React.FC = () => {
  const { addToast } = useToast();
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');
  const [page, setPage] = useState<number>(1);
  const [total, setTotal] = useState<number>(0);

  // Create / Edit Product Modal
  const [isProductModalOpen, setIsProductModalOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [productForm, setProductForm] = useState({
    name: '',
    type: 'service',
    sales_price: '0.00',
    cost_price: '0.00',
    notes: '',
    is_active: true,
  });

  // Variant Modal
  const [selectedProductForVariants, setSelectedProductForVariants] = useState<Product | null>(null);
  const [variantForm, setVariantForm] = useState({
    attribute: '',
    value: '',
    extra_price: '0.00',
  });

  const loadProducts = async () => {
    try {
      setLoading(true);
      const query = new URLSearchParams({
        page: page.toString(),
        page_size: '20',
        ...(search ? { q: search } : {}),
      });
      const data = await apiRequest<any>(`/products?${query.toString()}`);
      const items = Array.isArray(data) ? data : (data?.items || []);
      setProducts(items);
      setTotal(Array.isArray(data) ? data.length : (data?.total || items.length));
    } catch (err: any) {
      addToast(err.message || 'Failed to load products', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProducts();
  }, [page, search]);

  const handleOpenCreateProduct = () => {
    setEditingProduct(null);
    setProductForm({
      name: '',
      type: 'service',
      sales_price: '0.00',
      cost_price: '0.00',
      notes: '',
      is_active: true,
    });
    setIsProductModalOpen(true);
  };

  const handleOpenEditProduct = (p: Product) => {
    setEditingProduct(p);
    setProductForm({
      name: p.name,
      type: p.type,
      sales_price: p.sales_price,
      cost_price: p.cost_price,
      notes: p.notes || '',
      is_active: p.is_active,
    });
    setIsProductModalOpen(true);
  };

  const handleSaveProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingProduct) {
        await apiRequest(`/products/${editingProduct.id}`, {
          method: 'PUT',
          body: JSON.stringify(productForm),
        });
        addToast('Product updated successfully', 'success');
      } else {
        await apiRequest('/products', {
          method: 'POST',
          body: JSON.stringify(productForm),
        });
        addToast('Product created successfully', 'success');
      }
      setIsProductModalOpen(false);
      loadProducts();
    } catch (err: any) {
      addToast(err.message || 'Failed to save product', 'error');
    }
  };

  const handleDeleteProduct = async (id: string, name: string) => {
    if (!window.confirm(`Are you sure you want to delete product "${name}"?`)) return;
    try {
      await apiRequest(`/products/${id}`, { method: 'DELETE' });
      addToast('Product deleted', 'success');
      loadProducts();
    } catch (err: any) {
      addToast(err.message || 'Failed to delete product', 'error');
    }
  };

  // Variant operations
  const handleAddVariant = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProductForVariants) return;
    try {
      await apiRequest(`/products/${selectedProductForVariants.id}/variants`, {
        method: 'POST',
        body: JSON.stringify(variantForm),
      });
      addToast('Variant added', 'success');
      setVariantForm({ attribute: '', value: '', extra_price: '0.00' });
      
      // refresh product details
      const updated = await apiRequest<Product>(`/products/${selectedProductForVariants.id}`);
      setSelectedProductForVariants(updated);
      loadProducts();
    } catch (err: any) {
      addToast(err.message || 'Failed to add variant', 'error');
    }
  };

  const handleDeleteVariant = async (variantId: string) => {
    if (!selectedProductForVariants) return;
    try {
      await apiRequest(`/products/${selectedProductForVariants.id}/variants/${variantId}`, {
        method: 'DELETE',
      });
      addToast('Variant deleted', 'success');
      const updated = await apiRequest<Product>(`/products/${selectedProductForVariants.id}`);
      setSelectedProductForVariants(updated);
      loadProducts();
    } catch (err: any) {
      addToast(err.message || 'Failed to delete variant', 'error');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Products & Variants</h1>
          <p className="text-sm text-slate-500 mt-1">
            Manage your service offerings, base pricing, and variant add-ons.
          </p>
        </div>
        <button
          onClick={handleOpenCreateProduct}
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition shadow-xs"
        >
          <Plus className="w-4 h-4" />
          <span>New Product</span>
        </button>
      </div>

      {/* Filter and Search */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search products by name or type..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 border border-slate-200 rounded-lg text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
          />
        </div>
        <div className="text-xs text-slate-500 font-medium">
          Total Products: {total}
        </div>
      </div>

      {/* Products Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/75 border-b border-slate-200 text-slate-500 text-xs font-semibold uppercase tracking-wider">
                <th className="py-3 px-4">Product Name</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4 text-right">Sales Price</th>
                <th className="py-3 px-4 text-right">Cost Price</th>
                <th className="py-3 px-4 text-center">Variants</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-400">
                    Loading products...
                  </td>
                </tr>
              ) : products.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-400">
                    No products found.
                  </td>
                </tr>
              ) : (
                products.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-50/50 transition-colors">
                    <td className="py-3 px-4 font-semibold text-slate-900">
                      {p.name}
                      {p.notes && (
                        <span className="block text-xs font-normal text-slate-500 truncate max-w-xs">
                          {p.notes}
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-slate-600 capitalize">{p.type}</td>
                    <td className="py-3 px-4 text-right font-medium text-slate-900">
                      ${parseFloat(p.sales_price).toFixed(2)}
                    </td>
                    <td className="py-3 px-4 text-right text-slate-500">
                      ${parseFloat(p.cost_price).toFixed(2)}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <button
                        onClick={() => setSelectedProductForVariants(p)}
                        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-blue-50 text-blue-700 hover:bg-blue-100 transition"
                      >
                        <Layers className="w-3.5 h-3.5" />
                        <span>{p.variants?.length || 0} variants</span>
                      </button>
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={p.is_active ? 'active' : 'inactive'} />
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="inline-flex items-center gap-2">
                        <button
                          onClick={() => handleOpenEditProduct(p)}
                          className="p-1.5 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-md transition"
                          title="Edit Product"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteProduct(p.id, p.name)}
                          className="p-1.5 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-md transition"
                          title="Delete Product"
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

      {/* Product Form Modal */}
      <Modal
        isOpen={isProductModalOpen}
        onClose={() => setIsProductModalOpen(false)}
        title={editingProduct ? 'Edit Product' : 'Create New Product'}
      >
        <form onSubmit={handleSaveProduct} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Product Name *
            </label>
            <input
              type="text"
              required
              value={productForm.name}
              onChange={(e) => setProductForm({ ...productForm, name: e.target.value })}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
              placeholder="e.g. Enterprise Cloud Hosting"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Product Type
              </label>
              <select
                value={productForm.type}
                onChange={(e) => setProductForm({ ...productForm, type: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm bg-white"
              >
                <option value="service">Service</option>
                <option value="software">Software</option>
                <option value="subscription">Subscription</option>
                <option value="addon">Add-on</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Status
              </label>
              <select
                value={productForm.is_active ? 'true' : 'false'}
                onChange={(e) => setProductForm({ ...productForm, is_active: e.target.value === 'true' })}
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
                Base Sales Price ($) *
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                required
                value={productForm.sales_price}
                onChange={(e) => setProductForm({ ...productForm, sales_price: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Cost Price ($)
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={productForm.cost_price}
                onChange={(e) => setProductForm({ ...productForm, cost_price: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Notes / Description
            </label>
            <textarea
              rows={3}
              value={productForm.notes}
              onChange={(e) => setProductForm({ ...productForm, notes: e.target.value })}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
              placeholder="Internal notes or description..."
            />
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setIsProductModalOpen(false)}
              className="px-4 py-2 border border-slate-200 text-slate-600 rounded-lg text-sm font-medium hover:bg-slate-50 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition shadow-xs"
            >
              {editingProduct ? 'Save Changes' : 'Create Product'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Variants Manager Modal */}
      <Modal
        isOpen={!!selectedProductForVariants}
        onClose={() => setSelectedProductForVariants(null)}
        title={`Variants for ${selectedProductForVariants?.name || ''}`}
        maxWidth="max-w-2xl"
      >
        <div className="space-y-6">
          <p className="text-xs text-slate-500">
            Variants add specific options (e.g., brand, tier, region) with an additional cost on top of the base sales price ($
            {selectedProductForVariants ? parseFloat(selectedProductForVariants.sales_price).toFixed(2) : '0.00'}).
          </p>

          {/* Add Variant Form */}
          <form onSubmit={handleAddVariant} className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-3">
            <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">Add New Variant</h4>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="block text-[11px] font-semibold text-slate-600 uppercase mb-1">
                  Attribute *
                </label>
                <input
                  type="text"
                  placeholder="e.g. brand, region"
                  required
                  value={variantForm.attribute}
                  onChange={(e) => setVariantForm({ ...variantForm, attribute: e.target.value })}
                  className="w-full px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-sm"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-slate-600 uppercase mb-1">
                  Value *
                </label>
                <input
                  type="text"
                  placeholder="e.g. Odoo, US-East"
                  required
                  value={variantForm.value}
                  onChange={(e) => setVariantForm({ ...variantForm, value: e.target.value })}
                  className="w-full px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-sm"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-slate-600 uppercase mb-1">
                  Extra Price ($) *
                </label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={variantForm.extra_price}
                  onChange={(e) => setVariantForm({ ...variantForm, extra_price: e.target.value })}
                  className="w-full px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-sm"
                />
              </div>
            </div>
            <div className="flex justify-end pt-2">
              <button
                type="submit"
                className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold transition"
              >
                Add Variant
              </button>
            </div>
          </form>

          {/* Variants List */}
          <div className="rounded-xl border border-slate-200 overflow-hidden">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 text-xs font-semibold uppercase">
                  <th className="py-2.5 px-3">Attribute</th>
                  <th className="py-2.5 px-3">Value</th>
                  <th className="py-2.5 px-3 text-right">Extra Price</th>
                  <th className="py-2.5 px-3 text-right">Combined Unit Price</th>
                  <th className="py-2.5 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {selectedProductForVariants?.variants && selectedProductForVariants.variants.length > 0 ? (
                  selectedProductForVariants.variants.map((v) => {
                    const basePrice = parseFloat(selectedProductForVariants.sales_price);
                    const extra = parseFloat(v.extra_price);
                    const combined = basePrice + extra;
                    return (
                      <tr key={v.id} className="hover:bg-slate-50/50">
                        <td className="py-2.5 px-3 font-medium text-slate-800">{v.attribute}</td>
                        <td className="py-2.5 px-3 text-slate-600">{v.value}</td>
                        <td className="py-2.5 px-3 text-right text-slate-700">
                          +${extra.toFixed(2)}
                        </td>
                        <td className="py-2.5 px-3 text-right font-semibold text-slate-900">
                          ${combined.toFixed(2)}
                        </td>
                        <td className="py-2.5 px-3 text-right">
                          <button
                            onClick={() => handleDeleteVariant(v.id)}
                            className="p-1 text-slate-400 hover:text-red-600 rounded transition"
                            title="Delete Variant"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={5} className="py-6 text-center text-slate-400 text-xs">
                      No variants configured for this product.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          <div className="flex justify-end">
            <button
              onClick={() => setSelectedProductForVariants(null)}
              className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-sm font-medium transition"
            >
              Close
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
