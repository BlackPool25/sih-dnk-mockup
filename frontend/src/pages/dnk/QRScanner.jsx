// src/pages/dnk/QRScanner.jsx

import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useData } from "../../context/DataContext";
import { Html5Qrcode } from "html5-qrcode";

import {
  QrCode,
  Camera,
  CameraOff,
  Scan,
  X,
  Check,
  AlertCircle,
  Package,
  MapPin,
  User,
  FileCheck,
  ArrowLeft,
} from "lucide-react";

function QRScanner() {
  const navigate = useNavigate();
  const { loadShipmentByQR } = useData();

  const scannerRef = useRef(null);

  const [isScanning, setIsScanning] = useState(false);
  const [cameraActive, setCameraActive] = useState(false);
  const [scannedData, setScannedData] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  // Test on mount
  useEffect(() => {
    console.log("QRScanner mounted");
  }, []);

  // --------------------------------------------------
  // START CAMERA
  // --------------------------------------------------

  const startCamera = async () => {
    setIsLoading(true);
    setError(null);

    if (
      !navigator.mediaDevices ||
      !navigator.mediaDevices.getUserMedia
    ) {
      setError(
        "Camera not supported. Please use Chrome or Edge."
      );
      setIsLoading(false);
      return;
    }

    try {
      const container = document.getElementById(
        "scanner-container"
      );

      if (!container) {
        setError(
          "Scanner container not found. Please refresh and try again."
        );
        setIsLoading(false);
        return;
      }

      // Prevent creating multiple scanners
      if (scannerRef.current) {
        console.log("Scanner already exists");
        setIsLoading(false);
        return;
      }

      console.log("Starting QR scanner...");

      const html5QrCode = new Html5Qrcode(
        "scanner-container"
      );

      scannerRef.current = html5QrCode;

      const config = {
        fps: 10,
        qrbox: {
          width: 250,
          height: 250,
        },
        aspectRatio: 1.0,
      };

      await html5QrCode.start(
        {
          facingMode: "environment",
        },
        config,
        onScanSuccess,
        onScanError
      );

      console.log("Camera started successfully");

      setCameraActive(true);
      setIsScanning(true);
    } catch (err) {
      console.error("Camera error:", err);

      setError(
        "Unable to access camera. Please check camera permissions and try again."
      );

      scannerRef.current = null;
    } finally {
      setIsLoading(false);
    }
  };

  // --------------------------------------------------
  // QR SCAN SUCCESS
  // --------------------------------------------------

  const onScanSuccess = async (decodedText) => {
    console.log("QR Code scanned:", decodedText);

    await stopCamera();

    setIsLoading(true);
    setError(null);

    try {
      const normalizedQR = decodedText.trim().toUpperCase();

      console.log(
        "Looking up QR code:",
        normalizedQR
      );

      const shipment =
        await loadShipmentByQR(normalizedQR);

      console.log(
        "Shipment found:",
        shipment
      );

      if (shipment) {
        setScannedData(shipment);
        setError(null);
      } else {
        setError(
          `No shipment found with QR code: "${normalizedQR}"`
        );
        setScannedData(null);
      }
    } catch (err) {
      console.error(
        "Error fetching shipment:",
        err
      );

      setError(
        "Failed to fetch shipment details. Please try again."
      );

      setScannedData(null);
    } finally {
      setIsLoading(false);
    }
  };

  // --------------------------------------------------
  // QR SCAN ERROR
  // --------------------------------------------------

  const onScanError = (errorMessage) => {
    // html5-qrcode calls this constantly while looking
    // for a QR code, so don't display these as errors.
    if (
      errorMessage &&
      errorMessage.includes("Camera")
    ) {
      console.warn(
        "Scan error:",
        errorMessage
      );
    }
  };

  // --------------------------------------------------
  // STOP CAMERA
  // --------------------------------------------------

  const stopCamera = async () => {
    if (scannerRef.current) {
      try {
        await scannerRef.current.stop();

        await scannerRef.current.clear();
      } catch (err) {
        console.warn(
          "Error stopping camera:",
          err
        );
      }

      scannerRef.current = null;
    }

    setCameraActive(false);
    setIsScanning(false);
  };

  // --------------------------------------------------
  // MANUAL QR ENTRY
  // --------------------------------------------------

  const handleManualScan = async () => {
    const manualData = prompt(
      "Enter QR Code:\n\n" +
        "Available QR codes for testing:\n" +
        "• QR-001 (Verified - Jute Bags)\n" +
        "• QR-002 (Pending - Handloom Sarees)\n" +
        "• QR-003 (Verified - Wooden Toys)\n\n" +
        "Enter QR code:"
    );

    if (!manualData) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const normalizedQR =
        manualData.trim().toUpperCase();

      console.log(
        "Manual entry - normalized QR:",
        normalizedQR
      );

      const shipment =
        await loadShipmentByQR(normalizedQR);

      console.log(
        "Manual entry - shipment found:",
        shipment
      );

      if (shipment) {
        setScannedData(shipment);
        setError(null);

        if (cameraActive) {
          await stopCamera();
        }
      } else {
        setError(
          `No shipment found with QR code: "${normalizedQR}"\n\n` +
            `Available QR codes: QR-001, QR-002, QR-003`
        );

        setScannedData(null);
      }
    } catch (err) {
      console.error(
        "Error fetching shipment:",
        err
      );

      setError(
        "Failed to fetch shipment details. Please try again."
      );

      setScannedData(null);
    } finally {
      setIsLoading(false);
    }
  };

  // --------------------------------------------------
  // RESET
  // --------------------------------------------------

  const resetScanner = async () => {
    if (scannerRef.current) {
      await stopCamera();
    }

    setScannedData(null);
    setError(null);
    setCameraActive(false);
    setIsScanning(false);
    setIsLoading(false);
  };

  // --------------------------------------------------
  // CLEANUP WHEN PAGE UNMOUNTS
  // --------------------------------------------------

  useEffect(() => {
    return () => {
      if (scannerRef.current) {
        scannerRef.current
          .stop()
          .then(() => {
            return scannerRef.current?.clear();
          })
          .catch((err) => {
            console.warn(
              "Scanner cleanup error:",
              err
            );
          });

        scannerRef.current = null;
      }
    };
  }, []);

  return (
    <div className="min-h-screen bg-[#F8FAF7] p-4 lg:p-8">
      <div className="max-w-4xl mx-auto">

        {/* ------------------------------------------ */}
        {/* HEADER */}
        {/* ------------------------------------------ */}

        <div className="flex items-center gap-4 mb-6">
          <button
            onClick={() =>
              navigate("/dnk/dashboard")
            }
            className="p-2 rounded-lg hover:bg-[#F0F4EE] transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-[#6B7568]" />
          </button>

          <div>
            <h2 className="font-['Fraunces'] text-2xl font-semibold text-[#1B2E1B]">
               QR Scanner
            </h2>

            <p className="font-['Figtree'] text-[#6B7568]">
              Scan shipment QR codes to verify
              documents and details
            </p>
          </div>
        </div>

        {/* ------------------------------------------ */}
        {/* SCANNER CARD */}
        {/* ------------------------------------------ */}

        <div className="bg-white rounded-xl shadow-sm border border-[#E5EAE3] overflow-hidden">

          {/* Scanner header */}

          <div className="p-4 border-b border-[#E5EAE3] flex items-center justify-between">

            <div className="flex items-center gap-2">
              <QrCode className="w-5 h-5 text-[#6FAF6F]" />

              <span className="font-['Figtree'] font-medium text-[#1B2E1B]">
                QR Code Scanner
              </span>
            </div>

            {cameraActive && (
              <span className="flex items-center gap-1 text-xs font-['Figtree'] text-green-600">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                Active
              </span>
            )}
          </div>

          <div className="p-6">

            {/* -------------------------------------- */}
            {/* CAMERA VIEW */}
            {/* -------------------------------------- */}

            <div className="relative bg-[#1B2E1B] rounded-xl overflow-hidden aspect-video flex items-center justify-center">

              {/* IMPORTANT:
                  Scanner container ALWAYS exists.
                  This fixes "Scanner container not found".
              */}

              <div
                id="scanner-container"
                className={`w-full h-full ${
                  !cameraActive
                    ? "hidden"
                    : ""
                }`}
              />

              {/* Ready to scan */}

              {!cameraActive &&
                !scannedData &&
                !error && (
                  <div className="absolute inset-0 flex items-center justify-center text-center text-white p-8">

                    <div>
                      <QrCode className="w-16 h-16 mx-auto mb-4 opacity-50" />

                      <h3 className="font-['Fraunces'] text-xl font-semibold">
                        Ready to Scan
                      </h3>

                      <p className="font-['Figtree'] text-sm text-white/60 mt-2">
                        Click "Start Scanning"
                        to activate camera
                      </p>

                      <p className="font-['Figtree'] text-xs text-white/40 mt-1">
                        Or enter QR code manually
                      </p>
                    </div>

                  </div>
                )}

              {/* Loading */}

              {isLoading && (
                <div className="absolute inset-0 bg-black/50 flex items-center justify-center z-20">

                  <div className="text-center text-white">

                    <div className="w-12 h-12 border-4 border-[#A8C3A0] border-t-transparent rounded-full animate-spin mx-auto mb-4" />

                    <p className="font-['Figtree'] text-sm">
                      Loading...
                    </p>

                  </div>

                </div>
              )}

              {/* Scanner overlay */}

              {cameraActive &&
                !scannedData &&
                !error && (
                  <>
                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-10">

                      <div className="relative">

                        <div className="w-48 h-48 border-2 border-[#A8C3A0] rounded-lg shadow-[0_0_0_4000px_rgba(0,0,0,0.5)]">

                          <div className="absolute top-0 left-0 w-6 h-6 border-t-2 border-l-2 border-[#A8C3A0]" />

                          <div className="absolute top-0 right-0 w-6 h-6 border-t-2 border-r-2 border-[#A8C3A0]" />

                          <div className="absolute bottom-0 left-0 w-6 h-6 border-b-2 border-l-2 border-[#A8C3A0]" />

                          <div className="absolute bottom-0 right-0 w-6 h-6 border-b-2 border-r-2 border-[#A8C3A0]" />

                        </div>

                        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-40 h-0.5 bg-[#A8C3A0] animate-[scan_2s_ease-in-out_infinite] shadow-lg" />

                      </div>

                    </div>

                    {/* Scanning status */}

                    <div className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-black/75 text-white px-4 py-2 rounded-lg z-10">

                      <div className="flex items-center gap-2 font-['Figtree'] text-sm">

                        <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />

                        Scanning for QR code...

                      </div>

                    </div>
                  </>
                )}

              {/* Successful scan */}

              {scannedData && (
                <div className="absolute inset-0 bg-green-500/90 flex items-center justify-center z-20">

                  <div className="text-center text-white p-8">

                    <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center mx-auto mb-4">

                      <Check className="w-10 h-10" />

                    </div>

                    <h3 className="font-['Fraunces'] text-xl font-semibold">
                      QR Code Scanned!
                    </h3>

                    <p className="font-['Figtree'] text-sm text-white/80 mt-1">
                      Shipment:{" "}
                      {scannedData.id ||
                        scannedData.shipmentId ||
                        "N/A"}
                    </p>

                  </div>

                </div>
              )}

              {/* Error */}

              {error && !scannedData && (
                <div className="absolute inset-0 bg-red-500/90 flex items-center justify-center z-20">

                  <div className="text-center text-white p-8">

                    <AlertCircle className="w-16 h-16 mx-auto mb-4" />

                    <h3 className="font-['Fraunces'] text-xl font-semibold">
                      Scan Failed
                    </h3>

                    <p className="font-['Figtree'] text-sm text-white/80 mt-1 whitespace-pre-line">
                      {error}
                    </p>

                  </div>

                </div>
              )}

            </div>

            {/* -------------------------------------- */}
            {/* CONTROLS */}
            {/* -------------------------------------- */}

            <div className="mt-6 flex flex-wrap gap-3">

              {!scannedData && !error && (
                <>

                  {!cameraActive ? (
                    <button
                      onClick={startCamera}
                      disabled={isLoading}
                      className="flex-1 px-6 py-3 bg-[#A8C3A0] text-[#1B2E1B] font-['Figtree'] font-medium rounded-lg hover:bg-[#98B890] transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                      <Camera className="w-5 h-5" />

                      {isLoading
                        ? "Starting..."
                        : "Start Scanning"}
                    </button>
                  ) : (
                    <button
                      onClick={stopCamera}
                      className="flex-1 px-6 py-3 bg-red-500 text-white font-['Figtree'] font-medium rounded-lg hover:bg-red-600 transition-colors flex items-center justify-center gap-2"
                    >
                      <CameraOff className="w-5 h-5" />

                      Stop Scanning
                    </button>
                  )}

                  <button
                    onClick={handleManualScan}
                    disabled={isLoading}
                    className="px-6 py-3 border border-[#E5EAE3] text-[#6B7568] font-['Figtree'] font-medium rounded-lg hover:bg-[#F0F4EE] transition-colors flex items-center gap-2 disabled:opacity-50"
                  >
                    <Scan className="w-5 h-5" />

                    Manual Entry
                  </button>

                </>
              )}

              {(scannedData || error) && (
                <button
                  onClick={resetScanner}
                  className="flex-1 px-6 py-3 bg-[#A8C3A0] text-[#1B2E1B] font-['Figtree'] font-medium rounded-lg hover:bg-[#98B890] transition-colors flex items-center justify-center gap-2"
                >
                  <QrCode className="w-5 h-5" />

                  Scan New QR
                </button>
              )}

            </div>

          </div>
        </div>

        {/* ------------------------------------------ */}
        {/* SHIPMENT DETAILS */}
        {/* ------------------------------------------ */}

        {scannedData && (
          <div className="mt-6 bg-white rounded-xl shadow-sm border border-[#E5EAE3] overflow-hidden animate-fadeIn">

            {/* Details header */}

            <div className="p-4 bg-[#E8F0E6] border-b border-[#E5EAE3]">

              <div className="flex items-center justify-between">

                <div className="flex items-center gap-2">

                  <Package className="w-5 h-5 text-[#1B2E1B]" />

                  <span className="font-['Fraunces'] font-semibold text-[#1B2E1B]">
                    Shipment Details
                  </span>

                </div>

                <span
                  className={`px-2 py-1 rounded-full text-xs font-['Figtree'] font-medium ${
                    (
                      scannedData.status ||
                      scannedData.shipmentStatus
                    ) === "verified"
                      ? "bg-green-100 text-green-800"
                      : (
                          scannedData.status ||
                          scannedData.shipmentStatus
                        ) === "pending"
                      ? "bg-yellow-100 text-yellow-800"
                      : "bg-red-100 text-red-800"
                  }`}
                >
                  {(
                    scannedData.status ||
                    scannedData.shipmentStatus ||
                    "Unknown"
                  )
                    .charAt(0)
                    .toUpperCase() +
                    (
                      scannedData.status ||
                      scannedData.shipmentStatus ||
                      "Unknown"
                    ).slice(1)}
                </span>

              </div>

            </div>

            <div className="p-6 space-y-4">

              {/* Shipment ID / QR */}

              <div className="grid grid-cols-2 gap-4">

                <div>
                  <p className="font-['Figtree'] text-xs text-[#6B7568]">
                    Shipment ID
                  </p>

                  <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">
                    {scannedData.id ||
                      scannedData.shipmentId ||
                      "N/A"}
                  </p>
                </div>

                <div>
                  <p className="font-['Figtree'] text-xs text-[#6B7568]">
                    QR Code
                  </p>

                  <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">
                    {scannedData.qrCode ||
                      scannedData.qr ||
                      "N/A"}
                  </p>
                </div>

              </div>

              {/* Seller / Destination */}

              <div className="grid grid-cols-2 gap-4">

                <div className="flex items-start gap-2">

                  <User className="w-4 h-4 text-[#6B7568] mt-0.5" />

                  <div>
                    <p className="font-['Figtree'] text-xs text-[#6B7568]">
                      Seller
                    </p>

                    <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">
                      {scannedData.seller ||
                        scannedData.sellerName ||
                        "Unknown"}
                    </p>
                  </div>

                </div>

                <div className="flex items-start gap-2">

                  <MapPin className="w-4 h-4 text-[#6B7568] mt-0.5" />

                  <div>
                    <p className="font-['Figtree'] text-xs text-[#6B7568]">
                      Destination
                    </p>

                    <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">
                      {scannedData.destination ||
                        "N/A"}
                    </p>
                  </div>

                </div>

              </div>

              {/* Product information */}

              <div className="grid grid-cols-3 gap-4">

                <div className="p-3 bg-[#F8FAF7] rounded-lg">

                  <p className="font-['Figtree'] text-xs text-[#6B7568]">
                    Product
                  </p>

                  <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">
                    {scannedData.product ||
                      "Unknown"}
                  </p>

                </div>

                <div className="p-3 bg-[#F8FAF7] rounded-lg">

                  <p className="font-['Figtree'] text-xs text-[#6B7568]">
                    Quantity
                  </p>

                  <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">
                    {scannedData.quantity || 0}
                  </p>

                </div>

                <div className="p-3 bg-[#F8FAF7] rounded-lg">

                  <p className="font-['Figtree'] text-xs text-[#6B7568]">
                    Weight
                  </p>

                  <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">
                    {scannedData.weight ||
                      "N/A"}
                  </p>

                </div>

              </div>

              {/* Documents */}

              <div>

                <div className="flex items-center gap-2 mb-3">

                  <FileCheck className="w-4 h-4 text-[#6B7568]" />

                  <h4 className="font-['Figtree'] text-sm font-semibold text-[#1B2E1B]">
                    Documents (Extracted from Server)
                  </h4>

                </div>

                <div className="grid grid-cols-2 gap-2">

                  {scannedData.documentsData &&
                    Object.entries(
                      scannedData.documentsData
                    ).map(([doc, value]) => {

                      const verified =
                        scannedData.documents?.[
                          doc
                        ]?.verified !== false;

                      return (
                        <div
                          key={doc}
                          className="flex items-center gap-2 p-2 bg-[#F8FAF7] rounded-lg"
                        >

                          {verified ? (
                            <Check className="w-4 h-4 text-green-600" />
                          ) : (
                            <X className="w-4 h-4 text-red-600" />
                          )}

                          <div>

                            <p className="font-['Figtree'] text-xs font-medium text-[#1B2E1B]">
                              {doc.toUpperCase()}
                            </p>

                            <p className="font-['Figtree'] text-xs text-[#6B7568]">
                              {verified
                                ? value
                                : "Missing"}
                            </p>

                          </div>

                        </div>
                      );
                    })}

                  {!scannedData.documentsData && (
                    <div className="col-span-2 p-2 text-center font-['Figtree'] text-sm text-[#6B7568]">
                      No document data available
                    </div>
                  )}

                </div>

              </div>

              {/* Actions */}

              <div className="flex gap-3 pt-4 border-t border-[#E5EAE3]">

                <button
                  onClick={() =>
                    navigate(
                      `/dnk/shipment/${
                        scannedData.id ||
                        scannedData.shipmentId
                      }`
                    )
                  }
                  className="flex-1 px-4 py-2 bg-[#A8C3A0] text-[#1B2E1B] font-['Figtree'] font-medium rounded-lg hover:bg-[#98B890] transition-colors"
                >
                  View Full Details
                </button>

                <button
                  onClick={resetScanner}
                  className="px-4 py-2 border border-[#E5EAE3] text-[#6B7568] font-['Figtree'] font-medium rounded-lg hover:bg-[#F0F4EE] transition-colors"
                >
                  Scan New
                </button>

              </div>

            </div>
          </div>
        )}

      </div>

      {/* ------------------------------------------ */}
      {/* ANIMATIONS */}
      {/* ------------------------------------------ */}

      <style>{`
        @keyframes scan {
          0% {
            top: 10%;
          }

          50% {
            top: 90%;
          }

          100% {
            top: 10%;
          }
        }

        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }

          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .animate-fadeIn {
          animation: fadeIn 0.3s ease-out;
        }

        #scanner-container video {
          width: 100% !important;
          height: 100% !important;
          object-fit: cover;
        }
      `}</style>

    </div>
  );
}

export default QRScanner;