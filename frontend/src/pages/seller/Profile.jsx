import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useData } from "../../context/DataContext";
import Layout from "../../components/seller/Layout";
import {
  User,
  Briefcase,
  Phone,
  Mail,
  MapPin,
  CheckCircle,
  Upload,
  Eye,
  Edit,
  Save,
  X,
  Building,
  CreditCard,
  FileText,
  AlertCircle,
  Download,
  File,
  LogOut,
  Shield,
  AlertTriangle,
} from "lucide-react";
import {
  fetchSellerProfile,
  createSellerProfile,
  updateSellerProfile,
  uploadProfileDocument,
  listProfileDocuments,
  confirmHumanGate,
  MAX_DOC_BYTES,
} from "../../services/api";
import VerificationBadge from "../../components/VerificationBadge";
import VernacularBanner from "../../components/VernacularBanner";

const DOC_DEFS = [
  { id: 1, name: "IEC Certificate", docType: "iec_certificate" },
  { id: 2, name: "GSTIN Certificate", docType: "gst_certificate" },
  { id: 3, name: "AD Code Document", docType: "other" },
  { id: 4, name: "PAN Card", docType: "pan_card" },
  { id: 5, name: "Bank Statement", docType: "bank_statement" },
  { id: 6, name: "LUT / Export Bond", docType: "other" },
];

const DEMO_PAYLOAD = {
  firm_name: "Kumar Handloom Studio",
  owner_name: "Aarav Kumar",
  pan: "ABCDE1234F",
  iec: "1234567890",
  ad_code: "12345678901234",
  bank_account: "12345678901",
  ifsc: "SBIN0001234",
  bank_name: "State Bank of India",
  bank_branch: "Varanasi Main",
  gstin: "22AAAAA0000A1Z5",
  address_line1: "12, Weavers Colony",
  address_line2: "Varanasi",
  city: "Varanasi",
  state: "Uttar Pradesh",
  pincode: "221001",
  phone: "9876543210",
};

function trustBadgeClass(level) {
  if (level === "L3") return "bg-purple-100 text-purple-700 border-purple-200";
  if (level === "L2") return "bg-green-100 text-green-700 border-green-200";
  if (level === "L1") return "bg-amber-100 text-amber-700 border-amber-200";
  return "bg-gray-100 text-gray-600 border-gray-200";
}

