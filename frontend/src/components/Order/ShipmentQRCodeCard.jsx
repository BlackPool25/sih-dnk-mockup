import { useState, useEffect } from "react";
import QRCode from "qrcode";
import {
  QrCode,
  Download,
  Copy,
  Check,
  Printer,
  ExternalLink,
  ShieldCheck,
  FileText,
  Building2,
  Package,
} from "lucide-react";

export default function ShipmentQRCodeCard({ orderId, order, documentsData }) {
  const [qrDataUrl, setQrDataUrl] = useState("");
  const [copied, setCopied] = useState(false);
  const [generating, setGenerating] = useState(false);

  const cleanId = (orderId || "").replace("#", "");
  // Target URL that points to the backend / DNK Sahayak interface
  const scanTargetUrl = typeof window !== "undefined"
    ? `${window.location.origin}/dnk/shipment/${cleanId}`
    : `/dnk/shipment/${cleanId}`;

  useEffect(() => {
    if (cleanId) {
      generateQR();
    }
  }, [cleanId]);

  const generateQR = async () => {
    try {
      setGenerating(true);
      const url = await QRCode.toDataURL(scanTargetUrl, {
        width: 320,
        margin: 2,
        color: {
          dark: "#1B2E1B",
          light: "#FFFFFF",
        },
        errorCorrectionLevel: "H",
      });
      setQrDataUrl(url);
    } catch (err) {
      console.error("Error rendering QR code:", err);
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = () => {
    if (!qrDataUrl) return;
    const a = document.createElement("a");
    a.href = qrDataUrl;
    a.download = `DNK-QR-${cleanId.slice(0, 8)}.png`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const handlePrint = () => {
    const printWin = window.open("", "_blank", "width=600,height=700");
    if (!printWin) return;
    printWin.document.write(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>DNK Postal Label - ${cleanId}</title>
          <style>
            body { font-family: 'Segoe UI', Arial, sans-serif; text-align: center; padding: 24px; color: #1B2E1B; }
            .badge { display: inline-block; background: #E8F5E9; color: #2E7D32; font-weight: bold; padding: 4px 12px; border-radius: 12px; font-size: 12px; margin-bottom: 12px; border: 1px solid #C8E6C9; }
            .card { border: 2px solid #1B2E1B; border-radius: 16px; padding: 24px; max-width: 420px; margin: 0 auto; }
            .qr-img { width: 220px; height: 220px; margin: 12px auto; }
            .title { font-size: 18px; font-weight: bold; margin: 0 0 4px; }
            .subtitle { font-size: 12px; color: #666; margin: 0 0 16px; }
            .meta { text-align: left; background: #F8FAF7; padding: 12px; border-radius: 8px; font-size: 12px; line-height: 1.6; margin-top: 16px; border: 1px solid #E1E7DF; }
            .meta strong { color: #1B2E1B; }
            @media print { .no-print { display: none; } }
          </style>
        </head>
        <body>
          <div class="card">
            <div class="badge">DAK GHAR NIRYAT KENDRA • OFFICIAL COUNTER QR</div>
            <div class="title">Postal Dispatch & Verification QR</div>
            <div class="subtitle">Order ID: ${cleanId}</div>
            <img class="qr-img" src="${qrDataUrl}" alt="Shipment QR" />
            <div class="meta">
              <div><strong>Destination:</strong> ${order?.destination_country || "DE"}</div>
              <div><strong>Recipient:</strong> ${order?.consignee || "Consignee"}</div>
              <div><strong>Declared Value:</strong> ₹${((order?.value_minor || 0) / 100).toLocaleString("en-IN")}</div>
              <div><strong>Statutory Docs:</strong> INVOICE, PACKING LIST, CN22/23, PBE-IV</div>
              <div><strong>Target Endpoint:</strong> /dnk/shipment/${cleanId}</div>
            </div>
          </div>
          <script>
            window.onload = function() { window.print(); };
          </script>
        </body>
      </html>
    `);
    printWin.document.close();
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(scanTargetUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      alert(`QR Code Link: ${scanTargetUrl}`);
    }
  };

  return (
    <div className="bg-white rounded-xl border border-[#E1E7DF] p-6 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6 pb-4 border-b border-[#E8ECE7]">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-[#E8F5E9] text-[#2E7D32] rounded-xl">
            <QrCode className="w-6 h-6" />
          </div>
          <div>
            <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B]">
              Official Shipment QR Code
            </h3>
            <p className="font-['Figtree'] text-xs text-[#6B7568]">
              Dak Ghar Niryat Kendra Counter Scan & Verification
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-[#E8F5E9] border border-[#C8E6C9] rounded-full text-xs font-medium text-[#2E7D32] font-['Figtree']">
            <ShieldCheck className="w-3.5 h-3.5" />
            Database Linked
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
        {/* QR Code Preview Box */}
        <div className="md:col-span-5 flex flex-col items-center justify-center p-4 bg-[#F8FAF7] rounded-xl border border-[#E1E7DF]">
          {generating ? (
            <div className="w-48 h-48 flex items-center justify-center">
              <div className="w-8 h-8 border-4 border-[#A8C3A0] border-t-transparent rounded-full animate-spin" />
            </div>
          ) : qrDataUrl ? (
            <div className="relative group p-3 bg-white rounded-xl shadow-sm border border-[#E1E7DF]">
              <img
                src={qrDataUrl}
                alt={`Shipment QR for ${cleanId}`}
                className="w-48 h-48 object-contain rounded-lg"
              />
              <div className="mt-2 text-center">
                <span className="font-mono text-xs font-medium text-[#1B2E1B] bg-[#F0F4EE] px-2 py-0.5 rounded">
                  {cleanId ? `${cleanId.slice(0, 8)}…${cleanId.slice(-6)}` : "—"}
                </span>
              </div>
            </div>
          ) : (
            <div className="w-48 h-48 flex items-center justify-center text-xs text-[#6B7568]">
              QR Not Available
            </div>
          )}

          <div className="flex items-center gap-2 mt-4 w-full justify-center">
            <button
              onClick={handleDownload}
              className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 bg-white hover:bg-[#F0F4EE] text-[#1B2E1B] border border-[#D0D7CE] rounded-lg font-['Figtree'] text-xs font-medium transition-colors shadow-sm"
              title="Download QR code image"
            >
              <Download className="w-3.5 h-3.5 text-[#2E7D32]" />
              Save PNG
            </button>
            <button
              onClick={handlePrint}
              className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 bg-white hover:bg-[#F0F4EE] text-[#1B2E1B] border border-[#D0D7CE] rounded-lg font-['Figtree'] text-xs font-medium transition-colors shadow-sm"
              title="Print official dispatch label"
            >
              <Printer className="w-3.5 h-3.5 text-[#2E7D32]" />
              Print Label
            </button>
            <button
              onClick={handleCopy}
              className="p-2 bg-white hover:bg-[#F0F4EE] text-[#1B2E1B] border border-[#D0D7CE] rounded-lg font-['Figtree'] text-xs font-medium transition-colors shadow-sm"
              title="Copy scan link"
            >
              {copied ? (
                <Check className="w-4 h-4 text-[#2E7D32]" />
              ) : (
                <Copy className="w-4 h-4 text-[#6B7568]" />
              )}
            </button>
          </div>
        </div>

        {/* Counter Instructions & Document Access Info */}
        <div className="md:col-span-7 space-y-4">
          <div className="p-4 bg-[#F8FAF7] rounded-xl border border-[#E1E7DF]">
            <h4 className="font-['Figtree'] text-sm font-semibold text-[#1B2E1B] flex items-center gap-2 mb-1.5">
              <Building2 className="w-4 h-4 text-[#2E7D32]" />
              DNK Sahayak Counter Handover Workflow
            </h4>
            <p className="font-['Figtree'] text-xs text-[#525E50] leading-relaxed">
              When taking this consignment to the post office, the postal officer / Sahayak scans this QR code from their authorized login.
              The scan fetches the complete verified order record directly from the database and unlocks all 4 export documents.
            </p>
          </div>

          <div className="space-y-2">
            <p className="font-['Figtree'] text-xs font-medium text-[#6B7568] uppercase tracking-wider">
              Accessible to Postal Officer Upon Scan:
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-['Figtree']">
              <div className="flex items-center gap-2 p-2 bg-white rounded-lg border border-[#E8ECE7]">
                <Package className="w-4 h-4 text-[#2E7D32]" />
                <span className="text-[#1B2E1B]">Order Details & Specs</span>
              </div>
              <div className="flex items-center gap-2 p-2 bg-white rounded-lg border border-[#E8ECE7]">
                <ShieldCheck className="w-4 h-4 text-[#2E7D32]" />
                <span className="text-[#1B2E1B]">Seller KYC & IEC Verification</span>
              </div>
              <div className="flex items-center gap-2 p-2 bg-white rounded-lg border border-[#E8ECE7]">
                <FileText className="w-4 h-4 text-[#2E7D32]" />
                <span className="text-[#1B2E1B]">4 Statutory Export PDFs</span>
              </div>
              <div className="flex items-center gap-2 p-2 bg-white rounded-lg border border-[#E8ECE7]">
                <Download className="w-4 h-4 text-[#2E7D32]" />
                <span className="text-[#1B2E1B]">Complete DocPack Bundle</span>
              </div>
            </div>
          </div>

          <div className="pt-2 flex items-center justify-between">
            <a
              href={`/dnk/shipment/${cleanId}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 font-['Figtree'] text-xs font-medium text-[#2E7D32] hover:text-[#1B5E20] hover:underline"
            >
              Preview DNK Sahayak Counter View
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
            <span className="font-mono text-[10px] text-[#8C968A]">
              Endpoint: /orders/{cleanId ? cleanId.slice(0, 8) : "id"}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
