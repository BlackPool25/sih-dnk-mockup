import { AlertTriangle, FileWarning } from "lucide-react";

export default function DocNotReadyBanner({
  docType,
  reason,
  validationState,
  onGenerate,
  generating = false,
  canGenerate = true,
}) {
  const isPbeIii = (docType || "").toUpperCase() === "PBE_III";
  const displayReason =
    reason || (isPbeIii ? "PBE_III is not generated via this flow" : "Documents not ready — generate first.");
  return (
    <div className="rounded-lg border border-amber-300 bg-amber-50 p-4 flex flex-col gap-3">
      <div className="flex items-start gap-3">
        <div className="w-9 h-9 rounded-lg bg-amber-100 flex items-center justify-center flex-shrink-0">
          <AlertTriangle className="w-5 h-5 text-amber-600" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-['Figtree'] text-sm font-semibold text-amber-900 flex items-center gap-2">
            <FileWarning className="w-4 h-4" />
            DOC_NOT_READY{docType ? ` — ${docType}` : ""}
          </p>
          <p className="font-['Figtree'] text-sm text-amber-800 mt-1 break-words">{displayReason}</p>
          {validationState && (
            <p className="font-['Figtree'] text-xs text-amber-700 mt-1">
              validation_state: <span className="font-mono font-medium">{validationState}</span>
            </p>
          )}
          {isPbeIii && (
            <p className="font-['Figtree'] text-xs text-amber-700 mt-1">
              PBE_III is never generated in this flow. Use PBE_IV.
            </p>
          )}
        </div>
      </div>
      {canGenerate && onGenerate && !isPbeIii && (
        <div className="flex">
          <button
            onClick={onGenerate}
            disabled={generating}
            className="inline-flex items-center gap-2 px-4 py-2 bg-amber-600 text-white font-['Figtree'] text-sm font-medium rounded-lg hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {generating ? (
              <>
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Generating…
              </>
            ) : (
              <>Generate Documents</>
            )}
          </button>
        </div>
      )}
    </div>
  );
}