function Profile() {
  const navigate = useNavigate();
  const { loadProfile, updateProfile, profile: apiProfile, loading: ctxLoading, error: ctxError } = useData();
  const [isEditing, setIsEditing] = useState(false);
  const [showDocumentModal, setShowDocumentModal] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  const [showHumanGate, setShowHumanGate] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const fileInputRefs = useRef({});

  const [userData, setUserData] = useState(() => {
    const stored = localStorage.getItem("user");
    return stored ? JSON.parse(stored) : { name: "Aarav Kumar", email: "aarav@kumarhandloom.in" };
  });

  const [profile, setProfile] = useState({
    name: userData.name || "Aarav Kumar",
    business: "Kumar Handloom Studio",
    phone: "+91 98765 43210",
    email: userData.email || "aarav@kumarhandloom.in",
    address: "12, Weavers Colony, Varanasi, UP — 221001",
    since: "April 2023",
    iec: "Not available",
    gstin: "Not available",
    adCode: "Not available",
    lut: "Not submitted",
    bankAccount: "6789",
    bankHolder: "Aarav Kumar",
    bankName: "State Bank of India, Varanasi",
    bankAdCode: "SBI001234567",
  });

  const [trustLevel, setTrustLevel] = useState("L0");
  const [trustScore, setTrustScore] = useState(0);
  const [payoutsFrozen, setPayoutsFrozen] = useState(false);
  const [isVerified, setIsVerified] = useState(false);
  const [realProfile, setRealProfile] = useState(null);
  const [profileLoading, setProfileLoading] = useState(true);
  const [profileError, setProfileError] = useState(null);

  const [documents, setDocuments] = useState(
    DOC_DEFS.slice(0, 4).map((d) => ({
      id: d.id,
      name: d.name,
      docType: d.docType,
      status: "Not uploaded",
      uploaded: false,
      fileName: null,
      fileSize: null,
      uploadDate: null,
      documentNumber: null,
    }))
  );
  const [realDocs, setRealDocs] = useState([]);
  const [uploadingDoc, setUploadingDoc] = useState(null);
  const [uploadError, setUploadError] = useState(null);
  const [demoLoading, setDemoLoading] = useState(false);
  const [demoResult, setDemoResult] = useState(null);
  const [humanGateForm, setHumanGateForm] = useState({ current_ad: "", proposed_ad: "", current_ifsc: "", proposed_ifsc: "" });
  const [humanGateLoading, setHumanGateLoading] = useState(false);
  const [humanGateResult, setHumanGateResult] = useState(null);
  const [humanGateError, setHumanGateError] = useState(null);

  const [editForm, setEditForm] = useState(profile);

  const refreshTrustFromProfile = (p) => {
    if (!p) return;
    setTrustLevel(p.trust_level || "L0");
    setTrustScore(p.trust_score ?? 0);
    setPayoutsFrozen(!!p.payouts_frozen);
    setIsVerified(!!p.is_verified);
    setRealProfile(p);
    setProfile((prev) => ({
      ...prev,
      name: p.owner_name || prev.name,
      business: p.firm_name || prev.business,
      phone: p.phone ? `+91 ${p.phone}` : prev.phone,
      email: userData.email || prev.email,
      address: `${p.address_line1 || ""}${p.address_line2 ? ", " + p.address_line2 : ""}${p.city ? ", " + p.city : ""}${p.state ? ", " + p.state : ""}${p.pincode ? " — " + p.pincode : ""}` || prev.address,
      iec: p.iec || "Not available",
      gstin: p.gstin || "Not available",
      adCode: p.ad_code || "Not available",
      lut: "Not submitted",
      bankAccount: p.bank_account ? `****${String(p.bank_account).slice(-4)}` : prev.bankAccount,
      bankHolder: p.owner_name || prev.bankHolder,
      bankName: p.bank_name || prev.bankName,
      bankAdCode: p.ad_code || prev.bankAdCode,
    }));
  };

  const loadRealProfile = async () => {
    setProfileLoading(true);
    setProfileError(null);
    try {
      const p = await fetchSellerProfile();
      refreshTrustFromProfile(p);
    } catch (e) {
      if (e?.status === 404) {
        setProfileError("No profile yet — use Demo Docs to create one.");
      } else {
        setProfileError(e?.detail || e?.message || "Failed to load profile");
      }
    } finally {
      setProfileLoading(false);
    }
  };

  const loadRealDocs = async () => {
    try {
      const docs = await listProfileDocuments();
      setRealDocs(docs);
      setDocuments((prev) =>
        prev.map((doc) => {
          const match = docs.find((d) => d.doc_type === doc.docType);
          if (match) {
            return {
              ...doc,
              uploaded: true,
              status: "Encrypted ✓",
              fileName: match.filename,
              fileSize: "encrypted",
              uploadDate: new Date(match.uploaded_at).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }),
              documentNumber: match.checksum_sha256.slice(0, 12),
              realId: match.id,
            };
          }
          return doc;
        })
      );
    } catch {
      // ignore if not available
    }
  };

  useEffect(() => {
    loadRealProfile();
    loadRealDocs();
  }, []);

  useEffect(() => {
    loadProfile()
      .then((data) => {
        if (data) {
          setProfile((prev) => ({
            ...prev,
            name: data.name || prev.name,
            business: data.business || prev.business,
            phone: data.phone || prev.phone,
            email: data.email || prev.email,
            address: data.address || prev.address,
            since: data.since || prev.since,
            iec: data.iec || prev.iec,
            gstin: data.gstin || prev.gstin,
            adCode: data.adCode || prev.adCode,
            lut: data.lut || prev.lut,
          }));
          setEditForm((prev) => ({
            ...prev,
            name: data.name || prev.name,
            business: data.business || prev.business,
            phone: data.phone || prev.phone,
            email: data.email || prev.email,
            address: data.address || prev.address,
          }));
        }
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    const stored = localStorage.getItem("user");
    if (stored) {
      const user = JSON.parse(stored);
      setProfile((prev) => ({
        ...prev,
        name: user.name || prev.name,
        email: user.email || prev.email,
      }));
      setEditForm((prev) => ({
        ...prev,
        name: user.name || prev.name,
        email: user.email || prev.email,
      }));
    }
  }, []);

  const handleEdit = () => {
    setEditForm(profile);
    setIsEditing(true);
  };

  const handleSave = async () => {
    setProfile(editForm);
    const stored = localStorage.getItem("user");
    if (stored) {
      const user = JSON.parse(stored);
      user.name = editForm.name;
      user.email = editForm.email;
      localStorage.setItem("user", JSON.stringify(user));
    }
    try {
      await updateProfile(editForm);
      setIsEditing(false);
    } catch (err) {
      console.error("Error saving profile:", err);
      alert("Failed to save profile. Please try again.");
    }
  };

  const handleCancel = () => setIsEditing(false);

  const handleLogout = () => {
    localStorage.removeItem("user");
    localStorage.removeItem("token");
    navigate("/signin");
  };

  const handleViewDocument = (doc) => {
    if (doc.uploaded) {
      setSelectedDocument(doc);
      setShowDocumentModal(true);
    }
  };

  const handleUploadClick = (docId) => {
    const input = fileInputRefs.current[docId];
    if (input) input.click();
  };

  const handleUploadDocument = async (docId, file) => {
    if (!file) return;
    setUploadError(null);
    if (file.size > MAX_DOC_BYTES) {
      setUploadError(`File too large: ${(file.size / (1024 * 1024)).toFixed(1)} MB exceeds 10 MB limit.`);
      return;
    }
    const docDef = DOC_DEFS.find((d) => d.id === docId) || documents.find((d) => d.id === docId);
    const docType = docDef?.docType || "other";
    setUploadingDoc(docId);
    try {
      const result = await uploadProfileDocument(file, docType);
      await loadRealDocs();
      await loadRealProfile();
      setDocuments((prev) =>
        prev.map((doc) => {
          if (doc.id === docId) {
            return {
              ...doc,
              uploaded: true,
              status: "Encrypted ✓",
              fileName: result.filename || file.name,
              fileSize: `${(file.size / 1024).toFixed(1)} KB`,
              uploadDate: new Date().toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }),
              documentNumber: result.checksum_sha256 ? result.checksum_sha256.slice(0, 12) : null,
              realId: result.id,
            };
          }
          return doc;
        })
      );
    } catch (e) {
      const msg = e?.detail || e?.message || "Upload failed";
      if (typeof msg === "object") setUploadError(JSON.stringify(msg));
      else setUploadError(String(msg));
    } finally {
      setUploadingDoc(null);
      const inp = fileInputRefs.current[docId];
      if (inp) inp.value = "";
    }
  };

  const handleUseDemoDocs = async () => {
    setDemoLoading(true);
    setDemoResult(null);
    setProfileError(null);
    try {
      let result;
      try {
        const existing = await fetchSellerProfile();
        result = await updateSellerProfile(DEMO_PAYLOAD);
        void existing;
      } catch (e) {
        if (e?.status === 404) {
          result = await createSellerProfile(DEMO_PAYLOAD);
        } else if (e?.status === 422) {
          const detail = e?.data?.detail;
          if (detail && typeof detail === "object" && detail.payouts_frozen) {
            setPayoutsFrozen(true);
            setDemoResult({ error: detail.message || detail.vernacular || "Payouts frozen — confirm human gate" });
            setShowHumanGate(true);
            setHumanGateForm((prev) => ({
              ...prev,
              current_ad: detail.side_by_side?.current_ad || DEMO_PAYLOAD.ad_code,
              proposed_ad: DEMO_PAYLOAD.ad_code,
              current_ifsc: detail.side_by_side?.current_ifsc || DEMO_PAYLOAD.ifsc,
              proposed_ifsc: DEMO_PAYLOAD.ifsc,
            }));
            return;
          }
          throw e;
        } else {
          throw e;
        }
      }
      refreshTrustFromProfile(result);
      setDemoResult({ ok: true, trust_level: result.trust_level, payouts_frozen: result.payouts_frozen });
      await loadRealDocs();
    } catch (e) {
      const detail = e?.data?.detail || e?.detail || e?.message;
      let msg = typeof detail === "string" ? detail : JSON.stringify(detail || e?.message || "Demo fill failed");
      setDemoResult({ error: msg });
      if (e?.status === 422 && e?.data?.detail?.payouts_frozen) {
        setPayoutsFrozen(true);
        setShowHumanGate(true);
      }
    } finally {
      setDemoLoading(false);
    }
  };

  const handleConfirmHumanGate = async () => {
    setHumanGateLoading(true);
    setHumanGateError(null);
    setHumanGateResult(null);
    try {
      if (!humanGateForm.current_ad || !humanGateForm.proposed_ad) {
        setHumanGateError("current_ad and proposed_ad required (14 digits)");
        setHumanGateLoading(false);
        return;
      }
      const res = await confirmHumanGate({
        current_ad: humanGateForm.current_ad,
        proposed_ad: humanGateForm.proposed_ad,
        current_ifsc: humanGateForm.current_ifsc || undefined,
        proposed_ifsc: humanGateForm.proposed_ifsc || undefined,
      });
      setHumanGateResult(res);
      setPayoutsFrozen(false);
      await loadRealProfile();
      setDemoResult({ ok: true, trust_level: realProfile?.trust_level || trustLevel });
    } catch (e) {
      const msg = e?.detail || e?.message || "Human gate failed";
      setHumanGateError(typeof msg === "object" ? JSON.stringify(msg) : String(msg));
    } finally {
      setHumanGateLoading(false);
    }
  };

  const getStatusColor = (status) => {
    if (status === "Encrypted ✓" || status === "Verified") return "text-green-600";
    if (status === "Pending Verification") return "text-amber-600";
    if (status === "Optional") return "text-[#6B7568]";
    return "text-[#6B7568]";
  };

  const getStatusIcon = (status) => {
    if (status === "Encrypted ✓" || status === "Verified") return "✅";
    if (status === "Pending Verification") return "⏳";
    if (status === "Optional") return "📄";
    return "📄";
  };

  const getStatusBadgeColor = (status) => {
    if (status === "Encrypted ✓" || status === "Verified") return "bg-green-100 text-green-700 border-green-200";
    if (status === "Pending Verification") return "bg-amber-100 text-amber-700 border-amber-200";
    if (status === "Optional") return "bg-gray-100 text-gray-600 border-gray-200";
    return "bg-gray-100 text-gray-600 border-gray-200";
  };

  if (profileLoading && ctxLoading) {
    return (
      <Layout pageTitle="Seller Profile" pageSubtitle="Manage your account and export information.">
        <div className="flex items-center justify-center min-h-[300px]">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-[#A8C3A0] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="font-['Figtree'] text-[#6B7568]">Loading profile...</p>
          </div>
        </div>
      </Layout>
    );
  }

  if (ctxError && !realProfile) {
    // still show profile with error banner rather than full error screen
  }

  return (
    <Layout pageTitle="Seller Profile" pageSubtitle="Manage your account and export information.">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl border border-[#E1E7DF] overflow-hidden sticky top-6">
            <div className="bg-gradient-to-r from-[#E8F0E6] to-[#F0F7EE] p-6 text-center">
              <div className="w-24 h-24 rounded-full bg-[#A8C3A0] flex items-center justify-center mx-auto text-3xl font-['Fraunces'] font-semibold text-[#1B2E1B]">
                {profile.name
                  .split(" ")
                  .map((n) => n[0])
                  .join("")}
              </div>
              <h2 className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B] mt-3">{profile.name}</h2>
              <p className="font-['Figtree'] text-sm text-[#6B7568]">Seller since {profile.since}</p>
              <div className="flex items-center justify-center gap-2 mt-2 flex-wrap">
                <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-['Figtree'] font-medium border ${trustBadgeClass(trustLevel)}`}>
                  <Shield className="w-3.5 h-3.5" />
                  {trustLevel} {isVerified ? "· Verified" : "· Unverified"} {trustScore ? `· ${trustScore}` : ""}
                </span>
                <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-['Figtree'] font-medium ${payoutsFrozen ? "bg-red-100 text-red-700 border border-red-200" : "bg-green-100 text-green-700 border border-green-200"}`}>
                  {payoutsFrozen ? <AlertTriangle className="w-3.5 h-3.5" /> : <CheckCircle className="w-3.5 h-3.5" />}
                  {payoutsFrozen ? "Payouts frozen" : "Payouts active"}
                </span>
              </div>
              {payoutsFrozen && (
                <VernacularBanner
                  detail={{ vernacular: "यह खाता आपके IEC से लिंक AD Code के खाते से मेल नहीं खाता — इससे आपकी e-BRC नहीं बनेगी", side_by_side: { current_ad: realProfile?.ad_code || "—", proposed_ad: humanGateForm.proposed_ad || "—", current_ifsc: realProfile?.ifsc || "—", proposed_ifsc: humanGateForm.proposed_ifsc || "—" } }}
                  onConfirm={() => setShowHumanGate(true)}
                  className="mt-3 text-left"
                />
              )}
            </div>

            <div className="p-4 space-y-4">
              <div>
                <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider">Business</p>
                <div className="flex items-center gap-2 mt-1">
                  <Briefcase className="w-4 h-4 text-[#6B7568]" />
                  <span className="font-['Figtree'] text-sm text-[#1B2E1B]">{profile.business}</span>
                </div>
              </div>
              <div>
                <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider">Phone</p>
                <div className="flex items-center gap-2 mt-1">
                  <Phone className="w-4 h-4 text-[#6B7568]" />
                  <span className="font-['Figtree'] text-sm text-[#1B2E1B]">{profile.phone}</span>
                </div>
              </div>
              <div>
                <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider">Email</p>
                <div className="flex items-center gap-2 mt-1">
                  <Mail className="w-4 h-4 text-[#6B7568]" />
                  <span className="font-['Figtree'] text-sm text-[#1B2E1B]">{profile.email}</span>
                </div>
              </div>
              <div>
                <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider">Address</p>
                <div className="flex items-start gap-2 mt-1">
                  <MapPin className="w-4 h-4 text-[#6B7568] flex-shrink-0 mt-0.5" />
                  <span className="font-['Figtree'] text-sm text-[#1B2E1B]">{profile.address}</span>
                </div>
              </div>

              <div className="space-y-2">
                <button onClick={handleEdit} className="w-full flex items-center justify-center gap-2 px-4 py-2 border border-[#E5EAE3] rounded-lg font-['Figtree'] text-sm text-[#1B2E1B] hover:bg-[#F8FAF7] transition-colors">
                  <Edit className="w-4 h-4" />
                  Edit Profile
                </button>
                <button onClick={() => setShowLogoutConfirm(true)} className="w-full flex items-center justify-center gap-2 px-4 py-2 border border-red-200 rounded-lg font-['Figtree'] text-sm text-red-600 hover:bg-red-50 transition-colors">
                  <LogOut className="w-4 h-4" />
                  Logout
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-xl border border-[#E1E7DF] p-6">
            <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
              <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B]">Trust & Verification</h3>
              <VerificationBadge className="justify-end" />
            </div>
            <div className="grid grid-cols-2 gap-3 mb-4">
              <div className="p-3 bg-[#F8FAF7] rounded-lg border border-[#E1E7DF]">
                <p className="text-xs text-[#6B7568] font-['Figtree']">Trust Level</p>
                <p className="text-lg font-['Fraunces'] font-semibold text-[#1B2E1B]">{trustLevel}</p>
                <p className="text-xs text-[#6B7568] font-['Figtree']">L0 untrusted → L1 PAN → L2 IEC+AD+bank+IFSC → L3 liveness</p>
              </div>
              <div className="p-3 bg-[#F8FAF7] rounded-lg border border-[#E1E7DF]">
                <p className="text-xs text-[#6B7568] font-['Figtree']">Payouts</p>
                <p className={`text-sm font-['Figtree'] font-semibold ${payoutsFrozen ? "text-red-600" : "text-green-600"}`}>{payoutsFrozen ? "Frozen — human gate required" : "Active"}</p>
                <p className="text-xs text-[#6B7568] font-['Figtree']">AD/bank mismatch freezes payouts</p>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <button onClick={handleUseDemoDocs} disabled={demoLoading} className={`px-4 py-2 rounded-lg font-['Figtree'] text-sm font-medium transition-colors ${demoLoading ? "bg-gray-200 text-gray-500" : "bg-[#1B2E1B] text-white hover:bg-[#2a4a2a]"}`}>
                {demoLoading ? "Applying..." : "Use Demo Docs"}
              </button>
              <button onClick={loadRealProfile} className="px-4 py-2 rounded-lg border border-[#E1E7DF] font-['Figtree'] text-sm hover:bg-[#F8FAF7]">Refresh</button>
              {payoutsFrozen && (
                <button onClick={() => setShowHumanGate(true)} className="px-4 py-2 rounded-lg bg-amber-600 text-white font-['Figtree'] text-sm hover:bg-amber-700">Human Gate</button>
              )}
            </div>
            <p className="mt-2 text-xs font-['Figtree'] text-[#6B7568]">Fills mocked PAN/IEC/AD/bank → L2. Encrypted at rest, demo only.</p>
            {demoResult?.ok && <p className="mt-2 text-xs font-['Figtree'] text-green-700">✓ Demo profile applied — {demoResult.trust_level} {demoResult.payouts_frozen ? "(payouts frozen)" : ""}</p>}
            {demoResult?.error && (
              <>
                <p className="mt-2 text-xs font-['Figtree'] text-red-600">{demoResult.error}</p>
                {String(demoResult.error).includes("यह खाता") || payoutsFrozen ? (
                  <VernacularBanner detail={{ vernacular: "यह खाता आपके IEC से लिंक AD Code के खाते से मेल नहीं खाता — इससे आपकी e-BRC नहीं बनेगी", side_by_side: { current_ad: humanGateForm.current_ad, proposed_ad: humanGateForm.proposed_ad, current_ifsc: humanGateForm.current_ifsc, proposed_ifsc: humanGateForm.proposed_ifsc } }} className="mt-3" onConfirm={() => setShowHumanGate(true)} />
                ) : null}
              </>
            )}
            {profileError && <p className="mt-2 text-xs font-['Figtree'] text-amber-700">{profileError}</p>}
          </div>

          <div className="bg-white rounded-xl border border-[#E1E7DF] p-6">
            <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B] mb-4">Business & Export Details</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider">IEC Number</p>
                <p className={`font-['Figtree'] text-sm font-medium mt-1 ${profile.iec !== "Not available" ? "text-[#1B2E1B]" : "text-[#6B7568]"}`}>
                  {profile.iec}
                  {profile.iec !== "Not available" && <span className="ml-2 text-xs text-green-600">✅ Verified</span>}
                </p>
              </div>
              <div>
                <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider">GSTIN</p>
                <p className={`font-['Figtree'] text-sm font-medium mt-1 ${profile.gstin !== "Not available" ? "text-[#1B2E1B]" : "text-[#6B7568]"}`}>
                  {profile.gstin}
                  {profile.gstin !== "Not available" && <span className="ml-2 text-xs text-green-600">✅ Verified</span>}
                </p>
              </div>
              <div>
                <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider">AD Code</p>
                <p className={`font-['Figtree'] text-sm font-medium mt-1 ${profile.adCode !== "Not available" ? "text-[#1B2E1B]" : "text-[#6B7568]"}`}>
                  {profile.adCode}
                  {profile.adCode !== "Not available" && <span className="ml-2 text-xs text-green-600">✅ Verified</span>}
                </p>
              </div>
              <div>
                <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider">LUT / Bond</p>
                <p className={`font-['Figtree'] text-sm font-medium mt-1 ${profile.lut !== "Not submitted" ? "text-[#1B2E1B]" : "text-[#6B7568]"}`}>{profile.lut}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-[#E1E7DF] p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B]">Documents — encrypted</h3>
              <span className="text-xs font-['Figtree'] text-[#6B7568]">10 MB limit · AES-256-GCM</span>
            </div>
            {uploadError && (
              <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-lg flex gap-2">
                <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />
                <p className="text-xs font-['Figtree'] text-red-700">{uploadError}</p>
              </div>
            )}
            <div className="space-y-3">
              {documents.map((doc) => (
                <div key={doc.id} className="flex items-center justify-between py-2 border-b border-[#E8ECE7] last:border-0 gap-3">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="p-2 bg-[#F8FAF7] rounded-lg">
                      <File className="w-4 h-4 text-[#6B7568]" />
                    </div>
                    <div className="min-w-0">
                      <p className="font-['Figtree'] text-sm text-[#1B2E1B]">{doc.name}</p>
                      <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                        <span className={`text-xs font-['Figtree'] ${getStatusColor(doc.status)}`}>{getStatusIcon(doc.status)} {doc.status}</span>
                        {doc.uploaded && (
                          <>
                            <span className="text-xs text-[#6B7568]">·</span>
                            <span className="text-xs text-[#6B7568] truncate">{doc.fileName}</span>
                            <span className="text-xs text-[#6B7568]">·</span>
                            <span className="text-xs text-[#6B7568]">{doc.fileSize}</span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    {doc.uploaded ? (
                      <button onClick={() => handleViewDocument(doc)} className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-['Figtree'] text-[#6B7568] hover:text-[#1B2E1B] transition-colors bg-[#F8FAF7] rounded-lg hover:bg-[#E8F0E6]">
                        <Eye className="w-3.5 h-3.5" />
                        View
                      </button>
                    ) : null}
                    <input
                      type="file"
                      ref={(el) => (fileInputRefs.current[doc.id] = el)}
                      className="hidden"
                      onChange={(e) => handleUploadDocument(doc.id, e.target.files?.[0])}
                      accept=".pdf,.jpg,.jpeg,.png"
                    />
                    <button onClick={() => handleUploadClick(doc.id)} disabled={uploadingDoc === doc.id} className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-['Figtree'] font-medium rounded-lg transition-colors ${uploadingDoc === doc.id ? "bg-gray-200 text-gray-500 cursor-not-allowed" : "bg-[#A8C3A0] text-[#1B2E1B] hover:bg-[#98B890]"}`}>
                      {uploadingDoc === doc.id ? (
                        <>
                          <span className="animate-spin rounded-full h-3 w-3 border-2 border-[#1B2E1B] border-t-transparent"></span>
                          Uploading...
                        </>
                      ) : (
                        <>
                          <Upload className="w-3.5 h-3.5" />
                          {doc.uploaded ? "Replace" : "Upload"}
                        </>
                      )}
                    </button>
                  </div>
                </div>
              ))}
            </div>
            {realDocs.length > 0 && (
              <div className="mt-4 p-3 bg-green-50 rounded-lg border border-green-200">
                <p className="font-['Figtree'] text-xs text-green-700">{realDocs.length} encrypted document(s) on file — download verified via checksum.</p>
              </div>
            )}
          </div>

          <div className="bg-white rounded-xl border border-[#E1E7DF] p-6">
            <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B] mb-4">Bank & Settlement</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider">Account</p>
                <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B] mt-1">{profile.bankAccount}</p>
              </div>
              <div>
                <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider">Holder</p>
                <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B] mt-1">{profile.bankHolder}</p>
              </div>
              <div>
                <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider">Bank</p>
                <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B] mt-1">{profile.bankName}</p>
              </div>
              <div>
                <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider">AD Code</p>
                <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B] mt-1">{profile.bankAdCode}</p>
              </div>
            </div>
            <div className="mt-4 pt-4 border-t border-[#E8ECE7]">
              <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-['Figtree'] font-medium ${payoutsFrozen ? "bg-red-100 text-red-700" : "bg-green-100 text-green-700"}`}>
                {payoutsFrozen ? <AlertTriangle className="w-3.5 h-3.5" /> : <CheckCircle className="w-3.5 h-3.5" />}
                {payoutsFrozen ? "Payouts frozen" : "Linked"}
              </span>
            </div>
          </div>
        </div>
      </div>

      {showHumanGate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full">
            <div className="flex items-center justify-between p-6 border-b border-[#E8ECE7]">
              <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B]">Human Gate — Confirm AD/Bank Binding</h3>
              <button onClick={() => setShowHumanGate(false)} className="p-2 rounded-lg hover:bg-[#F0F5EE]">
                <X className="w-5 h-5 text-[#6B7568]" />
              </button>
            </div>
            <div className="p-6 space-y-3">
              <p className="text-xs font-['Figtree'] text-[#6B7568]">Side-by-side review required when AD Code or bank changes. This unfreezes payouts.</p>
              <div>
                <label className="block text-xs font-['Figtree'] text-[#6B7568] mb-1">Current AD (14 digits)</label>
                <input value={humanGateForm.current_ad} onChange={(e) => setHumanGateForm({ ...humanGateForm, current_ad: e.target.value })} className="w-full px-3 py-2 border border-[#E5EAE3] rounded-lg text-sm font-['Figtree']" placeholder="12345678901234" />
              </div>
              <div>
                <label className="block text-xs font-['Figtree'] text-[#6B7568] mb-1">Proposed AD</label>
                <input value={humanGateForm.proposed_ad} onChange={(e) => setHumanGateForm({ ...humanGateForm, proposed_ad: e.target.value })} className="w-full px-3 py-2 border border-[#E5EAE3] rounded-lg text-sm font-['Figtree']" placeholder="12345678901234" />
              </div>
              <div>
                <label className="block text-xs font-['Figtree'] text-[#6B7568] mb-1">Current IFSC</label>
                <input value={humanGateForm.current_ifsc} onChange={(e) => setHumanGateForm({ ...humanGateForm, current_ifsc: e.target.value })} className="w-full px-3 py-2 border border-[#E5EAE3] rounded-lg text-sm font-['Figtree']" placeholder="SBIN0001234" />
              </div>
              <div>
                <label className="block text-xs font-['Figtree'] text-[#6B7568] mb-1">Proposed IFSC</label>
                <input value={humanGateForm.proposed_ifsc} onChange={(e) => setHumanGateForm({ ...humanGateForm, proposed_ifsc: e.target.value })} className="w-full px-3 py-2 border border-[#E5EAE3] rounded-lg text-sm font-['Figtree']" placeholder="HDFC0001234" />
              </div>
              {humanGateError && <p className="text-xs font-['Figtree'] text-red-600">{humanGateError}</p>}
              {humanGateResult?.human_gate_confirmed && <p className="text-xs font-['Figtree'] text-green-600">✓ Human gate confirmed — payouts unfrozen.</p>}
            </div>
            <div className="flex items-center justify-end gap-3 p-6 border-t border-[#E8ECE7]">
              <button onClick={() => setShowHumanGate(false)} className="px-4 py-2 text-sm font-['Figtree'] text-[#6B7568]">Cancel</button>
              <button onClick={handleConfirmHumanGate} disabled={humanGateLoading} className={`px-6 py-2.5 rounded-lg text-sm font-['Figtree'] font-medium ${humanGateLoading ? "bg-gray-200 text-gray-500" : "bg-[#A8C3A0] text-[#1B2E1B] hover:bg-[#98B890]"}`}>
                {humanGateLoading ? "Confirming..." : "Confirm Human Gate"}
              </button>
            </div>
          </div>
        </div>
      )}

      {showDocumentModal && selectedDocument && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full">
            <div className="flex items-center justify-between p-6 border-b border-[#E8ECE7]">
              <div>
                <h3 className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B]">{selectedDocument.name}</h3>
                <p className="font-['Figtree'] text-sm text-[#6B7568]">{selectedDocument.uploadDate ? `Uploaded: ${selectedDocument.uploadDate}` : "Encrypted at rest"}</p>
              </div>
              <button onClick={() => setShowDocumentModal(false)} className="p-2 rounded-lg hover:bg-[#F0F5EE] transition-colors">
                <X className="w-5 h-5 text-[#6B7568]" />
              </button>
            </div>
            <div className="p-6">
              <div className="bg-[#F8FAF7] rounded-xl p-8 text-center border-2 border-dashed border-[#E5EAE3]">
                <FileText className="w-16 h-16 text-[#6B7568] mx-auto mb-4" />
                <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">{selectedDocument.fileName}</p>
                <p className="font-['Figtree'] text-xs text-[#6B7568] mt-1">{selectedDocument.fileSize} {selectedDocument.uploadDate ? `· ${selectedDocument.uploadDate}` : ""}</p>
                {selectedDocument.documentNumber && <p className="font-['Figtree'] text-xs text-[#6B7568] mt-1">Checksum: {selectedDocument.documentNumber}…</p>}
                <div className="mt-4 flex items-center justify-center gap-2">
                  <span className={`text-xs font-['Figtree'] px-2.5 py-1 rounded-full border ${getStatusBadgeColor(selectedDocument.status)}`}>{selectedDocument.status}</span>
                </div>
              </div>
            </div>
            <div className="flex items-center justify-end gap-3 p-6 border-t border-[#E8ECE7]">
              <button onClick={() => setShowDocumentModal(false)} className="px-4 py-2 font-['Figtree'] text-sm text-[#6B7568] hover:text-[#1B2E1B] transition-colors">Close</button>
              <button className="flex items-center gap-2 px-6 py-2.5 bg-[#A8C3A0] text-[#1B2E1B] font-['Figtree'] text-sm font-medium rounded-lg hover:bg-[#98B890] transition-colors">
                <Download className="w-4 h-4" />
                Download
              </button>
            </div>
          </div>
        </div>
      )}

      {isEditing && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b border-[#E8ECE7]">
              <h3 className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B]">Edit Profile</h3>
              <button onClick={handleCancel} className="p-2 rounded-lg hover:bg-[#F0F5EE] transition-colors">
                <X className="w-5 h-5 text-[#6B7568]" />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">Full Name</label>
                <input type="text" value={editForm.name} onChange={(e) => setEditForm({ ...editForm, name: e.target.value })} className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent" />
              </div>
              <div>
                <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">Business Name</label>
                <input type="text" value={editForm.business} onChange={(e) => setEditForm({ ...editForm, business: e.target.value })} className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent" />
              </div>
              <div>
                <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">Phone</label>
                <input type="text" value={editForm.phone} onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })} className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent" />
              </div>
              <div>
                <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">Email</label>
                <input type="email" value={editForm.email} onChange={(e) => setEditForm({ ...editForm, email: e.target.value })} className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent" />
              </div>
              <div>
                <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">Address</label>
                <textarea value={editForm.address} onChange={(e) => setEditForm({ ...editForm, address: e.target.value })} rows="2" className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent resize-none" />
              </div>
            </div>
            <div className="flex items-center justify-end gap-3 p-6 border-t border-[#E8ECE7]">
              <button onClick={handleCancel} className="px-4 py-2 font-['Figtree'] text-sm text-[#6B7568] hover:text-[#1B2E1B] transition-colors">Cancel</button>
              <button onClick={handleSave} className="flex items-center gap-2 px-6 py-2.5 bg-[#A8C3A0] text-[#1B2E1B] font-['Figtree'] text-sm font-medium rounded-lg hover:bg-[#98B890] transition-colors">
                <Save className="w-4 h-4" />
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}

      {showLogoutConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <LogOut className="w-8 h-8 text-red-600" />
              </div>
              <h3 className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B] mb-2">Logout Confirmation</h3>
              <p className="font-['Figtree'] text-sm text-[#6B7568] mb-6">Are you sure you want to logout? You will need to sign in again to access your account.</p>
              <div className="flex gap-3">
                <button onClick={() => setShowLogoutConfirm(false)} className="flex-1 px-4 py-2 border border-[#E5EAE3] text-[#6B7568] font-['Figtree'] font-medium rounded-lg hover:bg-[#F0F4EE] transition-colors">Cancel</button>
                <button onClick={handleLogout} className="flex-1 px-4 py-2 bg-red-600 text-white font-['Figtree'] font-medium rounded-lg hover:bg-red-700 transition-colors">Logout</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
}

export default Profile;
