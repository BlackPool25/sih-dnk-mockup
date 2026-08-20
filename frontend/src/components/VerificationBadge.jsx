import { useEffect, useState } from "react";
import { Shield, AlertTriangle, CheckCircle } from "lucide-react";
import { fetchSellerProfile } from "../services/api";
import { useHindi } from "../context/HindiContext";

const LEVEL_CONFIG = {
  L0: { score: 25, label: "L0", cls: "bg-gray-100 text-gray-600 border-gray-200", desc: "Untrusted" },
  L1: { score: 50, label: "L1", cls: "bg-amber-100 text-amber-700 border-amber-200", desc: "PAN verified" },
  L2: { score: 85, label: "L2", cls: "bg-green-100 text-green-700 border-green-200", desc: "IEC+AD+bank+IFSC" },
  L3: { score: 95, label: "L3", cls: "bg-purple-100 text-purple-700 border-purple-200", desc: "Liveness verified" },
};

export function trustBadgeClass(level) {
  return LEVEL_CONFIG[level]?.cls || LEVEL_CONFIG.L0.cls;
}

export function levelScore(level) {
  return LEVEL_CONFIG[level]?.score ?? 25;
}

/**
 * VerificationBadge — reads GET /profile trust_level/payouts_frozen
 * Shows L0 25 → L2 85 pills + red payouts frozen chip.
 * Respects hindi_help via HindiContext (no auto-detect).
 * Compact mode for Header site-wide, full mode for Profile page.
 */
export default function VerificationBadge({ compact = false, className = "" }) {
  const { hindiHelp } = useHindi();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const p = await fetchSellerProfile();
        if (!cancelled) setProfile(p);
      } catch {
        if (!cancelled) setProfile(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  if (loading) {
    return (
      <span data-testid="verification-badge-loading" className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs border bg-gray-50 text-gray-400 ${className}`}>
        <Shield className="w-3.5 h-3.5 animate-pulse" /> Loading…
      </span>
    );
  }
  if (!profile) {
    // unauthenticated / non-seller — hide silently site-wide
    return null;
  }

  const level = profile.trust_level || "L0";
  const score = profile.trust_score ?? levelScore(level);
  const frozen = !!profile.payouts_frozen;
  const cfg = LEVEL_CONFIG[level] || LEVEL_CONFIG.L0;

  if (compact) {
    return (
      <span data-testid="verification-badge" className={`inline-flex items-center gap-1.5 ${className}`}>
        <span data-testid={`trust-pill-${level}`} className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium border ${cfg.cls}`}>
          <Shield className="w-3 h-3" />
          {level} · {score}
        </span>
        {frozen ? (
          <span data-testid="payouts-frozen-chip" className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-red-100 text-red-700 border border-red-200">
            <AlertTriangle className="w-3 h-3" />
            {hindiHelp ? "भुगतान रोका गया" : "Payouts frozen"}
          </span>
        ) : null}
      </span>
    );
  }

  return (
    <div data-testid="verification-badge" className={`flex flex-wrap items-center gap-2 ${className}`}>
      {Object.entries(LEVEL_CONFIG).map(([lvl, c]) => {
        const active = lvl === level;
        return (
          <span
            key={lvl}
            data-testid={`trust-pill-${lvl}`}
            className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium border ${active ? c.cls + " ring-2 ring-offset-1 ring-[#A8C3A0]" : "bg-white text-gray-400 border-gray-200 opacity-60"}`}
            title={`${lvl} — ${c.desc} — ${c.score}`}
          >
            <Shield className="w-3.5 h-3.5" />
            {lvl} {c.score}
          </span>
        );
      })}
      {frozen ? (
        <span data-testid="payouts-frozen-chip" className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium bg-red-100 text-red-700 border border-red-200">
          <AlertTriangle className="w-3.5 h-3.5" />
          {hindiHelp ? "भुगतान रोका गया" : "Payouts frozen"}
        </span>
      ) : (
        <span data-testid="payouts-active-chip" className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700 border border-green-200">
          <CheckCircle className="w-3.5 h-3.5" />
          {hindiHelp ? "भुगतान सक्रिय" : "Payouts active"}
        </span>
      )}
    </div>
  );
}
