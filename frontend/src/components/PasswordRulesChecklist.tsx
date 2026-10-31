import React from 'react';
import { Check, X } from 'lucide-react';

interface Props {
  password: string;
}

export const PasswordRulesChecklist: React.FC<Props> = ({ password }) => {
  const rules = [
    { label: 'Minimum 9 characters (more than 8)', valid: password.length >= 9 },
    { label: 'At least one uppercase letter (A-Z)', valid: /[A-Z]/.test(password) },
    { label: 'At least one lowercase letter (a-z)', valid: /[a-z]/.test(password) },
    { label: 'At least one special character (!@#$%^&*...)', valid: /[^a-zA-Z0-9]/.test(password) },
  ];

  return (
    <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 my-2 text-xs">
      <div className="font-medium text-slate-700 mb-2">Password Requirements:</div>
      <div className="space-y-1.5">
        {rules.map((r, i) => (
          <div key={i} className="flex items-center gap-2">
            {r.valid ? (
              <span className="flex items-center justify-center w-4 h-4 rounded-full bg-emerald-100 text-emerald-700">
                <Check className="w-2.5 h-2.5" />
              </span>
            ) : (
              <span className="flex items-center justify-center w-4 h-4 rounded-full bg-slate-200 text-slate-400">
                <X className="w-2.5 h-2.5" />
              </span>
            )}
            <span className={r.valid ? 'text-emerald-700 font-medium' : 'text-slate-500'}>
              {r.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};
