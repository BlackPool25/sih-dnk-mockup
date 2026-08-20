import { useState, useEffect, useCallback } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useData } from "../../context/DataContext";
import DocsTabs from "../../components/Order/DocsTabs";
import DocNotReadyBanner from "../../components/Order/DocNotReadyBanner";
import { getOrder, getDocuments } from "../../services/api";
import {
  ArrowLeft,
  Package,
  MapPin,
  User,
  Calendar,
  DollarSign,
  FileCheck,
  CheckCircle,
  XCircle,
  AlertCircle,
  Download,
  Printer,
  Share2,
  Truck,
  Clock,
  Check,
  X,
  AlertTriangle,
} from "lucide-react";

function ShipmentDetails() {
  const navigate = useNavigate();
  const { id } = useParams();
  const { loadShipmentDetails, loading, error } = useData();
  const [activeTab, setActiveTab] = useState("details");
  const [shipment, setShipment] = useState(null);
  const [realOrder, setRealOrder] = useState(null);
  const [docsData, setDocsData] = useState(null);
  const [docsLoading, setDocsLoading] = useState(false);
  const [docNotReady, setDocNotReady] = useState(null);

  useEffect(() => {
    if (id) {
      loadShipmentDetails(id)
        .then((data) => {
          if (data) setShipment(data);
        })
        .catch(console.error);
    }
  }, [id, loadShipmentDetails]);

  const fetchDocs = useCallback(async () => {
    if (!id) return;
    setDocsLoading(true);
    try {
      const o = await getOrder(id);
      setRealOrder(o);
    } catch {}
    try {
      const d = await getDocuments(id);
      setDocsData(d);
      const vs = d?.validation_state || "";
      const raw = d?.documents_raw || d?.docs || d?.generated || [];
      const hasAny = Array.isArray(raw) && raw.length > 0;
      const ready = String(vs).toLowerCase() === "ready" || String(vs).toLowerCase() === "validated" || String(vs).toLowerCase() === "complete";
      if (!ready || !hasAny) {
        setDocNotReady({
          docType: "",
          reason: !hasAny ? "No documents generated yet — seller must generate INVOICE, PACKING_LIST, CN22, CN23, PBE_IV per parcel." : `validation_state is ${vs || "unknown"}`,
          validationState: vs || null,
        });
      } else {
        setDocNotReady(null);
      }
    } catch (e) {
      const detail = e?.detail || e?.data?.detail;
      if (e?.status === 422 && detail?.code === "DOC_NOT_READY") {
        setDocNotReady({ docType: detail.doc_type || "", reason: detail.reason || e.message, validationState: detail.validation_state || null });
      } else if (e?.status === 404) {
        setDocNotReady({ docType: "", reason: "Order not found or not accessible", validationState: null });
      }
    } finally {
      setDocsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (activeTab === "documents") fetchDocs();
  }, [activeTab, fetchDocs]);

  const getStatusColor = (status) => {
    switch (status) {
      case "verified":
        return "bg-green-100 text-green-800";
      case "pending":
        return "bg-yellow-100 text-yellow-800";
      case "rejected":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case "verified":
        return <CheckCircle className="w-5 h-5" />;
      case "pending":
        return <Clock className="w-5 h-5" />;
      case "rejected":
        return <XCircle className="w-5 h-5" />;
      default:
        return <AlertCircle className="w-5 h-5" />;
    }
  };

  const getField = (field, fallback = "N/A") => shipment?.[field] || fallback;

  if (loading && !shipment) {
    return (
      <div className="min-h-screen bg-[#F8FAF7] flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-[#A8C3A0] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="font-['Figtree'] text-[#6B7568]">Loading shipment details...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[#F8FAF7] flex items-center justify-center">
        <div className="text-center">
          <p className="font-['Figtree'] text-red-600">Error: {error}</p>
          <button
            onClick={() => loadShipmentDetails(id)}
            className="mt-4 px-4 py-2 bg-[#A8C3A0] text-[#1B2E1B] rounded-lg font-['Figtree'] hover:bg-[#98B890] transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!shipment) {
    return (
      <div className="min-h-screen bg-[#F8FAF7] flex items-center justify-center">
        <div className="text-center">
          <Package className="w-16 h-16 text-[#E5EAE3] mx-auto mb-4" />
          <h3 className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B]">Shipment Not Found</h3>
          <p className="font-['Figtree'] text-[#6B7568] mt-2">The shipment you're looking for doesn't exist.</p>
          <button onClick={() => navigate("/dnk/dashboard")} className="mt-4 px-4 py-2 bg-[#A8C3A0] text-[#1B2E1B] rounded-lg font-['Figtree'] hover:bg-[#98B890] transition-colors">
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F8FAF7] p-4 lg:p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center gap-4 mb-6">
          <button onClick={() => navigate("/dnk/dashboard")} className="p-2 rounded-lg hover:bg-[#F0F4EE] transition-colors">
            <ArrowLeft className="w-5 h-5 text-[#6B7568]" />
          </button>
          <div className="flex-1">
            <h2 className="font-['Fraunces'] text-2xl font-semibold text-[#1B2E1B]">Shipment Details</h2>
            <div className="flex items-center gap-3 mt-1">
              <p className="font-['Figtree'] text-sm text-[#6B7568]">{getField("id", getField("shipmentId", "N/A"))}</p>
              <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-['Figtree'] font-medium ${getStatusColor(getField("status", getField("shipmentStatus", "pending")))}`}>
                {getStatusIcon(getField("status", getField("shipmentStatus", "pending")))}
                {getField("status", getField("shipmentStatus", "pending")).charAt(0).toUpperCase() + getField("status", getField("shipmentStatus", "pending")).slice(1)}
              </span>
            </div>
          </div>
          <div className="flex gap-2">
            <button className="p-2 rounded-lg hover:bg-[#F0F4EE] transition-colors" title="Print">
              <Printer className="w-5 h-5 text-[#6B7568]" />
            </button>
            <button className="p-2 rounded-lg hover:bg-[#F0F4EE] transition-colors" title="Share">
              <Share2 className="w-5 h-5 text-[#6B7568]" />
            </button>
          </div>
        </div>

        <div className="flex gap-1 bg-white rounded-xl p-1 border border-[#E5EAE3] mb-6">
          {["details", "documents", "tracking"].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 px-4 py-2 rounded-lg font-['Figtree'] text-sm font-medium transition-colors ${activeTab === tab ? "bg-[#A8C3A0] text-[#1B2E1B]" : "text-[#6B7568] hover:bg-[#F0F4EE]"}`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-[#E5EAE3] overflow-hidden">
          {activeTab === "details" && (
            <div className="p-6 space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 bg-[#F8FAF7] rounded-lg">
                  <div className="flex items-center gap-2 mb-1">
                    <User className="w-4 h-4 text-[#6B7568]" />
                    <p className="font-['Figtree'] text-xs text-[#6B7568]">Seller</p>
                  </div>
                  <p className="font-['Figtree'] font-medium text-[#1B2E1B]">{getField("seller", getField("sellerName", "Unknown"))}</p>
                  <p className="font-['Figtree'] text-sm text-[#6B7568]">{getField("sellerContact", "N/A")}</p>
                </div>
                <div className="p-4 bg-[#F8FAF7] rounded-lg">
                  <div className="flex items-center gap-2 mb-1">
                    <Calendar className="w-4 h-4 text-[#6B7568]" />
                    <p className="font-['Figtree'] text-xs text-[#6B7568]">Order Date</p>
                  </div>
                  <p className="font-['Figtree'] font-medium text-[#1B2E1B]">{getField("date", getField("orderDate", "N/A"))}</p>
                  <p className="font-['Figtree'] text-sm text-[#6B7568]">{getField("tracking", getField("trackingStatus", "N/A"))}</p>
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 bg-[#F8FAF7] rounded-lg">
                  <div className="flex items-center gap-2 mb-1">
                    <Package className="w-4 h-4 text-[#6B7568]" />
                    <p className="font-['Figtree'] text-xs text-[#6B7568]">Product</p>
                  </div>
                  <p className="font-['Figtree'] font-medium text-[#1B2E1B]">{getField("product", "Unknown")}</p>
                  <p className="font-['Figtree'] text-sm text-[#6B7568]">{getField("category", "N/A")}</p>
                </div>
                <div className="p-4 bg-[#F8FAF7] rounded-lg">
                  <p className="font-['Figtree'] text-xs text-[#6B7568]">Quantity & Weight</p>
                  <p className="font-['Figtree'] font-medium text-[#1B2E1B]">{getField("quantity", 0)} units</p>
                  <p className="font-['Figtree'] text-sm text-[#6B7568]">
                    {getField("weight", "N/A")} {getField("dimensions") ? `• ${getField("dimensions")}` : ""}
                  </p>
                </div>
                <div className="p-4 bg-[#F8FAF7] rounded-lg">
                  <div className="flex items-center gap-2 mb-1">
                    <DollarSign className="w-4 h-4 text-[#6B7568]" />
                    <p className="font-['Figtree'] text-xs text-[#6B7568]">Value</p>
                  </div>
                  <p className="font-['Figtree'] font-medium text-[#1B2E1B]">{getField("value", "₹0")}</p>
                </div>
              </div>
              <div className="p-4 bg-[#F8FAF7] rounded-lg">
                <div className="flex items-center gap-2 mb-1">
                  <MapPin className="w-4 h-4 text-[#6B7568]" />
                  <p className="font-['Figtree'] text-xs text-[#6B7568]">Destination</p>
                </div>
                <p className="font-['Figtree'] font-medium text-[#1B2E1B]">{getField("destination", "N/A")}</p>
                <p className="font-['Figtree'] text-sm text-[#6B7568]">{getField("destinationAddress", "")}</p>
              </div>
              {getField("notes") && (
                <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                  <p className="font-['Figtree'] text-sm text-yellow-800">📝 {getField("notes")}</p>
                </div>
              )}
              <div className="flex gap-3 pt-4 border-t border-[#E5EAE3]">
                <button className="flex-1 px-4 py-2 bg-[#A8C3A0] text-[#1B2E1B] font-['Figtree'] font-medium rounded-lg hover:bg-[#98B890] transition-colors">Verify Documents</button>
                <button className="flex-1 px-4 py-2 border border-[#E5EAE3] text-[#6B7568] font-['Figtree'] font-medium rounded-lg hover:bg-[#F0F4EE] transition-colors flex items-center justify-center gap-2">
                  <Download className="w-4 h-4" />
                  Export
                </button>
              </div>
            </div>
          )}

          {activeTab === "documents" && (
            <div className="p-6 space-y-4">
              <div className="flex items-center justify-between">
                <p className="font-['Figtree'] text-sm text-[#6B7568]">Per-parcel export documents — INVOICE, PACKING_LIST, CN22, CN23, PBE_IV</p>
                <span className="px-2 py-1 bg-[#F8FAF7] border border-[#E1E7DF] rounded-lg font-['Figtree'] text-xs text-[#6B7568]">PBE_III blocked</span>
              </div>
              {docsLoading ? (
                <div className="py-8 text-center">
                  <div className="w-8 h-8 border-4 border-[#A8C3A0] border-t-transparent rounded-full animate-spin mx-auto mb-3" />
                  <p className="font-['Figtree'] text-sm text-[#6B7568]">Loading documents…</p>
                </div>
              ) : (
                <>
                  {docNotReady && (
                    <DocNotReadyBanner
                      docType={docNotReady.docType}
                      reason={docNotReady.reason}
                      validationState={docNotReady.validationState}
                      canGenerate={false}
                      onGenerate={null}
                    />
                  )}
                  <DocsTabs
                    orderId={id}
                    order={realOrder || shipment}
                    documentsData={docsData}
                    validationState={docsData?.validation_state || realOrder?.validation_state}
                    docNotReady={docNotReady}
                    canGenerate={false}
                    onGenerate={null}
                  />
                  <div className="rounded-lg border border-[#E5EAE3] bg-[#F8FAF7] p-3 space-y-2">
                    <p className="font-['Figtree'] text-xs font-semibold text-[#1B2E1B] flex items-center gap-2">
                      <FileCheck className="w-4 h-4 text-[#6B7568]" />
                      KYC Verification (legacy)
                    </p>
                    {shipment.documents && Object.entries(shipment.documents).map(([doc, data]) => (
                      <div key={doc} className="flex items-center justify-between py-2 border-t border-[#E5EAE3] first:border-0">
                        <div className="flex items-center gap-2">
                          <div className={`p-1.5 rounded ${data.verified ? "bg-green-100" : "bg-red-100"}`}>
                            {data.verified ? <Check className="w-4 h-4 text-green-600" /> : <X className="w-4 h-4 text-red-600" />}
                          </div>
                          <span className="font-['Figtree'] text-xs font-medium text-[#1B2E1B]">{doc.toUpperCase()}</span>
                          <span className="font-['Figtree'] text-xs text-[#6B7568]">{data.number || "—"}</span>
                        </div>
                        <span className={`text-xs font-['Figtree'] ${data.verified ? "text-green-600" : "text-red-600"}`}>{data.verified ? "Verified" : "Missing"}</span>
                      </div>
                    ))}
                  </div>
                  <p className="font-['Figtree'] text-xs text-[#6B7568] flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    Tabs proof: DNK per-parcel download via GET /orders/{"{id}"}/pdf?doc_type=&parcel_id= · PBE_III blocked · DOC_NOT_READY amber banner
                  </p>
                </>
              )}
            </div>
          )}

          {activeTab === "tracking" && (
            <div className="p-6">
              {shipment.trackingUpdates && shipment.trackingUpdates.length > 0 ? (
                <div className="relative">
                  {shipment.trackingUpdates.map((update, index) => (
                    <div key={index} className="flex gap-4 mb-6 last:mb-0">
                      <div className="flex flex-col items-center">
                        <div className={`w-4 h-4 rounded-full border-2 ${index === 0 ? "bg-[#A8C3A0] border-[#A8C3A0]" : "bg-white border-[#E5EAE3]"}`} />
                        {index < shipment.trackingUpdates.length - 1 && <div className="w-0.5 h-12 bg-[#E5EAE3]" />}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <p className="font-['Figtree'] font-medium text-[#1B2E1B]">{update.status}</p>
                          <p className="font-['Figtree'] text-xs text-[#6B7568]">{update.date || update.time || "N/A"}</p>
                        </div>
                        <p className="font-['Figtree'] text-sm text-[#6B7568]">{update.location || "N/A"}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 font-['Figtree'] text-[#6B7568]">No tracking updates available for this shipment.</div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ShipmentDetails;
