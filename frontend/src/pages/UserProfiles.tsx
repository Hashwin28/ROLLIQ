import React, { useState } from 'react';
import { useAppStore } from '../store/appStore';
import { api } from '../api/endpoints';
import { User } from '../types';
import {
  Users,
  UserPlus,
  Check,
  ShieldCheck,
  Trash2,
  Calendar,
  Layers,
} from 'lucide-react';

export const UserProfiles: React.FC = () => {
  const { users, currentUser, dispatch, refreshUsers } = useAppStore();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [nameInput, setNameInput] = useState('');
  const [ageGroupInput, setAgeGroupInput] = useState<'child' | 'adult' | 'elderly'>('adult');
  const [submitting, setSubmitting] = useState(false);

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nameInput.trim()) return;

    setSubmitting(true);
    try {
      const newUser = await api.createUser({
        display_name: nameInput.trim(),
        age_group: ageGroupInput,
      });
      await refreshUsers();
      dispatch({ type: 'SET_CURRENT_USER', payload: newUser });
      setNameInput('');
      setIsModalOpen(false);
    } catch (_) {
      // ignore
    } finally {
      setSubmitting(false);
    }
  };

  const handleSelectUser = (u: User) => {
    dispatch({ type: 'SET_CURRENT_USER', payload: u });
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[#1f293d]">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">
            User Profiles & Cohort Management
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Isolated mobility profiles, personal baseline histories, and subject cohorts
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 transition-colors flex items-center gap-2 shadow-sm"
        >
          <UserPlus className="w-3.5 h-3.5" />
          <span>New Subject Profile</span>
        </button>
      </div>

      {/* User Profiles Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {users.map((u) => {
          const isSelected = u.id === currentUser?.id;
          return (
            <div
              key={u.id}
              onClick={() => handleSelectUser(u)}
              className={`p-5 rounded-2xl border transition-all cursor-pointer relative flex flex-col justify-between ${
                isSelected
                  ? 'bg-[#151f33] border-sky-500/60 shadow-lg shadow-sky-500/10'
                  : 'bg-[#121826] border-[#20293d] hover:border-slate-600'
              }`}
            >
              <div>
                <div className="flex items-start justify-between">
                  <div className="w-11 h-11 rounded-xl bg-sky-500/20 text-sky-400 border border-sky-500/40 flex items-center justify-center font-bold text-base">
                    {u.display_name.charAt(0)}
                  </div>

                  {isSelected && (
                    <span className="flex items-center gap-1 text-[11px] font-semibold text-sky-400 bg-sky-500/15 border border-sky-500/30 px-2.5 py-0.5 rounded-full">
                      <Check className="w-3 h-3" /> Active Subject
                    </span>
                  )}
                </div>

                <div className="mt-3">
                  <h3 className="text-sm font-bold text-white">{u.display_name}</h3>
                  <p className="text-xs text-slate-400 capitalize mt-0.5">
                    Age Group: <strong className="text-slate-300">{u.age_group || 'adult'}</strong>
                  </p>
                  <p className="text-[10px] text-slate-500 font-mono mt-1">ID: {u.id}</p>
                </div>
              </div>

              <div className="mt-5 pt-3 border-t border-[#1c263b] flex items-center justify-between text-xs text-slate-400">
                <span className="flex items-center gap-1 font-mono text-[11px]">
                  <Calendar className="w-3.5 h-3.5 text-slate-500" />
                  {new Date(u.created_at).toLocaleDateString()}
                </span>
                <span className="text-sky-400 text-xs font-semibold hover:underline">
                  {isSelected ? 'Currently Monitored' : 'Switch to Profile →'}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Create User Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#141b2a] border border-[#232f48] rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div>
              <h3 className="text-base font-bold text-white">Create Subject Profile</h3>
              <p className="text-xs text-slate-400 mt-1">
                Add an individual subject for personalized bed-mobility baseline tracking.
              </p>
            </div>

            <form onSubmit={handleCreateUser} className="space-y-4">
              <div>
                <label className="text-xs font-medium text-slate-300 block mb-1">
                  Full Name / Subject ID
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. John Doe / Subject #204"
                  value={nameInput}
                  onChange={(e) => setNameInput(e.target.value)}
                  className="w-full bg-[#0d121c] border border-[#232f48] rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-sky-400"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-slate-300 block mb-1">
                  Age Cohort
                </label>
                <select
                  value={ageGroupInput}
                  onChange={(e) => setAgeGroupInput(e.target.value as any)}
                  className="w-full bg-[#0d121c] border border-[#232f48] rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-sky-400"
                >
                  <option value="adult">Adult (18–64)</option>
                  <option value="elderly">Elderly (65+)</option>
                  <option value="child">Pediatric (&lt;18)</option>
                </select>
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 text-xs font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 text-xs font-bold rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 transition-colors"
                >
                  {submitting ? 'Creating...' : 'Save Profile'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
