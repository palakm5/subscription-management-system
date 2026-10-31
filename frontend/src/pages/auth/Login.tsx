import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../auth/AuthContext';
import { useToast } from '../../components/ToastContext';
import { Eye, EyeOff, Shield, Users, User, CheckCircle2 } from 'lucide-react';

export const Login: React.FC = () => {
  const { login } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [activePreset, setActivePreset] = useState<'admin' | 'staff' | 'customer' | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const u = await login(email, password);
      toast('success', `Welcome back, ${u.email}!`);
      if (u.role === 'customer') {
        navigate('/portal/subscriptions');
      } else {
        navigate('/');
      }
    } catch (err: any) {
      toast('error', err.message || 'Login failed. Please check your credentials.');
    } finally {
      setSubmitting(false);
    }
  };

  const setDemoCredentials = (role: 'admin' | 'staff' | 'customer') => {
    setActivePreset(role);
    if (role === 'admin') {
      setEmail('admin@brightloop.com');
      setPassword('AdminSecure1!');
      toast('info', 'Loaded Admin credentials: admin@brightloop.com');
    } else if (role === 'staff') {
      setEmail('staff@brightloop.com');
      setPassword('StaffSecure1!');
      toast('info', 'Loaded Staff credentials: staff@brightloop.com');
    } else {
      setEmail('customer@brightloop.com');
      setPassword('CustomerSecure1!');
      toast('info', 'Loaded Customer credentials: customer@brightloop.com');
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
          Sign in to Brightloop
        </h2>
        <p className="mt-1 text-center text-xs text-slate-500">
          Enterprise Subscription & Recurring Billing Management
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-6 shadow-sm border border-slate-200 rounded-xl sm:px-10">
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
                Email address
              </label>
              <div className="mt-1">
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    setActivePreset(null);
                  }}
                  className="block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="name@company.com"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between">
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Password
                </label>
                <Link
                  to="/forgot-password"
                  className="text-xs font-medium text-blue-600 hover:text-blue-700"
                >
                  Forgot password?
                </Link>
              </div>
              <div className="mt-1 relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    setActivePreset(null);
                  }}
                  className="block w-full rounded-lg border border-slate-300 pl-3 pr-10 py-2 text-sm text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="•••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-1"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-lg shadow-xs text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition-colors cursor-pointer"
            >
              {submitting ? 'Authenticating...' : 'Sign In'}
            </button>
          </form>

          {/* Quick Demo Credentials */}
          <div className="mt-6 pt-5 border-t border-slate-100">
            <span className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-2 text-center">
              One-Click Demo Credentials
            </span>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => setDemoCredentials('admin')}
                className={`py-2 px-2 border rounded-lg text-xs font-medium transition-all flex flex-col items-center gap-1 cursor-pointer ${
                  activePreset === 'admin'
                    ? 'bg-blue-50 border-blue-400 text-blue-700 shadow-2xs font-semibold'
                    : 'bg-slate-50 hover:bg-slate-100 border-slate-200 text-slate-700'
                }`}
              >
                <Shield className="w-3.5 h-3.5 text-blue-600" />
                <span>Admin</span>
              </button>
              <button
                type="button"
                onClick={() => setDemoCredentials('staff')}
                className={`py-2 px-2 border rounded-lg text-xs font-medium transition-all flex flex-col items-center gap-1 cursor-pointer ${
                  activePreset === 'staff'
                    ? 'bg-indigo-50 border-indigo-400 text-indigo-700 shadow-2xs font-semibold'
                    : 'bg-slate-50 hover:bg-slate-100 border-slate-200 text-slate-700'
                }`}
              >
                <Users className="w-3.5 h-3.5 text-indigo-600" />
                <span>Staff</span>
              </button>
              <button
                type="button"
                onClick={() => setDemoCredentials('customer')}
                className={`py-2 px-2 border rounded-lg text-xs font-medium transition-all flex flex-col items-center gap-1 cursor-pointer ${
                  activePreset === 'customer'
                    ? 'bg-emerald-50 border-emerald-400 text-emerald-700 shadow-2xs font-semibold'
                    : 'bg-slate-50 hover:bg-slate-100 border-slate-200 text-slate-700'
                }`}
              >
                <User className="w-3.5 h-3.5 text-emerald-600" />
                <span>Customer</span>
              </button>
            </div>

            {/* Quick credentials cheatsheet */}
            <div className="mt-3 p-2.5 bg-slate-50 rounded-lg border border-slate-100 text-[11px] text-slate-600 space-y-1">
              <div className="flex justify-between items-center">
                <span className="font-semibold text-slate-700">Admin:</span>
                <span className="font-mono text-slate-500">admin@brightloop.com / AdminSecure1!</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="font-semibold text-slate-700">Staff:</span>
                <span className="font-mono text-slate-500">staff@brightloop.com / StaffSecure1!</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="font-semibold text-slate-700">Customer:</span>
                <span className="font-mono text-slate-500">customer@brightloop.com / CustomerSecure1!</span>
              </div>
            </div>
          </div>

          <div className="mt-6 text-center">
            <span className="text-xs text-slate-500">
              Need a new customer account?{' '}
              <Link to="/signup" className="font-semibold text-blue-600 hover:text-blue-700">
                Sign up
              </Link>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
