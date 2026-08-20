import { useState, useMemo } from "react";
import { Download, FileText, Loader2, Package, CheckCircle, Clock } from "lucide-react";
import DocNotReadyBanner from "./DocNotReadyBanner";
import { downloadOrderPdfForDoc } from "../../services/api";

// Always show these 4 doc types — never filter/hide. CN23 is derived automatically
// when value >300 SDR, but PBE_IV flow only needs INVOICE+PACKING_LIST+CN22+PBE_IV.
const DOC_TYPES = [
  { key: "INVOICE", label: "Commercial Invoice", short: "Invoice" },
  { key: "PACKING_LIST", label: "Packing List", short: "Packing" },
  { key: "CN22", label: "CN22", short: "CN22" },
  { key: "PBE_IV", label: "PBE-IV", short: "PBE-IV" },
];

function deriveParcels(order, parcelsProp) {
  if (Array.isArray(parcelsProp) && parcelsProp.length > 0) return parcelsProp;
  if (order?.parcels && Array.isArray(order.parcels) && order.parcels.length > 0) {
    return order.parcels.map((p, idx) => {
      if (typeof p === "string") return { parcel_id: p, label: `Parcel ${idx + 1}` };
      if (p && typeof p === "object" && p.parcel_id) {
        return { ...p, label: p.label || `Parcel ${idx + 1} · ${p.parcel_id.slice(0, 8)}` };
      }
      return { parcel_id: `parcel-${idx}`, label: `Parcel ${idx + 1}`, ...p };
    });
  }
  const items = order?.line_items;
  if (Array.isArray(items) && items.length > 0) {
    if (items.length === 1) {
      return [{ parcel_id: null, label: "Parcel 1", item: items[0] }];
    }
    return items.map((it, idx) => ({
      parcel_id: it.parcel_id || it.id || `item-${idx}`,
      label: `Parcel ${idx + 1} · ${it.category_slug || it.hs_code || `Item ${idx + 1}`}`,
      item: it,
    }));
  }
  return [{ parcel_id: null, label: "Parcel 1" }];
}

function isDocGenerated(documentsData, docType) {
  const lists = [
    documentsData?.documents_raw,
    documentsData?.generated,
    documentsData?.docs,
    documentsData?.documents ? Object.values(documentsData.documents).filter(Boolean) : null,
  ];
  for (const list of lists) {
    if (!Array.isArray(list) || list.length === 0) continue;
    for (const d of list) {
      if (!d || typeof d !== "object") continue;
      const t = String(d.doc_type || d.docType || d.type || "").toUpperCase();
      if (t === docType) return true;
      if (docType === "PACKING_LIST" && t === "PACKING") return true;
      if (docType === "PACKING" && t === "PACKING_LIST") return true;
    }
  }
  // Also check mapped documents object (backend proxy maps doc types to named keys)
  const mapped = documentsData?.documents;
  if (mapped && typeof mapped === "object" && !Array.isArray(mapped)) {
    const keyMap = { INVOICE: "commercial_invoice", PACKING_LIST: "packing_list", CN22: "customs_declaration", PBE_IV: "postal_bill_of_export" };
    const mappedKey = keyMap[docType];
    if (mappedKey && mapped[mappedKey]) return true;
  }
  return false;
}

