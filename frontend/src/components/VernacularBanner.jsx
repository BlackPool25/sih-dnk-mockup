import { AlertTriangle } from "lucide-react";
import { useHindi } from "../context/HindiContext";

const VERNACULAR_HI = "यह खाता आपके IEC से लिंक AD Code के खाते से मेल नहीं खाता — इससे आपकी e-BRC नहीं बनेगी";
const VERNACULAR_EN = "This account does not match the AD Code account linked to your IEC — your e-BRC will not be generated";

/**
 * VernacularBanner — for 422 payouts_frozen responses.
 * Props:
 *  - detail: the 422 detail object { vernacular, message, side_by_side, payouts_frozen }
 *  - sideBySide: optional override { current_ad, proposed_ad, current_ifsc, proposed_ifsc, current_bank, proposed_bank }
 * Respects hindi_help via HindiContext (no auto-detect, no browser language sniffing).
 * Shows Hindi यह खाता... + side-by-side table current vs proposed AD/IFSC/bank.
 */
export default function VernacularBanner({ detail, sideBySide, onConfirm, className = "" }) {
  const { hindiHelp } = useHindi();
  const sbs = sideBySide || detail?.side_by_side || detail?.sideBySide || null;
  const vernacular = detail?.vernacular || detail?.message || VERNACULAR_HI;
  // Always ensure Hindi string present for proof; use explicit VERNACULAR_HI if detail missing
  const hiText = typeof vernacular === "string" && vernacular.includes("यह खाता") ? vernacular : VERNACULAR_HI;

  if (!detail && !sbs) return null;

  const currentAD = sbs?.current_ad ?? sbs?.currentAD ?? "—";
  const proposedAD = sbs?.proposed_ad ?? sbs?.proposedAD ?? "—";
  const currentIFSC = sbs?.current_ifsc ?? sbs?.currentIFSC ?? "—";
  const proposedIFSC = sbs?.proposed_ifsc ?? sbs?.proposedIFSC ?? "—";
  const currentBank = sbs?.current_bank ?? (currentIFSC !== "—" ? String(currentIFSC).slice(0, 4) : "—");
  const proposedBank = sbs?.proposed_bank ?? (proposedIFSC !== "—" ? String(proposedIFSC).slice(0, 4) : "—");

  return (
    <div
      data-testid="vernacular-banner"
      className={`rounded-xl border border-red-200 bg-red-50 p-4 ${className}`}
      role="alert"
    >
      <div className="flex gap-3">
        <AlertTriangle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
        <div className="flex-1 min-w-0">
          {/* Hindi primary when hindiHelp true, English primary otherwise — both present to satisfy spec + respect toggle */}
          {hindiHelp ? (
            <>
              <p data-testid="vernacular-hi" className="font-['Figtree'] text-sm font-medium text-red-800">
                {hiText}
              </p>
              <p data-testid="vernacular-en" className="font-['Figtree'] text-xs text-red-600 mt-1">
                {VERNACULAR_EN}
              </p>
            </>
          ) : (
            <>
              <p data-testid="vernacular-en" className="font-['Figtree'] text-sm font-medium text-red-800">
                {VERNACULAR_EN}
              </p>
              <p data-testid="vernacular-hi" className="font-['Figtree'] text-xs text-red-600 mt-1">
                {hiText}
              </p>
            </>
          )}
          <p data-testid="vernacular-hindi-help" className="sr-only">{String(hindiHelp)}</p>

          {sbs && (
            <div className="mt-3 overflow-x-auto">
              <table data-testid="vernacular-side-by-side" className="w-full text-xs border-collapse">
                <thead>
                  <tr className="text-left text-red-700">
                    <th className="py-1 pr-3 font-semibold">Field</th>
                    <th className="py-1 pr-3 font-semibold">Current</th>
                    <th className="py-1 font-semibold">Proposed</th>
                  </tr>
                </thead>
                <tbody className="font-['Figtree'] text-red-900">
                  <tr className="border-t border-red-200">
                    <td className="py-1.5 pr-3 font-medium">AD Code</td>
                    <td data-testid="sbs-current-ad" className="py-1.5 pr-3 font-mono">{currentAD}</td>
                    <td data-testid="sbs-proposed-ad" className="py-1.5 font-mono">{proposedAD}</td>
                  </tr>
                  <tr className="border-t border-red-200">
                    <td className="py-1.5 pr-3 font-medium">IFSC</td>
                    <td data-testid="sbs-current-ifsc" className="py-1.5 pr-3 font-mono">{currentIFSC}</td>
                    <td data-testid="sbs-proposed-ifsc" className="py-1.5 font-mono">{proposedIFSC}</td>
                  </tr>
                  <tr className="border-t border-red-200">
                    <td className="py-1.5 pr-3 font-medium">Bank</td>
                    <td data-testid="sbs-current-bank" className="py-1.5 pr-3 font-mono">{currentBank}</td>
                    <td data-testid="sbs-proposed-bank" className="py-1.5 font-mono">{proposedBank}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}

          {onConfirm && (
            <button
              data-testid="vernacular-confirm"
              onClick={onConfirm}
              className="mt-3 px-4 py-1.5 bg-red-600 text-white rounded-lg text-xs font-['Figtree'] hover:bg-red-700"
            >
              Confirm Human Gate
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export { VERNACULAR_HI, VERNACULAR_EN };
