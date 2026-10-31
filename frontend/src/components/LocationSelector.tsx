import React, { useEffect, useMemo, useState } from 'react';
import { COUNTRIES, type CountryOption, type StateOption } from '../data/locations';
import { Globe, MapPin, Building2 } from 'lucide-react';

interface LocationSelectorProps {
  country: string;
  state: string;
  city: string;
  onCountryChange: (val: string) => void;
  onStateChange: (val: string) => void;
  onCityChange: (val: string) => void;
  layout?: 'grid' | 'stacked';
  required?: boolean;
}

export const LocationSelector: React.FC<LocationSelectorProps> = ({
  country,
  state,
  city,
  onCountryChange,
  onStateChange,
  onCityChange,
  layout = 'grid',
  required = false,
}) => {
  // Find matching country
  const currentCountryObj = useMemo<CountryOption | undefined>(() => {
    if (!country) return COUNTRIES[0];
    const normalized = country.toLowerCase().trim();
    return COUNTRIES.find(
      (c) =>
        c.name.toLowerCase() === normalized ||
        c.code.toLowerCase() === normalized
    );
  }, [country]);

  // If country is not in the list and not empty
  const isCustomCountry = !currentCountryObj && Boolean(country);

  // States list for current country
  const statesList = useMemo<StateOption[]>(() => {
    return currentCountryObj?.states || [];
  }, [currentCountryObj]);

  // Find matching state
  const currentStateObj = useMemo<StateOption | undefined>(() => {
    if (!state || !currentCountryObj) return undefined;
    const normalized = state.toLowerCase().trim();
    return statesList.find(
      (s) =>
        s.name.toLowerCase() === normalized ||
        (s.code && s.code.toLowerCase() === normalized)
    );
  }, [state, currentCountryObj, statesList]);

  // Is custom state?
  const [customStateMode, setCustomStateMode] = useState<boolean>(false);
  const [customCityMode, setCustomCityMode] = useState<boolean>(false);

  useEffect(() => {
    if (state && !currentStateObj && statesList.length > 0) {
      setCustomStateMode(true);
    } else {
      setCustomStateMode(false);
    }
  }, [state, currentStateObj, statesList]);

  // Cities list for current state
  const citiesList = useMemo<string[]>(() => {
    return currentStateObj?.cities || [];
  }, [currentStateObj]);

  useEffect(() => {
    if (city && citiesList.length > 0 && !citiesList.includes(city)) {
      setCustomCityMode(true);
    } else {
      setCustomCityMode(false);
    }
  }, [city, citiesList]);

  // Handlers
  const handleCountrySelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    if (val === '__custom__') {
      onCountryChange('Other');
      onStateChange('');
      onCityChange('');
      setCustomStateMode(true);
      setCustomCityMode(true);
      return;
    }

    const found = COUNTRIES.find((c) => c.code === val);
    if (found) {
      onCountryChange(found.name);
      // Default to first state and first city
      if (found.states.length > 0) {
        const firstState = found.states[0];
        onStateChange(firstState.name);
        if (firstState.cities.length > 0) {
          onCityChange(firstState.cities[0]);
        } else {
          onCityChange('');
        }
      } else {
        onStateChange('');
        onCityChange('');
      }
      setCustomStateMode(false);
      setCustomCityMode(false);
    }
  };

  const handleStateSelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    if (val === '__other__') {
      setCustomStateMode(true);
      onStateChange('');
      onCityChange('');
      setCustomCityMode(true);
      return;
    }

    setCustomStateMode(false);
    const foundState = statesList.find((s) => s.name === val || s.code === val);
    if (foundState) {
      onStateChange(foundState.name);
      if (foundState.cities.length > 0) {
        onCityChange(foundState.cities[0]);
        setCustomCityMode(false);
      } else {
        onCityChange('');
      }
    } else {
      onStateChange(val);
    }
  };

  const handleCitySelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    if (val === '__other__') {
      setCustomCityMode(true);
      onCityChange('');
      return;
    }
    setCustomCityMode(false);
    onCityChange(val);
  };

  return (
    <div className={layout === 'grid' ? 'grid grid-cols-1 sm:grid-cols-3 gap-3' : 'space-y-3'}>
      {/* Country / Region */}
      <div>
        <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1 flex items-center gap-1.5">
          <Globe className="w-3.5 h-3.5 text-blue-600" />
          <span>Country / Region {required && '*'}</span>
        </label>
        <select
          value={currentCountryObj ? currentCountryObj.code : '__custom__'}
          onChange={handleCountrySelect}
          className="block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 shadow-2xs cursor-pointer"
        >
          {COUNTRIES.map((c) => (
            <option key={c.code} value={c.code}>
              {c.name}
            </option>
          ))}
          <option value="__custom__">Other (Enter manually)</option>
        </select>
        {isCustomCountry && (
          <input
            type="text"
            value={country}
            onChange={(e) => onCountryChange(e.target.value)}
            placeholder="Type country name..."
            className="mt-1.5 block w-full rounded-lg border border-slate-300 px-3 py-1.5 text-xs text-slate-900 focus:border-blue-500 focus:outline-none"
          />
        )}
      </div>

      {/* State / Province */}
      <div>
        <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1 flex items-center gap-1.5">
          <MapPin className="w-3.5 h-3.5 text-blue-600" />
          <span>State / Region {required && '*'}</span>
        </label>
        {statesList.length > 0 && !isCustomCountry ? (
          <div>
            <select
              value={customStateMode ? '__other__' : currentStateObj ? currentStateObj.name : ''}
              onChange={handleStateSelect}
              className="block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 shadow-2xs cursor-pointer"
            >
              <option value="" disabled>
                Select state / region...
              </option>
              {statesList.map((s) => (
                <option key={s.name} value={s.name}>
                  {s.name} {s.code ? `(${s.code})` : ''}
                </option>
              ))}
              <option value="__other__">Other / Not Listed</option>
            </select>
            {customStateMode && (
              <input
                type="text"
                value={state}
                onChange={(e) => onStateChange(e.target.value)}
                placeholder="Type your state / region..."
                className="mt-1.5 block w-full rounded-lg border border-slate-300 px-3 py-1.5 text-xs text-slate-900 focus:border-blue-500 focus:outline-none"
              />
            )}
          </div>
        ) : (
          <input
            type="text"
            value={state}
            onChange={(e) => onStateChange(e.target.value)}
            placeholder="State / Region"
            className="block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        )}
      </div>

      {/* City */}
      <div>
        <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1 flex items-center gap-1.5">
          <Building2 className="w-3.5 h-3.5 text-blue-600" />
          <span>City {required && '*'}</span>
        </label>
        {citiesList.length > 0 && !customStateMode && !isCustomCountry ? (
          <div>
            <select
              value={customCityMode ? '__other__' : city}
              onChange={handleCitySelect}
              className="block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 shadow-2xs cursor-pointer"
            >
              <option value="" disabled>
                Select city...
              </option>
              {citiesList.map((ct) => (
                <option key={ct} value={ct}>
                  {ct}
                </option>
              ))}
              <option value="__other__">Other / Custom City</option>
            </select>
            {customCityMode && (
              <input
                type="text"
                value={city}
                onChange={(e) => onCityChange(e.target.value)}
                placeholder="Type your city name..."
                className="mt-1.5 block w-full rounded-lg border border-slate-300 px-3 py-1.5 text-xs text-slate-900 focus:border-blue-500 focus:outline-none"
              />
            )}
          </div>
        ) : (
          <input
            type="text"
            value={city}
            onChange={(e) => onCityChange(e.target.value)}
            placeholder="City"
            className="block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        )}
      </div>
    </div>
  );
};
