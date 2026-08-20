import { Check, Clock, ChevronDown } from "lucide-react";

export const UPFRONT_ORDER = ["pan", "iec", "ad_code", "icegate", "bank"];
export const SKIPPABLE_FIELDS = ["gstin", "udyam", "rcmc"];

export const FIELD_LABELS = {
  pan: "PAN",
  iec: "IEC",
  ad_code: "AD Code",
  icegate: "ICEGATE",
  bank: "Bank",
  gstin: "GSTIN",
  udyam: "Udyam",
  rcmc: "RCMC",
};

export const STEP_META = {
  pan: { label: "PAN", desc: "10 अक्षर", required: true },
  iec: { label: "IEC", desc: "10 अंक", required: true },
  ad_code: { label: "AD Code", desc: "14 अंक", required: true },
  icegate: { label: "ICEGATE", desc: "कस्टम खाता", required: true },
  bank: { label: "Bank", desc: "₹1 check", required: true },
  gstin: { label: "GSTIN", desc: "बाद में", required: false },
  udyam: { label: "Udyam", desc: "बाद में", required: false },
  rcmc: { label: "RCMC", desc: "बाद में", required: false },
};

export function VerificationStepper({ currentField, completedFields = [], collapsedOpen, onToggleCollapsed, onSelectField }) {
  return (
    <div data-testid="verification-stepper" className="mb-6">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-['Figtree'] text-xs font-semibold tracking-widest text-[#1B2E1B] uppercase">Verification Steps</h3>
        <span className="font-['Figtree'] text-xs text-[#6B7568]">{UPFRONT_ORDER.length} Required + 3 बाद में</span>
      </div>

      {/* Horizontal stepper */}
      <div className="flex items-center gap-1 sm:gap-2 overflow-x-auto pb-2" role="list" aria-label="verification stepper">
        {UPFRONT_ORDER.map((field, idx) => {
          const meta = STEP_META[field];
          const isActive = currentField === field;
          const isCompleted = completedFields.includes(field);
          return (
            <div key={field} className="flex items-center flex-1 min-w-0" role="listitem">
              <button
                type="button"
                onClick={() => onSelectField?.(field)}
                className={`flex flex-col items-center gap-1 flex-1 rounded-lg border px-2 py-2 sm:px-3 sm:py-2.5 transition-colors cursor-pointer focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] ${
                  isActive ? "bg-[#1B2E1B] border-[#1B2E1B] text-white" : isCompleted ? "bg-[#E8F0E6] border-[#A8C3A0] text-[#1B2E1B]" : "bg-white border-[#E5EAE3] text-[#6B7568] hover:border-[#A8C3A0]"
                }`}
                aria-current={isActive ? "step" : undefined}
                data-testid={`step-${field}`}
                data-required="true"
                aria-label={`Verification step ${meta.label}`}
              >
                <div className="flex items-center gap-1.5">
                  <span className={`flex items-center justify-center w-5 h-5 rounded-full text-[10px] font-bold shrink-0 ${isActive ? "bg-white text-[#1B2E1B]" : isCompleted ? "bg-[#A8C3A0] text-[#1B2E1B]" : "bg-[#E5EAE3] text-[#6B7568]"}`}>
                    {isCompleted ? <Check className="w-3 h-3" /> : idx + 1}
                  </span>
                  <span className="font-['Figtree'] text-xs font-semibold whitespace-nowrap">{meta.label}</span>
                </div>
                <span className={`font-['Figtree'] text-[10px] leading-none whitespace-nowrap ${isActive ? "text-white/70" : "text-[#6B7568]"}`}>{meta.desc}</span>
                <span className={`font-['Figtree'] text-[10px] font-medium px-1.5 py-0.5 rounded ${isActive ? "bg-white/20 text-white" : "bg-[#F8FAF7] text-[#6B7568] border border-[#E5EAE3]"}`}>Required</span>
              </button>
              {idx < UPFRONT_ORDER.length - 1 && (
                <div className={`mx-1 h-0.5 flex-1 min-w-[8px] ${isCompleted ? "bg-[#A8C3A0]" : "bg-[#E5EAE3]"}`} aria-hidden="true" />
              )}
            </div>
          );
        })}
      </div>

      {/* Skippable collapsed */}
      <div className="mt-3 rounded-lg border border-dashed border-[#E5EAE3] bg-[#F8FAF7]">
        <button
          type="button"
          onClick={onToggleCollapsed}
          aria-expanded={!!collapsedOpen}
          aria-controls="skippable-fields"
          data-testid="skippable-toggle"
          className="w-full flex items-center justify-between px-3 py-2.5 text-left"
        >
          <span className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-[#6B7568]" />
            <span className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">बाद में — Optional (Skip for now)</span>
            <span className="hidden sm:inline font-['Figtree'] text-xs text-[#6B7568]">GSTIN · Udyam · RCMC</span>
          </span>
          <ChevronDown className={`w-4 h-4 text-[#6B7568] transition-transform ${collapsedOpen ? "rotate-180" : ""}`} />
        </button>
        {collapsedOpen && (
          <div id="skippable-fields" className="px-3 pb-3 grid grid-cols-3 gap-2" data-testid="skippable-fields">
            {SKIPPABLE_FIELDS.map((field) => {
              const meta = STEP_META[field];
              const isActive = currentField === field;
              return (
                <button
                  key={field}
                  type="button"
                  onClick={() => onSelectField?.(field)}
                  data-testid={`step-${field}`}
                  data-required="false"
                  data-skippable="true"
                  className={`rounded-lg border px-2 py-2 text-center cursor-pointer focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] ${isActive ? "bg-[#1B2E1B] border-[#1B2E1B] text-white" : "bg-white border-[#E5EAE3] text-[#6B7568] hover:border-[#A8C3A0]"}`}
                >
                  <div className="font-['Figtree'] text-xs font-semibold">{meta.label}</div>
                  <div className="font-['Figtree'] text-[10px]">{meta.desc}</div>
                  <div className="font-['Figtree'] text-[10px] mt-1 inline-block px-1.5 py-0.5 rounded bg-[#F8FAF7] border border-[#E5EAE3]">बाद में</div>
                </button>
              );
            })}
          </div>
        )}
      </div>

      <p className="font-['Figtree'] text-[10px] text-[#6B7568] mt-2">
        Upfront order: <span data-testid="upfront-order">{UPFRONT_ORDER.join(" → ")}</span> · Skippable: बाद में (तब भरें)
      </p>
    </div>
  );
}

export default VerificationStepper;
