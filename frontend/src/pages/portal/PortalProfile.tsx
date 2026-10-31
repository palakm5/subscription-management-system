import React, { useEffect, useState } from 'react';
import { apiRequest } from '../../api/client';
import { useToast } from '../../components/ToastContext';
import {
  User,
  Building,
  Phone,
  Receipt,
  MapPin,
  Save
} from 'lucide-react';
import { LocationSelector } from '../../components/LocationSelector';

interface BillingAddress {
  line1?: string;
  city?: string;
  state?: string;
  zip?: string;
  country?: string;
}

interface CustomerProfile {
  id: string;
  name: string;
  company?: string;
  phone?: string;
  tax_id?: string;
  billing_address: BillingAddress;
}

export const PortalProfile: React.FC = () => {
  const { addToast } = useToast();
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [profile, setProfile] = useState<CustomerProfile | null>(null);

  const loadProfile = async () => {
    try {
      setLoading(true);
      const data = await apiRequest<CustomerProfile>('/portal/profile');
      setProfile(data);
    } catch (err: any) {
      addToast(err.message || 'Failed to load profile', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProfile();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!profile) return;
    try {
      setSaving(true);
      const updated = await apiRequest<CustomerProfile>('/portal/profile', {
        method: 'PUT',
        body: JSON.stringify({
          name: profile.name,
          company: profile.company || null,
          phone: profile.phone || null,
          tax_id: profile.tax_id || null,
          billing_address: profile.billing_address || {},
        }),
      });
      setProfile(updated);
      addToast('Profile updated successfully', 'success');
    } catch (err: any) {
      addToast(err.message || 'Failed to update profile', 'error');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-slate-400">Loading your profile...</div>;
  }

  if (!profile) {
    return <div className="p-8 text-center text-slate-400">Profile could not be loaded.</div>;
  }

  return (
    <div className="max-w-3xl space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Account Profile</h1>
        <p className="text-sm text-slate-500 mt-1">
          Manage your organization details and primary billing address for automatic invoice snapshots.
        </p>
      </div>

      <form onSubmit={handleSave} className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-6">
        {/* Contact info */}
        <div>
          <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-4 flex items-center gap-2">
            <User className="w-4 h-4 text-blue-600" />
            <span>Primary Contact</span>
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Full Name *
              </label>
              <input
                type="text"
                required
                value={profile.name}
                onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Company Name
              </label>
              <input
                type="text"
                value={profile.company || ''}
                onChange={(e) => setProfile({ ...profile, company: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Phone Number
              </label>
              <input
                type="text"
                value={profile.phone || ''}
                onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Tax Identification Number
              </label>
              <input
                type="text"
                placeholder="e.g. VAT/EIN #US-987654321"
                value={profile.tax_id || ''}
                onChange={(e) => setProfile({ ...profile, tax_id: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
              />
            </div>
          </div>
        </div>

        {/* Billing Address */}
        <div className="border-t border-slate-100 pt-6">
          <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-4 flex items-center gap-2">
            <MapPin className="w-4 h-4 text-blue-600" />
            <span>Billing Address</span>
          </h3>

          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Address Line 1
              </label>
              <input
                type="text"
                value={profile.billing_address?.line1 || ''}
                onChange={(e) =>
                  setProfile({
                    ...profile,
                    billing_address: { ...profile.billing_address, line1: e.target.value },
                  })
                }
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                placeholder="Street address or P.O. Box"
              />
            </div>

            <LocationSelector
              country={profile.billing_address?.country || 'United States'}
              state={profile.billing_address?.state || ''}
              city={profile.billing_address?.city || ''}
              onCountryChange={(val) =>
                setProfile({
                  ...profile,
                  billing_address: { ...profile.billing_address, country: val },
                })
              }
              onStateChange={(val) =>
                setProfile({
                  ...profile,
                  billing_address: { ...profile.billing_address, state: val },
                })
              }
              onCityChange={(val) =>
                setProfile({
                  ...profile,
                  billing_address: { ...profile.billing_address, city: val },
                })
              }
              layout="grid"
            />

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Zip / Postal Code
              </label>
              <input
                type="text"
                value={profile.billing_address?.zip || ''}
                onChange={(e) =>
                  setProfile({
                    ...profile,
                    billing_address: { ...profile.billing_address, zip: e.target.value },
                  })
                }
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                placeholder="e.g. 78701"
              />
            </div>
          </div>
        </div>

        <div className="flex justify-end pt-4 border-t border-slate-100">
          <button
            type="submit"
            disabled={saving}
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-semibold transition shadow-xs disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            <span>{saving ? 'Saving...' : 'Save Profile Changes'}</span>
          </button>
        </div>
      </form>
    </div>
  );
};
