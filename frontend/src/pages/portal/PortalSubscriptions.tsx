import React, { useEffect, useState } from 'react';
import { apiRequest } from '../../api/client';
import { useToast } from '../../components/ToastContext';
import { StatusBadge } from '../../components/StatusBadge';
import { Modal } from '../../components/Modal';
import {
  Repeat,
  Calendar,
  Layers,
  PauseCircle,
  PlayCircle,
  XCircle,
  Eye,
  CreditCard
} from 'lucide-react';

interface SubscriptionLine {
  line_id: string;
  product_name: string;
  variant_label?: string;
  quantity: number;
  unit_price: string;
  amount: string;
}

interface PortalSubscription {
  id: string;
  number: string;
  plan_id: string;
  status: 'draft' | 'quotation' | 'confirmed' | 'active' | 'paused' | 'closed';
  start_date: string;
  expiry_date: string;
  next_invoice_date?: string;
  lines: SubscriptionLine[];
}

export const PortalSubscriptions: React.FC = () => {
  const { addToast } = useToast();
  const [subs, setSubs] = useState<PortalSubscription[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedSub, setSelectedSub] = useState<PortalSubscription | null>(null);

  const loadSubscriptions = async () => {
    try {
      setLoading(true);
      const data = await apiRequest<{ items: PortalSubscription[]; total: number }>('/portal/subscriptions?page=1&page_size=50');
      setSubs(data.items);
    } catch (err: any) {
      addToast(err.message || 'Failed to load your subscriptions', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSubscriptions();
  }, []);

  const handleTransition = async (id: string, target: string) => {
    try {
      const updated = await apiRequest<PortalSubscription>(`/portal/subscriptions/${id}/transition`, {
        method: 'POST',
        body: JSON.stringify({ to: target }),
      });
      addToast(`Subscription is now ${target}`, 'success');
      setSelectedSub(updated);
      loadSubscriptions();
    } catch (err: any) {
      addToast(err.message || 'Action could not be completed', 'error');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">My Subscriptions</h1>
        <p className="text-sm text-slate-500 mt-1">
          Review your active service plans, renewal dates, and line items.
        </p>
      </div>

      {/* Subscriptions Grid */}
      {loading ? (
        <div className="p-8 text-center text-slate-400 bg-white rounded-xl border border-slate-200">
          Loading your subscriptions...
        </div>
      ) : subs.length === 0 ? (
        <div className="p-8 text-center text-slate-400 bg-white rounded-xl border border-slate-200">
          You currently have no active or historical subscriptions.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {subs.map((s) => (
            <div
              key={s.id}
              className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex flex-col justify-between space-y-4 hover:border-slate-300 transition"
            >
              <div>
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-blue-700 text-base">{s.number}</span>
                  <StatusBadge status={s.status} />
                </div>

                <div className="mt-3 space-y-1 text-xs text-slate-600">
                  <div className="flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5 text-slate-400" />
                    <span>Period: {s.start_date.substring(0, 10)} to {s.expiry_date.substring(0, 10)}</span>
                  </div>
                  {s.next_invoice_date && (
                    <div className="flex items-center gap-1.5 font-semibold text-slate-800">
                      <CreditCard className="w-3.5 h-3.5 text-blue-600" />
                      <span>Next invoice date: {s.next_invoice_date.substring(0, 10)}</span>
                    </div>
                  )}
                </div>

                {/* Lines summary */}
                <div className="mt-4 pt-3 border-t border-slate-100">
                  <span className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1">
                    Services Included ({s.lines.length})
                  </span>
                  <ul className="text-xs text-slate-700 space-y-1">
                    {s.lines.map((l, i) => (
                      <li key={i} className="flex justify-between">
                        <span>
                          {l.quantity}x {l.product_name} {l.variant_label ? `(${l.variant_label})` : ''}
                        </span>
                        <span className="font-medium text-slate-900">${parseFloat(l.amount).toFixed(2)}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Actions */}
              <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                <button
                  onClick={() => setSelectedSub(s)}
                  className="text-xs font-semibold text-blue-600 hover:text-blue-800"
                >
                  View Details
                </button>

                <div className="flex items-center gap-2">
                  {s.status === 'active' && (
                    <>
                      <button
                        onClick={() => handleTransition(s.id, 'paused')}
                        className="px-2.5 py-1 text-xs font-medium bg-amber-50 text-amber-700 hover:bg-amber-100 rounded transition"
                      >
                        Pause
                      </button>
                      <button
                        onClick={() => handleTransition(s.id, 'closed')}
                        className="px-2.5 py-1 text-xs font-medium bg-rose-50 text-rose-700 hover:bg-rose-100 rounded transition"
                      >
                        Cancel
                      </button>
                    </>
                  )}

                  {s.status === 'paused' && (
                    <button
                      onClick={() => handleTransition(s.id, 'active')}
                      className="px-2.5 py-1 text-xs font-medium bg-emerald-50 text-emerald-700 hover:bg-emerald-100 rounded transition"
                    >
                      Resume
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Details Modal */}
      <Modal
        isOpen={!!selectedSub}
        onClose={() => setSelectedSub(null)}
        title={selectedSub ? `Subscription Details: ${selectedSub.number}` : ''}
      >
        {selectedSub && (
          <div className="space-y-4">
            <div className="p-3 bg-slate-50 rounded-lg text-xs space-y-1 text-slate-700">
              <div className="flex justify-between">
                <span>Status:</span>
                <StatusBadge status={selectedSub.status} />
              </div>
              <div className="flex justify-between">
                <span>Start Date:</span>
                <span>{selectedSub.start_date.substring(0, 10)}</span>
              </div>
              <div className="flex justify-between">
                <span>Expiry Date:</span>
                <span>{selectedSub.expiry_date.substring(0, 10)}</span>
              </div>
              {selectedSub.next_invoice_date && (
                <div className="flex justify-between font-semibold">
                  <span>Next Scheduled Invoice:</span>
                  <span>{selectedSub.next_invoice_date.substring(0, 10)}</span>
                </div>
              )}
            </div>

            <div className="border border-slate-200 rounded-lg overflow-hidden">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-50 text-slate-500 uppercase font-semibold">
                  <tr>
                    <th className="p-2.5">Item</th>
                    <th className="p-2.5 text-center">Qty</th>
                    <th className="p-2.5 text-right">Price</th>
                    <th className="p-2.5 text-right">Total</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {selectedSub.lines.map((l, i) => (
                    <tr key={i}>
                      <td className="p-2.5 font-medium text-slate-800">
                        {l.product_name} {l.variant_label ? `(${l.variant_label})` : ''}
                      </td>
                      <td className="p-2.5 text-center">{l.quantity}</td>
                      <td className="p-2.5 text-right">${parseFloat(l.unit_price).toFixed(2)}</td>
                      <td className="p-2.5 text-right font-semibold">${parseFloat(l.amount).toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setSelectedSub(null)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold"
              >
                Close
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};
