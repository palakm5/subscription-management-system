import React, { useEffect, useState } from 'react';
import { apiRequest } from '../../api/client';
import { useToast } from '../../components/ToastContext';
import { Modal } from '../../components/Modal';
import { PasswordRulesChecklist } from '../../components/PasswordRulesChecklist';
import { StatusBadge } from '../../components/StatusBadge';
import {
  UserCheck,
  Plus,
  Mail,
  Shield,
  KeyRound,
  UserPlus
} from 'lucide-react';

interface StaffUser {
  id: string;
  email: string;
  role: string;
  is_active: boolean;
  customer_id?: string;
  created_at: string;
}

export const StaffManagement: React.FC = () => {
  const { addToast } = useToast();
  const [staffList, setStaffList] = useState<StaffUser[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const loadStaff = async () => {
    try {
      setLoading(true);
      const data = await apiRequest<StaffUser[]>('/admin/staff');
      setStaffList(data);
    } catch (err: any) {
      addToast(err.message || 'Failed to load staff list', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStaff();
  }, []);

  const handleCreateStaff = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      addToast('Passwords do not match', 'error');
      return;
    }
    try {
      const res = await apiRequest<StaffUser>('/admin/staff', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
      addToast(`Staff member ${res.email} created`, 'success');
      setEmail('');
      setPassword('');
      setConfirmPassword('');
      setIsModalOpen(false);
      loadStaff();
    } catch (err: any) {
      addToast(err.message || 'Failed to create staff member', 'error');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Staff Team</h1>
          <p className="text-sm text-slate-500 mt-1">
            Admin management of staff team credentials and internal role provisioning.
          </p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition shadow-xs"
        >
          <UserPlus className="w-4 h-4" />
          <span>New Staff Member</span>
        </button>
      </div>

      {/* Staff List Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/75 border-b border-slate-200 text-slate-500 text-xs font-semibold uppercase tracking-wider">
                <th className="py-3 px-4">Staff Email</th>
                <th className="py-3 px-4">Role</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Date Added</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {loading ? (
                <tr>
                  <td colSpan={4} className="py-8 text-center text-slate-400">
                    Loading staff directory...
                  </td>
                </tr>
              ) : staffList.length === 0 ? (
                <tr>
                  <td colSpan={4} className="py-8 text-center text-slate-400">
                    No staff members created yet.
                  </td>
                </tr>
              ) : (
                staffList.map((s) => (
                  <tr key={s.id} className="hover:bg-slate-50/50 transition-colors">
                    <td className="py-3 px-4 font-semibold text-slate-900 flex items-center gap-2">
                      <div className="w-7 h-7 rounded-full bg-slate-100 text-slate-600 flex items-center justify-center text-xs font-bold">
                        {s.email.substring(0, 2).toUpperCase()}
                      </div>
                      <span>{s.email}</span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold bg-blue-50 text-blue-700 uppercase">
                        <Shield className="w-3 h-3" />
                        {s.role}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={s.is_active ? 'active' : 'inactive'} />
                    </td>
                    <td className="py-3 px-4 text-xs text-slate-500">
                      {new Date(s.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Staff Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Create Staff Member"
      >
        <form onSubmit={handleCreateStaff} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Email Address *
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="staff@brightloop.io"
                className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-lg text-sm"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Initial Password *
            </label>
            <div className="relative">
              <KeyRound className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Strong staff password"
                className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-lg text-sm"
              />
            </div>
            <div className="mt-2">
              <PasswordRulesChecklist password={password} />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-xs font-semibold text-slate-700 uppercase">
                Confirm Password *
              </label>
              {confirmPassword && password === confirmPassword && (
                <span className="text-[11px] font-semibold text-emerald-600">✓ Passwords match</span>
              )}
              {confirmPassword && password !== confirmPassword && (
                <span className="text-[11px] font-semibold text-rose-500">✗ Passwords do not match</span>
              )}
            </div>
            <div className="relative">
              <KeyRound className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Re-enter password to confirm"
                className={`w-full pl-9 pr-3 py-2 border rounded-lg text-sm transition-colors ${
                  confirmPassword && password !== confirmPassword
                    ? 'border-rose-300 bg-rose-50/20'
                    : confirmPassword && password === confirmPassword
                    ? 'border-emerald-300 bg-emerald-50/20'
                    : 'border-slate-200'
                }`}
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
              Create Staff Account
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
