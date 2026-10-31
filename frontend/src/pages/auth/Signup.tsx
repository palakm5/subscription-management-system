import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../auth/AuthContext';
import { useToast } from '../../components/ToastContext';
import { PasswordRulesChecklist } from '../../components/PasswordRulesChecklist';
import { LocationSelector } from '../../components/LocationSelector';
import { Check, X, ShieldCheck } from 'lucide-react';

export const Signup: React.FC = () => {
  const { signup } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [name, setName] = useState('');
  const [company, setCompany] = useState('');
  const [phone, setPhone] = useState('');
  const [line1, setLine1] = useState('');
  const [country, setCountry] = useState('United States');
  const [state, setState] = useState('California');
  const [city, setCity] = useState('San Francisco');
  const [zip, setZip] = useState('');
  const [taxId, setTaxId] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Validation logic
  const isPasswordValid =
    password.length >= 9 &&
    /[A-Z]/.test(password) &&
    /[a-z]/.test(password) &&
    /[^a-zA-Z0-9]/.test(password);

  const passwordsMatch = confirmPassword.length > 0 && password === confirmPassword;
  const passwordsMismatch = confirmPassword.length > 0 && password !== confirmPassword;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!isPasswordValid) {
      toast('error', 'Please make sure your password meets all 4 requirements.');
      return;
    }

    if (password !== confirmPassword) {
      toast('error', 'Passwords do not match. Please ensure both passwords are identical.');
      return;
    }

    setSubmitting(true);
    try {
      await signup({
        email,
        password,
        confirm_password: confirmPassword,
        name,
        company,
        phone,
        billing_address: {
          line1,
          city,
          state,
          zip,
          country,
        },
        tax_id: taxId,
      });
      toast('success', 'Account created successfully! Welcome to your customer portal.');
      navigate('/portal/subscriptions');
    } catch (err: any) {
      toast('error', err.message || 'Registration failed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white font-bold text-xl shadow-xs">
            B
          </div>
        </div>
        <h2 className="mt-4 text-center text-2xl font-bold tracking-tight text-slate-900">
          Create Customer Account
        </h2>
        <p className="mt-1 text-center text-xs text-slate-500">
          Sign up to manage your Brightloop subscriptions and invoices
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-xl">
        <div className="bg-white py-8 px-6 shadow-sm border border-slate-200 rounded-xl sm:px-10">
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Contact Name *
                </label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="Jane Doe"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Company Name
                </label>
                <input
                  type="text"
                  value={company}
                  onChange={(e) => setCompany(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="Acme Corp"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Email Address *
                </label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="jane@company.com"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Phone Number
                </label>
                <input
                  type="text"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="+1 (555) 000-0000"
                />
              </div>
            </div>

            {/* Password Section */}
            <div className="space-y-3 pt-1">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Password *
                </label>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="•••••••••"
                />
                {/* Live interactive rule validator */}
                <PasswordRulesChecklist password={password} />
              </div>

              {/* Confirm Password Field */}
              <div>
                <div className="flex items-center justify-between">
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
                    Confirm Password *
                  </label>
                  {passwordsMatch && (
                    <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-600">
                      <Check className="w-3.5 h-3.5" />
                      <span>Passwords match</span>
                    </span>
                  )}
                  {passwordsMismatch && (
                    <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-rose-500">
                      <X className="w-3.5 h-3.5" />
                      <span>Passwords do not match</span>
                    </span>
                  )}
                </div>
                <div className="relative mt-1">
                  <input
                    type="password"
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className={`block w-full rounded-lg border px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-1 transition-colors ${
                      passwordsMismatch
                        ? 'border-rose-400 focus:border-rose-500 focus:ring-rose-500 bg-rose-50/20'
                        : passwordsMatch
                        ? 'border-emerald-500 focus:border-emerald-500 focus:ring-emerald-500 bg-emerald-50/20'
                        : 'border-slate-300 focus:border-blue-500 focus:ring-blue-500'
                    }`}
                    placeholder="Re-enter your password"
                  />
                  {passwordsMatch && (
                    <span className="absolute right-3 top-1/2 -translate-y-1/2 text-emerald-600">
                      <ShieldCheck className="w-4 h-4" />
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Billing Address with Region, State, and City Dropdowns */}
            <div className="pt-3 border-t border-slate-100">
              <span className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                Billing Address
              </span>
              <div className="space-y-3">
                <input
                  type="text"
                  value={line1}
                  onChange={(e) => setLine1(e.target.value)}
                  className="block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="Street Address (Line 1)"
                />

                {/* Dropdowns for Country/Region, State, and City */}
                <LocationSelector
                  country={country}
                  state={state}
                  city={city}
                  onCountryChange={setCountry}
                  onStateChange={setState}
                  onCityChange={setCity}
                  layout="grid"
                />

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                      ZIP / Postal Code
                    </label>
                    <input
                      type="text"
                      value={zip}
                      onChange={(e) => setZip(e.target.value)}
                      className="block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                      placeholder="e.g. 94103"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                      Tax ID / VAT (Optional)
                    </label>
                    <input
                      type="text"
                      value={taxId}
                      onChange={(e) => setTaxId(e.target.value)}
                      className="block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono text-xs"
                      placeholder="e.g. US-TAX-987"
                    />
                  </div>
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={submitting || (confirmPassword.length > 0 && !passwordsMatch)}
              className="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-lg shadow-xs text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition-colors cursor-pointer mt-4"
            >
              {submitting ? 'Creating account...' : 'Complete Registration'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <span className="text-xs text-slate-500">
              Already have an account?{' '}
              <Link to="/login" className="font-semibold text-blue-600 hover:text-blue-700">
                Sign in
              </Link>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
