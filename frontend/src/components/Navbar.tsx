import React, { useState } from 'react';
import { LogOut, Play, RefreshCw, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../auth/AuthContext';
import { apiRequest } from '../api/client';
import { useToast } from './ToastContext';
import { Modal } from './Modal';

export const Navbar: React.FC = () => {
  const { user, isAdmin, logout } = useAuth();
  const { toast } = useToast();
  const [runningBilling, setRunningBilling] = useState(false);
  const [billingResult, setBillingResult] = useState<any>(null);

  const handleRunBilling = async () => {
    setRunningBilling(true);
    try {
      const res = await apiRequest('/billing/run', { method: 'POST' });
      setBillingResult(res);
      toast(
        'success',
        `Billing run complete: ${res.created} invoices created, ${res.skipped_duplicates} duplicate periods skipped.`
      );
    } catch (err: any) {
      toast('error', err.message || 'Billing run failed');
    } finally {
      setRunningBilling(false);
    }
  };

  return (
    <>
      <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-xs font-medium text-slate-500">Workspace</span>
          <span className="text-slate-300">/</span>
          <span className="text-xs font-semibold text-slate-800">
            {isAdmin ? 'System Administrator' : user?.role === 'staff' ? 'Staff Operations' : 'Self-Service Portal'}
          </span>
        </div>

        <div className="flex items-center gap-3">
          {isAdmin && (
            <button
              onClick={handleRunBilling}
              disabled={runningBilling}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white shadow-xs transition-colors cursor-pointer disabled:opacity-50"
            >
              {runningBilling ? (
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Play className="w-3.5 h-3.5 fill-current" />
              )}
              <span>{runningBilling ? 'Processing...' : 'Run Billing Now'}</span>
            </button>
          )}

          <button
            onClick={logout}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Sign out</span>
          </button>
        </div>
      </header>

      {/* Billing Result Modal */}
      <Modal
        isOpen={billingResult !== null}
        onClose={() => setBillingResult(null)}
        title="Billing Run Outcome"
      >
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-emerald-700 font-semibold text-sm">
            <CheckCircle2 className="w-5 h-5" />
            <span>Recurring billing cycle executed successfully</span>
          </div>

          <div className="grid grid-cols-3 gap-3 text-center">
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
              <span className="block text-2xl font-bold text-slate-900">{billingResult?.processed}</span>
              <span className="text-xs text-slate-500">Processed</span>
            </div>
            <div className="bg-emerald-50 p-3 rounded-lg border border-emerald-200">
              <span className="block text-2xl font-bold text-emerald-700">{billingResult?.created}</span>
              <span className="text-xs text-emerald-600">Invoices Created</span>
            </div>
            <div className="bg-amber-50 p-3 rounded-lg border border-amber-200">
              <span className="block text-2xl font-bold text-amber-700">{billingResult?.skipped_duplicates}</span>
              <span className="text-xs text-amber-600">Duplicates Blocked</span>
            </div>
          </div>

          {billingResult?.details && billingResult.details.length > 0 && (
            <div className="bg-slate-50 rounded-lg p-3 text-xs text-slate-600 max-h-48 overflow-y-auto space-y-1">
              <div className="font-semibold text-slate-700 mb-1">Details:</div>
              {billingResult.details.map((d: string, idx: number) => (
                <div key={idx} className="font-mono text-[11px]">{d}</div>
              ))}
            </div>
          )}

          <div className="flex justify-end pt-2">
            <button
              onClick={() => {
                setBillingResult(null);
                window.location.reload();
              }}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs"
            >
              Done & Refresh
            </button>
          </div>
        </div>
      </Modal>
    </>
  );
};