export default function DocsTabs({
  orderId,
  order,
  documentsData,
  parcels: parcelsProp,
  validationState,
  docNotReady,
  onGenerate,
  generating = false,
  canGenerate = true,
  onDownloadComplete,
}) {
  const parcels = useMemo(() => deriveParcels(order, parcelsProp), [order, parcelsProp]);
  const [activeIdx, setActiveIdx] = useState(0);
  const [downloadingKey, setDownloadingKey] = useState(null);
  const [banner, setBanner] = useState(null);
  const [localError, setLocalError] = useState(null);

  const activeParcel = parcels[activeIdx] || parcels[0];
  const activeParcelId = activeParcel?.parcel_id || null;

  async function handleDownload(docType) {
    if (docType === "PBE_III") {
      setBanner({ docType, reason: "PBE_III is not generated via this flow", validationState });
      return;
    }
    const key = `${docType}:${activeParcelId || "single"}`;
    setDownloadingKey(key);
    setBanner(null);
    setLocalError(null);
    try {
      const blob = await downloadOrderPdfForDoc(orderId, docType, activeParcelId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      const suffix = activeParcelId ? `-${activeParcelId}` : "";
      a.href = url;
      a.download = `${docType.toLowerCase()}${suffix}-${orderId}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      if (onDownloadComplete) onDownloadComplete(docType, activeParcelId);
    } catch (err) {
      const status = err?.status;
      const detail = err?.detail || err?.data?.detail;
      const code = detail?.code || err?.data?.detail?.code;
      const reason = detail?.reason || detail?.detail?.reason || detail?.reason || err?.message || "";
      if (status === 422 && (code === "DOC_NOT_READY" || detail?.code === "DOC_NOT_READY" || String(err.message).includes("DOC_NOT_READY"))) {
        setBanner({ docType, reason: reason || "DOC_NOT_READY — documents not yet generated", validationState: detail?.validation_state || validationState });
      } else if (status === 422) {
        setBanner({ docType, reason: reason || err.message, validationState });
      } else {
        setLocalError(err.message || "Download failed");
      }
    } finally {
      setDownloadingKey(null);
    }
  }

  const effectiveBanner = banner || docNotReady;

  return (
    <div className="space-y-4">
      {parcels.length > 1 && (
        <div className="flex gap-2 overflow-x-auto pb-1">
          {parcels.map((p, idx) => (
            <button
              key={p.parcel_id || idx}
              onClick={() => {
                setActiveIdx(idx);
                setBanner(null);
              }}
              className={`px-4 py-2 rounded-lg font-['Figtree'] text-sm font-medium whitespace-nowrap border transition-colors ${
                idx === activeIdx
                  ? "bg-[#A8C3A0] text-[#1B2E1B] border-[#A8C3A0]"
                  : "bg-white text-[#6B7568] border-[#E5EAE3] hover:bg-[#F0F4EE]"
              }`}
            >
              <span className="inline-flex items-center gap-1.5">
                <Package className="w-4 h-4" />
                {p.label}
              </span>
            </button>
          ))}
        </div>
      )}

      {parcels.length === 1 && (
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#F8FAF7] border border-[#E5EAE3] font-['Figtree'] text-xs text-[#6B7568]">
          <Package className="w-3.5 h-3.5" />
          {parcels[0].label}
          {activeParcelId ? ` · ${activeParcelId}` : ""}
        </div>
      )}

      {effectiveBanner && (
        <DocNotReadyBanner
          docType={effectiveBanner.docType}
          reason={effectiveBanner.reason}
          validationState={effectiveBanner.validationState || validationState}
          onGenerate={onGenerate}
          generating={generating}
          canGenerate={canGenerate}
        />
      )}

      {localError && <div className="rounded-lg border border-red-200 bg-red-50 p-3 font-['Figtree'] text-sm text-red-700">{localError}</div>}

      {/* Always render all 4 doc cards — never filter/hide. Status per doc, download always enabled. */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {DOC_TYPES.map((dt) => {
          const key = `${dt.key}:${activeParcelId || "single"}`;
          const isDownloading = downloadingKey === key;
          const generated = isDocGenerated(documentsData, dt.key);
          return (
            <div key={dt.key} className="flex items-center justify-between p-4 bg-[#F8FAF7] rounded-lg border border-[#E5EAE3]">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-[#E8F0E6] flex items-center justify-center">
                  <FileText className="w-4 h-4 text-[#6FAF6F]" />
                </div>
                <div>
                  <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">{dt.label}</p>
                  <p className="font-['Figtree'] text-xs text-[#6B7568]">
                    {dt.key}
                    {activeParcelId ? ` · ${String(activeParcelId).slice(0, 8)}` : ""}
                  </p>
                  <span
                    className={`mt-1 inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium font-['Figtree'] border ${generated ? "bg-green-50 text-green-700 border-green-200" : "bg-amber-50 text-amber-700 border-amber-200"}`}
                  >
                    {generated ? <CheckCircle className="w-3 h-3" /> : <Clock className="w-3 h-3" />}
                    {generated ? "generated" : "not yet"}
                  </span>
                </div>
              </div>
              <button
                onClick={() => handleDownload(dt.key)}
                disabled={isDownloading}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-[#E5EAE3] text-[#1B2E1B] font-['Figtree'] text-xs font-medium rounded-lg hover:bg-[#F0F4EE] disabled:opacity-50 transition-colors"
                title={`Download ${dt.label}${activeParcelId ? ` for ${activeParcelId}` : ""}`}
              >
                {isDownloading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                PDF
              </button>
            </div>
          );
        })}
      </div>

      {!effectiveBanner && (() => {
        const hasAny = DOC_TYPES.some((dt) => isDocGenerated(documentsData, dt.key));
        if (hasAny) return null;
        const empty = !documentsData || (!documentsData.documents_raw && !documentsData.generated && !documentsData.docs);
        if (!empty) return null;
        return (
          <div className="rounded-lg border border-amber-300 bg-amber-50 p-4">
            <p className="font-['Figtree'] text-sm text-amber-800">No documents generated yet for this order.</p>
            {canGenerate && onGenerate && (
              <button
                onClick={onGenerate}
                disabled={generating}
                className="mt-3 inline-flex items-center gap-2 px-4 py-2 bg-amber-600 text-white font-['Figtree'] text-sm font-medium rounded-lg hover:bg-amber-700 disabled:opacity-50 transition-colors"
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
            )}
          </div>
        );
      })()}

      <p className="font-['Figtree'] text-xs text-[#6B7568]">PBE_III is not generated via this flow — PBE_IV only. Cards always show INVOICE, PACKING_LIST, CN22, PBE_IV with generated/not yet status.</p>
    </div>
  );
}
