"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { api, ApiError } from "@/lib/api-client";
import type { Profile, Skill, SkillLevel } from "@/types";

const LEVELS: SkillLevel[] = ["beginner", "intermediate", "advanced"];

export default function ProfilePage() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [bio, setBio] = useState("");
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [language, setLanguage] = useState("");
  const [level, setLevel] = useState<SkillLevel>("beginner");
  const [score, setScore] = useState(50);

  useEffect(() => {
    api
      .getProfile()
      .then((p) => {
        setProfile(p);
        setBio(p.bio ?? "");
      })
      .catch(() => undefined);
    api.listSkills().then(setSkills).catch(() => undefined);
  }, []);

  async function saveBio() {
    setError(null);
    try {
      const updated = await api.updateProfile({ bio });
      setProfile(updated);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Save failed");
    }
  }

  async function addSkill(e: React.FormEvent) {
    e.preventDefault();
    if (!language.trim()) return;
    try {
      const skill = await api.upsertSkill({ language: language.trim(), level, score });
      setSkills((prev) => {
        const others = prev.filter((s) => s.language !== skill.language);
        return [...others, skill];
      });
      setLanguage("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save skill");
    }
  }

  return (
    <div>
      <PageHeader title="Profile" subtitle="Your account and skill tracking" />
      <div className="grid gap-6 p-6 lg:grid-cols-2">
        <div className="card">
          <h3 className="font-semibold">Account</h3>
          {profile ? (
            <div className="mt-4 space-y-3">
              <div className="flex items-center gap-3">
                {profile.avatar_url && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={profile.avatar_url}
                    alt="avatar"
                    className="h-12 w-12 rounded-full"
                  />
                )}
                <div>
                  <p className="font-medium">
                    {profile.github_username ?? "GitHub user"}
                  </p>
                  <p className="text-xs text-slate-500">{profile.id}</p>
                </div>
              </div>
              <label className="block text-sm text-slate-400">Bio</label>
              <textarea
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                rows={3}
                className="input resize-none"
                placeholder="Tell us about your interests..."
              />
              <button onClick={saveBio} className="btn-primary">
                {saved ? "Saved!" : "Save bio"}
              </button>
            </div>
          ) : (
            <p className="mt-3 text-sm text-slate-500">Loading...</p>
          )}
          {error && <p className="mt-3 text-sm text-red-300">{error}</p>}
        </div>

        <div className="card">
          <h3 className="font-semibold">Skills</h3>
          <form onSubmit={addSkill} className="mt-4 space-y-2">
            <input
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              placeholder="Language or technology (e.g. Python)"
              className="input"
            />
            <div className="flex gap-2">
              <select
                value={level}
                onChange={(e) => setLevel(e.target.value as SkillLevel)}
                className="input"
              >
                {LEVELS.map((l) => (
                  <option key={l} value={l}>
                    {l}
                  </option>
                ))}
              </select>
              <input
                type="number"
                min={0}
                max={100}
                value={score}
                onChange={(e) => setScore(Number(e.target.value))}
                className="input w-24"
              />
              <button className="btn-primary">Add</button>
            </div>
          </form>

          <div className="mt-4 space-y-2">
            {skills.length === 0 && (
              <p className="text-sm text-slate-500">No skills tracked yet.</p>
            )}
            {skills.map((s) => (
              <div key={s.id} className="rounded-lg bg-surface-muted p-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium text-slate-100">{s.language}</span>
                  <span className="text-slate-400">{s.level}</span>
                </div>
                <div className="mt-2 h-2 overflow-hidden rounded-full bg-surface">
                  <div
                    className="h-full bg-brand-500"
                    style={{ width: `${s.score}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
