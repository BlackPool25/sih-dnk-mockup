// src/components/QRCodeGenerator.jsx
import { useState, useRef, useEffect } from "react";
import QRCode from "qrcode";
import { Download, Copy, Check, QrCode } from "lucide-react";

function QRCodeGenerator({ shipmentId, qrData }) {
  const [qrCodeUrl, setQrCodeUrl] = useState("");
  const [copied, setCopied] = useState(false);
  const canvasRef = useRef(null);

  useEffect(() => {
    if (qrData) {
      generateQRCode();
    }
  }, [qrData]);

  const generateQRCode = async () => {
    try {
      // Generate QR code as data URL
      const qrDataUrl = await QRCode.toDataURL(qrData, {
        width: 300,
        margin: 2,
        color: {
          dark: "#1B2E1B",
          light: "#FFFFFF",
        },
      });
      setQrCodeUrl(qrDataUrl);
    } catch (error) {
      console.error("Error generating QR code:", error);
    }
  };

  const downloadQRCode = () => {
    if (!qrCodeUrl) return;
    const link = document.createElement("a");
    link.download = `QR-${shipmentId || "shipment"}.png`;
    link.href = qrCodeUrl;
    link.click();
  };

  const copyToClipboard = async () => {
    if (!qrCodeUrl) return;
    try {
      const response = await fetch(qrCodeUrl);
      const blob = await response.blob();
      await navigator.clipboard.write([
        new ClipboardItem({
          [blob.type]: blob,
        }),
      ]);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error("Error copying QR code:", error);
      // Fallback: copy text
      try {
        await navigator.clipboard.writeText(qrData);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      } catch (err) {
        alert("QR Code data: " + qrData);
      }
    }
  };

  return (
    <div className="flex flex-col items-center p-6 bg-white rounded-xl border border-[#E5EAE3]">
      <div className="flex items-center gap-2 mb-4">
        <QrCode className="w-5 h-5 text-[#6FAF6F]" />
        <h3 className="font-['Figtree'] font-semibold text-[#1B2E1B]">
          Shipment QR Code
        </h3>
      </div>

      {/* QR Code Display */}
      <div className="relative">
        {qrCodeUrl ? (
          <img
            src={qrCodeUrl}
            alt="QR Code"
            className="w-48 h-48 border-2 border-[#E5EAE3] rounded-lg"
          />
        ) : (
          <div className="w-48 h-48 bg-[#F8FAF7] border-2 border-dashed border-[#E5EAE3] rounded-lg flex items-center justify-center">
            <p className="font-['Figtree'] text-sm text-[#6B7568]">
              No QR Code
            </p>
          </div>
        )}
      </div>

      {/* QR Code Data */}
      <p className="mt-3 font-['Figtree'] text-xs text-[#6B7568] break-all max-w-[200px] text-center">
        {qrData || "No data"}
      </p>

      {/* Actions */}
      <div className="flex gap-2 mt-4">
        <button
          onClick={downloadQRCode}
          disabled={!qrCodeUrl}
          className="px-4 py-2 bg-[#A8C3A0] text-[#1B2E1B] font-['Figtree'] text-sm font-medium rounded-lg hover:bg-[#98B890] transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          <Download className="w-4 h-4" />
          Download
        </button>
        <button
          onClick={copyToClipboard}
          disabled={!qrCodeUrl}
          className="px-4 py-2 border border-[#E5EAE3] text-[#6B7568] font-['Figtree'] text-sm font-medium rounded-lg hover:bg-[#F0F4EE] transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {copied ? (
            <>
              <Check className="w-4 h-4 text-green-600" />
              Copied!
            </>
          ) : (
            <>
              <Copy className="w-4 h-4" />
              Copy
            </>
          )}
        </button>
      </div>
    </div>
  );
}

export default QRCodeGenerator;