// src/pages/SignUp.jsx — T3 verification stepper PAN→IEC→AD→ICEGATE→bank upfront + बाद में skips + GuidanceHint + Demo Skip (mocked fixtures)
import { useState, useEffect, useCallback } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { ArrowLeft, Store, ShoppingBag, Check, ChevronRight } from "lucide-react";
import { useData } from "../context/DataContext";
import { useHindi } from "../context/HindiContext";
import { getSignupGuidance } from "../services/api";
import { VerificationStepper, UPFRONT_ORDER, SKIPPABLE_FIELDS } from "../components/VerificationStepper";
import GuidanceHint from "../components/GuidanceHint";

const MOCK_FIXTURES = {
  pan: "ABCDE1234F",
  iec: "1234567890",
  ad_code: "12345678901234",
  ifsc: "SBIN0001234",
  bank_account: "123456789012",
  bank_name: "State Bank of India",
  bank_branch: "Jaipur Main",
  icegate: "ICEGATE-DEMO-001",
  gstin: "22ABCDE1234F1Z5",
};

function SignUp() {
  const navigate = useNavigate();
  const location = useLocation();
  const { signUp } = useData();
  const { hindiHelp, toggleHindiHelp } = useHindi();

  const [userType, setUserType] = useState(null);
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
    businessName: "",
    phone: "",
    address: "",
    // upfront verification fields — Required
    pan: "",
    iec: "",
    ad_code: "",
    icegate: "",
    bank_account: "",
    ifsc: "",
    bank_name: "",
    // skippable — बाद में
    gstin: "",
    udyam: "",
    rcmc: "",
  });

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);
  const [guidance, setGuidance] = useState(null);
  const [guidanceField, setGuidanceField] = useState(null);
  const [guidanceLoading, setGuidanceLoading] = useState(false);
  const [activeField, setActiveField] = useState(null);
  const [selectedStep, setSelectedStep] = useState("iec");
  const [skippableOpen, setSkippableOpen] = useState(false);
  const [demoCreds, setDemoCreds] = useState(null);
  const [demoTarget, setDemoTarget] = useState("/");
  const [copiedField, setCopiedField] = useState(null);

  const backgroundImageUrl =
    "https://plus.unsplash.com/premium_photo-1679811672048-9d4b810a7588?q=80&w=687&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D";

  const handleUserTypeSelect = (type) => {
    setUserType(type);
    setStep(2);
  };

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  // explicit hindi_help bool — never auto-detect
  const fetchGuidance = useCallback(
    async (field) => {
      if (!field) return;
      setGuidanceField(field);
      setActiveField(field);
      setGuidanceLoading(true);
      try {
        // MUST pass explicit boolean hindiHelp, no auto-detect
        if (typeof hindiHelp !== "boolean") throw new Error("hindiHelp must be boolean");
        const data = await getSignupGuidance(field, hindiHelp);
        setGuidance(data);
      } catch {
        setGuidance(null);
      } finally {
        setGuidanceLoading(false);
      }
    },
    [hindiHelp]
  );

  useEffect(() => {
    const field = guidanceField || selectedStep || "iec";
    if (!field) return;
    if (!guidanceField && !guidance) return;
    let cancelled = false;
    (async () => {
      setGuidanceLoading(true);
      try {
        if (typeof hindiHelp !== "boolean") throw new Error("hindiHelp must be boolean");
        const data = await getSignupGuidance(field, hindiHelp);
        if (!cancelled) setGuidance(data);
      } catch {
        if (!cancelled) setGuidance(null);
      } finally {
        if (!cancelled) setGuidanceLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [hindiHelp]);

  const onFocusField = (field) => fetchGuidance(field);
  const onHoverField = (field) => fetchGuidance(field);
  const handleStepperSelect = (field) => {
    setSelectedStep(field);
    setActiveField(field);
    fetchGuidance(field);
  };

  useEffect(() => {
    if (userType === "seller" && step === 2 && !guidanceField && !guidance && !guidanceLoading) {
      fetchGuidance(selectedStep || "iec");
    }
  }, [userType, step, guidanceField, guidance, guidanceLoading, selectedStep, fetchGuidance]);

  const completedFields = [
    ...(formData.pan.trim().length >= 10 ? ["pan"] : []),
    ...(formData.iec.trim().length >= 10 ? ["iec"] : []),
    ...(formData.ad_code.trim().length >= 14 ? ["ad_code"] : []),
    ...(formData.icegate.trim().length >= 3 ? ["icegate"] : []),
    ...(formData.bank_account.trim().length >= 6 && formData.ifsc.trim().length >= 8 ? ["bank"] : []),
    ...(formData.gstin.trim().length >= 5 ? ["gstin"] : []),
    ...(formData.udyam.trim().length >= 3 ? ["udyam"] : []),
    ...(formData.rcmc.trim().length >= 3 ? ["rcmc"] : []),
  ];

  const handleCopy = async (field, value) => {
    try {
      await navigator.clipboard.writeText(value);
      setCopiedField(field);
      setTimeout(() => setCopiedField(null), 1500);
    } catch {
      void 0;
    }
  };

  const handleDemoContinue = () => {
    navigate(demoTarget);
  };

  const handleDemoDismiss = () => {
    setDemoCreds(null);
  };

  const handleDemoSkip = async () => {
    setError("");
    setDemoLoading(true);
    try {
      const ts = Date.now().toString().slice(-6);
      const email = `demo_${ts}_${Math.floor(Math.random()*1000).toString().padStart(3,"0")}@test.in`;
      const password = "DemoPass123!";
      const name = "Demo Seller";
      const businessName = "Demo Handicrafts";
      const demoType = userType || "seller";
      const roleForBackend = demoType === "dnk" ? "sahayak" : demoType;
      const uniqueTs = Date.now().toString();
      const iecUnique = `1${uniqueTs.slice(-9).padStart(9,"0")}`;
      const panNum = uniqueTs.slice(-4).padStart(4,"0");
      const panLetter = String.fromCharCode(65 + (parseInt(uniqueTs.slice(-2),10)%26));
      const panUnique = `ABCDE${panNum}${panLetter}`;

      const regRes = await fetch("/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, role: roleForBackend }),
      });
      if (!regRes.ok) {
        const d = await regRes.json().catch(() => ({}));
        const detail = typeof d.detail === "string" ? d.detail : (d.detail?.message || JSON.stringify(d.detail || {}));
        throw new Error(detail || d.message || `Demo register failed: ${regRes.status}`);
      }

      const loginRes = await fetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!loginRes.ok) {
        const d = await loginRes.json().catch(() => ({}));
        const detail = typeof d.detail === "string" ? d.detail : (d.detail?.message || JSON.stringify(d.detail || {}));
        throw new Error(detail || d.message || `Demo login failed: ${loginRes.status}`);
      }
      const loginData = await loginRes.json();
      const accessToken = loginData.access_token;
      const refreshToken = loginData.refresh_token;

      try {
        localStorage.setItem("token", accessToken);
        localStorage.setItem("access_token", accessToken);
        if (refreshToken) localStorage.setItem("refresh_token", refreshToken);
        const u = loginData.user || { id: `demo-${ts}`, email, role: roleForBackend };
        const frontType = u.role === "sahayak" ? "dnk" : u.role || demoType;
        localStorage.setItem(
          "user",
          JSON.stringify({ id: u.id, email: u.email || email, role: u.role || roleForBackend, userType: frontType, name, businessName, token: accessToken, refresh_token: refreshToken })
        );
      } catch {
        // ignore storage errors
      }

      const makePayload = (iecVal, panVal) => ({
        firm_name: businessName,
        owner_name: name,
        pan: panVal,
        iec: iecVal,
        ad_code: MOCK_FIXTURES.ad_code,
        bank_account: MOCK_FIXTURES.bank_account,
        ifsc: MOCK_FIXTURES.ifsc,
        bank_name: MOCK_FIXTURES.bank_name,
        bank_branch: MOCK_FIXTURES.bank_branch,
        address_line1: "12 Demo Lane",
        city: "Jaipur",
        state: "Rajasthan",
        pincode: "302001",
        phone: "9876543210",
      });
      let profOk = false;
      let lastDetail = "";
      for (let attempt = 0; attempt < 3 && !profOk; attempt++) {
        const iecTry = attempt === 0 ? iecUnique : `1${(Date.now()+attempt).toString().slice(-9).padStart(9,"0")}`;
        const panTry = attempt === 0 ? panUnique : `ABCDE${(Date.now()+attempt).toString().slice(-4).padStart(4,"0")}F`;
        const profilePayload = makePayload(iecTry, panTry);
        const profRes = await fetch("/profile", {
          method: "POST",
          headers: { "Content-Type": "application/json", Authorization: `Bearer ${accessToken}` },
          body: JSON.stringify(profilePayload),
        });
        if (profRes.ok || profRes.status === 409) { profOk = true; break; }
        const d = await profRes.json().catch(() => ({}));
        lastDetail = typeof d.detail === "string" ? d.detail : JSON.stringify(d.detail || d.message || d);
        const isDuplicate = profRes.status === 422 || profRes.status === 500 || /duplicate|iec|unique|already exists/i.test(lastDetail);
        if (isDuplicate && attempt < 2) continue;
        console.warn("Demo profile POST warning:", d);
        if (profRes.status !== 409) {
          try {
            const putRes = await fetch("/profile", { method: "PUT", headers: { "Content-Type": "application/json", Authorization: `Bearer ${accessToken}` }, body: JSON.stringify(profilePayload) });
            if (putRes.ok) profOk = true;
          } catch { void 0; }
        }
        break;
      }
      if (!profOk && lastDetail && /duplicate|iec/i.test(lastDetail)) {
        console.warn("Demo profile duplicate IEC after retries:", lastDetail);
      }

      try {
        await fetch("/verify/l2", {
          method: "POST",
          headers: { "Content-Type": "application/json", Authorization: `Bearer ${accessToken}` },
          body: JSON.stringify({
            iec: iecUnique,
            ad_code: MOCK_FIXTURES.ad_code,
            bank_account: MOCK_FIXTURES.bank_account,
            ifsc: MOCK_FIXTURES.ifsc,
          }),
        });
      } catch {
        // ignore — mock only
      }

      const frontTypeFinal = roleForBackend === "sahayak" ? "dnk" : roleForBackend;
      const targetPath =
        frontTypeFinal === "seller"
          ? "/seller/voice"
          : frontTypeFinal === "buyer"
            ? "/marketplace"
            : frontTypeFinal === "dnk"
              ? "/dnk/dashboard"
              : "/";
      setDemoCreds({ email, password });
      setDemoTarget(targetPath);
    } catch (err) {
      const raw = err?.detail || err?.message || String(err) || "Demo Skip failed";
      const msg = typeof raw === "string" ? raw : JSON.stringify(raw);
      setError(msg);
    } finally {
      setDemoLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (formData.password !== formData.confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    if (formData.password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    // seller must fill upfront order (Required)
    if (userType === "seller") {
      if (!formData.pan.trim()) { setError("PAN is required (Required)"); return; }
      if (!formData.iec.trim()) { setError("IEC is required (Required)"); return; }
      if (!formData.ad_code.trim()) { setError("AD Code is required (Required)"); return; }
      if (!formData.icegate.trim()) { setError("ICEGATE is required (Required)"); return; }
      if (!formData.bank_account.trim() || !formData.ifsc.trim()) { setError("Bank account + IFSC are required (Required)"); return; }
    }
    setLoading(true);
    try {
      const payload = {
        email: formData.email.trim(),
        password: formData.password,
        name: formData.name.trim(),
        businessName: formData.businessName.trim(),
        phone: formData.phone.trim(),
        userType: userType,
        role: userType,
      };
      const result = await signUp(payload);

      // If seller, attempt to create profile with entered verification data (mocked path)
      if (userType === "seller" && result?.access_token) {
        const token = result.access_token;
        const profilePayload = {
          firm_name: formData.businessName.trim() || "My Firm",
          owner_name: formData.name.trim(),
          pan: formData.pan.trim() || undefined,
          iec: formData.iec.trim() || undefined,
          ad_code: formData.ad_code.trim() || undefined,
          bank_account: formData.bank_account.trim() || undefined,
          ifsc: formData.ifsc.trim() || undefined,
          bank_name: formData.bank_name.trim() || undefined,
          gstin: formData.gstin.trim() || undefined,
          address_line1: formData.address?.trim() || undefined,
          city: undefined,
          state: undefined,
          pincode: undefined,
          phone: formData.phone.trim() || undefined,
        };
        // remove empties
        Object.keys(profilePayload).forEach((k) => profilePayload[k] === undefined && delete profilePayload[k]);
        try {
          await fetch("/profile", {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify(profilePayload),
          });
        } catch {
          // ignore — profile create is best-effort here
        }
      }

      const next = new URLSearchParams(location.search).get("next");
      if (next) { navigate(next); return; }
      const frontType = result?.user?.userType || userType;
      if (frontType === "seller") navigate("/seller/voice");
      else if (frontType === "buyer") navigate("/marketplace");
      else if (frontType === "dnk" || frontType === "sahayak") navigate("/dnk/dashboard");
      else navigate("/");
    } catch (err) {
      const msg = err?.detail || err?.message || "Registration failed";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    if (step === 2) { setStep(1); setUserType(null); }
  };

  const inputBase = "w-full px-4 py-2.5 rounded-lg border font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent";

  return (
    <div
      className="min-h-screen bg-fixed"
      style={{ backgroundImage: `url(${backgroundImageUrl})`, backgroundSize: "cover", backgroundPosition: "center", backgroundRepeat: "no-repeat" }}
    >
      <div className="min-h-screen bg-black/50 flex">
        {/* Left branding */}
        <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-[#2D4A27]/90 via-[#3B5E34]/90 to-[#1F381A]/92 p-12 flex-col justify-between backdrop-blur-[2px]">
          <div>
            <h1 className="font-['Fraunces'] text-3xl font-semibold text-white">NiryatSaathi</h1>
            <p className="font-['Figtree'] text-white/80 mt-2">The Handmade Marketplace</p>
          </div>
          <div>
            <h2 className="font-['Fraunces'] text-4xl font-semibold text-white leading-tight">Join India&apos;s<br />Handmade Community</h2>
            <p className="font-['Figtree'] text-white/80 mt-4 max-w-md">Connect with artisans, discover unique products, and grow your handmade business.</p>
            <div className="flex items-center gap-8 mt-8">
              <div><p className="font-['Fraunces'] text-2xl font-semibold text-white">500+</p><p className="font-['Figtree'] text-sm text-white/80">Artisans</p></div>
              <div><p className="font-['Fraunces'] text-2xl font-semibold text-white">40+</p><p className="font-['Figtree'] text-sm text-white/80">Countries</p></div>
              <div><p className="font-['Fraunces'] text-2xl font-semibold text-white">10k+</p><p className="font-['Figtree'] text-sm text-white/80">Products</p></div>
            </div>
          </div>
          <div className="flex items-center gap-2"><span className="font-['Figtree'] text-sm text-white/60">© 2026 NiryatSaathi</span></div>
        </div>

        {/* Right form */}
        <div className="w-full lg:w-1/2 flex items-center justify-center p-4 sm:p-8">
          <div className="w-full max-w-xl bg-white/95 backdrop-blur-sm rounded-2xl p-6 sm:p-8 shadow-xl max-h-[95vh] overflow-y-auto">
            {step === 2 && (
              <button onClick={handleBack} className="flex items-center gap-2 font-['Figtree'] text-sm text-[#6B7568] hover:text-[#1B2E1B] transition-colors mb-4">
                <ArrowLeft className="w-4 h-4" /> Back
              </button>
            )}

            {step === 1 ? (
              <div>
                <div className="text-center mb-8">
                  <h2 className="font-['Fraunces'] text-2xl font-semibold text-[#1B2E1B]">Create Your Account</h2>
                  <p className="font-['Figtree'] text-[#6B7568] mt-2">Choose how you want to use NiryatSaathi</p>
                </div>
                <div className="space-y-4">
                  <button onClick={() => handleUserTypeSelect("seller")} className="w-full p-6 bg-white rounded-xl border-2 border-[#E5EAE3] hover:border-[#A8C3A0] transition-all text-left group">
                    <div className="flex items-start gap-4">
                      <div className="p-3 bg-[#E8F0E6] rounded-lg group-hover:bg-[#A8C3A0] transition-colors"><Store className="w-6 h-6 text-[#6FAF6F] group-hover:text-white transition-colors" /></div>
                      <div className="flex-1">
                        <h3 className="font-['Figtree'] text-lg font-semibold text-[#1B2E1B]">I&apos;m a Seller</h3>
                        <p className="font-['Figtree'] text-sm text-[#6B7568] mt-1">Sell handmade products, manage orders, and grow your business</p>
                        <div className="flex items-center gap-4 mt-3">
                          <span className="text-xs font-['Figtree'] text-[#6FAF6F] flex items-center gap-1"><Check className="w-3.5 h-3.5" />List products</span>
                          <span className="text-xs font-['Figtree'] text-[#6FAF6F] flex items-center gap-1"><Check className="w-3.5 h-3.5" />Manage orders</span>
                          <span className="text-xs font-['Figtree'] text-[#6FAF6F] flex items-center gap-1"><Check className="w-3.5 h-3.5" />Reach global buyers</span>
                        </div>
                      </div>
                      <ChevronRight className="w-5 h-5 text-[#6B7568] group-hover:text-[#6FAF6F] transition-colors" />
                    </div>
                  </button>
                  <button onClick={() => handleUserTypeSelect("buyer")} className="w-full p-6 bg-white rounded-xl border-2 border-[#E5EAE3] hover:border-[#A8C3A0] transition-all text-left group">
                    <div className="flex items-start gap-4">
                      <div className="p-3 bg-[#E8F0E6] rounded-lg group-hover:bg-[#A8C3A0] transition-colors"><ShoppingBag className="w-6 h-6 text-[#6FAF6F] group-hover:text-white transition-colors" /></div>
                      <div className="flex-1">
                        <h3 className="font-['Figtree'] text-lg font-semibold text-[#1B2E1B]">I&apos;m a Buyer</h3>
                        <p className="font-['Figtree'] text-sm text-[#6B7568] mt-1">Discover unique handmade products from artisans across India</p>
                        <div className="flex items-center gap-4 mt-3">
                          <span className="text-xs font-['Figtree'] text-[#6FAF6F] flex items-center gap-1"><Check className="w-3.5 h-3.5" />Browse products</span>
                          <span className="text-xs font-['Figtree'] text-[#6FAF6F] flex items-center gap-1"><Check className="w-3.5 h-3.5" />Order handmade</span>
                          <span className="text-xs font-['Figtree'] text-[#6FAF6F] flex items-center gap-1"><Check className="w-3.5 h-3.5" />Support artisans</span>
                        </div>
                      </div>
                      <ChevronRight className="w-5 h-5 text-[#6B7568] group-hover:text-[#6FAF6F] transition-colors" />
                    </div>
                  </button>
                </div>
                <div className="mt-6 text-center">
                  <p className="font-['Figtree'] text-sm text-[#6B7568]">Already have an account? <button onClick={() => navigate("/signin")} className="text-[#6FAF6F] hover:text-[#5A9A5A] font-medium transition-colors">Sign In</button></p>
                </div>
              </div>
            ) : (
              <div>
                <div className="text-center mb-4">
                  <h2 className="font-['Fraunces'] text-2xl font-semibold text-[#1B2E1B]">{userType === "seller" ? "Seller Sign Up" : "Buyer Sign Up"}</h2>
                  <p className="font-['Figtree'] text-[#6B7568] mt-2 text-sm">{userType === "seller" ? "PAN → IEC → AD → ICEGATE → Bank upfront · GSTIN/Udyam/RCMC बाद में" : "Create your buyer account and start shopping"}</p>
                </div>

                {error && <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-sm font-['Figtree'] text-red-700" role="alert">{error}</div>}

                {/* Hindi help toggle — explicit bool, no auto-detect */}
                <div className="flex justify-end mb-3">
                  <label className="inline-flex items-center gap-2 cursor-pointer">
                    <span className="font-['Figtree'] text-sm text-[#1B2E1B]">हिन्दी में मदद चाहिए?</span>
                    <button type="button" role="switch" aria-checked={hindiHelp} onClick={toggleHindiHelp} data-testid="hindi-toggle" className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${hindiHelp ? "bg-[#1B2E1B]" : "bg-[#E5EAE3]"}`}>
                      <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${hindiHelp ? "translate-x-4" : "translate-x-1"}`} />
                    </button>
                  </label>
                </div>

                {demoCreds && (
                  <div data-testid="demo-creds" className="mb-4 p-4 rounded-lg bg-emerald-50 border border-emerald-200 text-sm font-['Figtree'] text-emerald-800">
                    <p className="font-semibold">Demo account created — save your credentials</p>
                    <p className="text-xs text-emerald-700 mt-1">Stays visible until you continue. Copy before leaving.</p>
                    <div className="mt-3 space-y-2">
                      <div className="flex items-center justify-between gap-2 bg-white rounded-lg px-3 py-2 border border-emerald-200">
                        <div className="min-w-0 flex-1">
                          <p className="text-[10px] tracking-widest uppercase text-emerald-600">Email</p>
                          <p className="font-mono text-sm text-[#1B2E1B] truncate" data-testid="demo-email">{demoCreds.email}</p>
                        </div>
                        <button type="button" onClick={() => handleCopy("email", demoCreds.email)} data-testid="copy-email" className="shrink-0 px-3 py-1.5 rounded-md bg-[#1B2E1B] text-white text-xs font-medium hover:bg-[#2D4A27] transition-colors">
                          {copiedField === "email" ? "Copied!" : "Copy"}
                        </button>
                      </div>
                      <div className="flex items-center justify-between gap-2 bg-white rounded-lg px-3 py-2 border border-emerald-200">
                        <div className="min-w-0 flex-1">
                          <p className="text-[10px] tracking-widest uppercase text-emerald-600">Password</p>
                          <p className="font-mono text-sm text-[#1B2E1B] truncate" data-testid="demo-password">{demoCreds.password}</p>
                        </div>
                        <button type="button" onClick={() => handleCopy("password", demoCreds.password)} data-testid="copy-password" className="shrink-0 px-3 py-1.5 rounded-md bg-[#1B2E1B] text-white text-xs font-medium hover:bg-[#2D4A27] transition-colors">
                          {copiedField === "password" ? "Copied!" : "Copy"}
                        </button>
                      </div>
                    </div>
                    <div className="mt-3 flex gap-2">
                      <button type="button" onClick={handleDemoContinue} data-testid="demo-continue" className="flex-1 px-4 py-2.5 rounded-lg bg-[#1B2E1B] text-white text-sm font-medium hover:bg-[#2D4A27] transition-colors">
                        Continue
                      </button>
                      <button type="button" onClick={handleDemoDismiss} data-testid="demo-dismiss" className="px-4 py-2.5 rounded-lg bg-white border border-emerald-200 text-emerald-800 text-sm font-medium hover:bg-emerald-100 transition-colors">
                        Dismiss
                      </button>
                    </div>
                  </div>
                )}

                <VerificationStepper
                  currentField={activeField || selectedStep}
                  completedFields={completedFields}
                  collapsedOpen={skippableOpen}
                  onToggleCollapsed={() => setSkippableOpen((v) => !v)}
                  onSelectField={handleStepperSelect}
                />

                {userType === "seller" && step === 2 && (() => {
                  const displayField = guidanceField || activeField || selectedStep || "iec";
                  const displayGuidance = guidance;
                  const showHint = guidanceLoading || !!displayGuidance;
                  return showHint ? (
                    <div className="mb-4">
                      <GuidanceHint key={`${displayField}-${String(hindiHelp)}`} guidance={displayGuidance} field={displayField} loading={guidanceLoading} />
                      <p className="font-['Figtree'] text-[10px] text-[#6B7568] mt-1">GET /guidance/signup?field={displayField}&hindi_help={String(hindiHelp)} — explicit bool (no auto-detect)</p>
                    </div>
                  ) : (
                    <div className="mb-4">
                      <GuidanceHint key={`${displayField}-${String(hindiHelp)}-empty`} guidance={null} field={displayField} loading={true} />
                    </div>
                  );
                })()}

                {/* Demo Skip — auto POST /auth/register + POST /profile with mocked fixtures without manual entry */}
                <div className="mb-4 p-3 rounded-xl border border-dashed border-[#A8C3A0] bg-[#F8FAF7] flex flex-col sm:flex-row items-center justify-between gap-3">
                  <div className="text-left">
                    <p className="font-['Figtree'] text-sm font-semibold text-[#1B2E1B]">Demo? Skip verification</p>
                    <p className="font-['Figtree'] text-xs text-[#6B7568]">Auto-creates account + profile with mocked PAN/AD/bank (verification-service mock, no typing).</p>
                  </div>
                  <button
                    type="button"
                    data-testid="demo-skip"
                    aria-label="Demo Skip — auto register and profile with mocked fixtures"
                    onClick={handleDemoSkip}
                    disabled={demoLoading || loading}
                    className="shrink-0 px-5 py-2.5 rounded-lg bg-[#1B2E1B] text-white font-['Figtree'] text-sm font-medium hover:bg-[#2D4A27] transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                  >
                    {demoLoading ? "Creating demo..." : "Demo Skip"}
                  </button>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                  {/* Base fields */}
                  <div>
                    <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">Full Name *</label>
                    <input type="text" name="name" value={formData.name} onChange={handleInputChange} placeholder="Enter your full name" required className={`${inputBase} border-[#E5EAE3]`} />
                  </div>
                  <div>
                    <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">Email Address *</label>
                    <input type="email" name="email" value={formData.email} onChange={handleInputChange} placeholder="Enter your email" required className={`${inputBase} border-[#E5EAE3]`} />
                  </div>
                  <div>
                    <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">Password *</label>
                    <input type="password" name="password" value={formData.password} onChange={handleInputChange} placeholder="Create a password (min 8 characters)" required minLength={8} className={`${inputBase} border-[#E5EAE3]`} />
                  </div>
                  <div>
                    <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">Confirm Password *</label>
                    <input type="password" name="confirmPassword" value={formData.confirmPassword} onChange={handleInputChange} placeholder="Confirm your password" required className={`${inputBase} border-[#E5EAE3]`} />
                  </div>
                  {userType === "seller" && (
                    <div>
                      <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">Business Name *</label>
                      <input type="text" name="businessName" value={formData.businessName} onChange={handleInputChange} placeholder="Enter your business name" required className={`${inputBase} border-[#E5EAE3]`} />
                    </div>
                  )}
                  <div>
                    <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">Phone Number</label>
                    <input type="tel" name="phone" value={formData.phone} onChange={handleInputChange} placeholder="Enter your phone number" className={`${inputBase} border-[#E5EAE3]`} />
                  </div>

                  {/* Seller verification fields — _UPFRONT_ORDER PAN→IEC→AD→ICEGATE→bank (Required) */}
                  {userType === "seller" && (
                    <>
                      <div className="pt-2 border-t border-[#E5EAE3]">
                        <p className="font-['Figtree'] text-xs font-semibold tracking-widest text-[#1B2E1B] uppercase mb-3">Verification Details — Required upfront</p>

                        {/* PAN */}
                        <div className="mb-4">
                          <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">PAN <span className="text-red-600">*</span> <span className="text-[10px] font-normal text-[#6B7568] ml-1">Required</span></label>
                          <input
                            type="text" name="pan" value={formData.pan} onChange={handleInputChange}
                            onFocus={() => onFocusField("pan")} onMouseEnter={() => onHoverField("pan")}
                            placeholder="ABCDE1234F" maxLength={10}
                            data-testid="input-pan"
                            className={`${inputBase} border-[#E5EAE3]`}
                          />
                        </div>

                        {/* IEC */}
                        <div className="mb-4">
                          <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">IEC (Import Export Code) <span className="text-red-600">*</span> <span className="text-[10px] font-normal text-[#6B7568] ml-1">Required</span></label>
                          <input
                            type="text" name="iec" value={formData.iec} onChange={handleInputChange}
                            onFocus={() => onFocusField("iec")} onMouseEnter={() => onHoverField("iec")}
                            placeholder="1234567890" maxLength={10}
                            data-testid="input-iec"
                            className={`${inputBase} border-[#E5EAE3]`}
                          />
                        </div>

                        {/* AD Code */}
                        <div className="mb-4">
                          <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">AD Code (14 digits) <span className="text-red-600">*</span> <span className="text-[10px] font-normal text-[#6B7568] ml-1">Required</span></label>
                          <input
                            type="text" name="ad_code" value={formData.ad_code} onChange={handleInputChange}
                            onFocus={() => onFocusField("ad_code")} onMouseEnter={() => onHoverField("ad_code")}
                            placeholder="12345678901234" maxLength={14}
                            data-testid="input-ad_code"
                            className={`${inputBase} border-[#E5EAE3]`}
                          />
                        </div>

                        {/* ICEGATE */}
                        <div className="mb-4">
                          <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">ICEGATE ID <span className="text-red-600">*</span> <span className="text-[10px] font-normal text-[#6B7568] ml-1">Required</span></label>
                          <input
                            type="text" name="icegate" value={formData.icegate} onChange={handleInputChange}
                            onFocus={() => onFocusField("icegate")} onMouseEnter={() => onHoverField("icegate")}
                            placeholder="ICEGATE-DEMO-001"
                            data-testid="input-icegate"
                            className={`${inputBase} border-[#E5EAE3]`}
                          />
                        </div>

                        {/* Bank upfront */}
                        <div className="mb-2">
                          <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">Bank Account <span className="text-red-600">*</span> <span className="text-[10px] font-normal text-[#6B7568] ml-1">Required</span></label>
                          <input
                            type="text" name="bank_account" value={formData.bank_account} onChange={handleInputChange}
                            onFocus={() => onFocusField("bank")} onMouseEnter={() => onHoverField("bank")}
                            placeholder="123456789012" data-testid="input-bank"
                            className={`${inputBase} border-[#E5EAE3]`}
                          />
                        </div>
                        <div className="grid grid-cols-2 gap-3 mb-4">
                          <div>
                            <label className="block font-['Figtree'] text-xs font-medium text-[#1B2E1B] mb-1">IFSC <span className="text-red-600">*</span></label>
                            <input
                              type="text" name="ifsc" value={formData.ifsc} onChange={handleInputChange}
                              onFocus={() => onFocusField("bank")} onMouseEnter={() => onHoverField("bank")}
                              placeholder="SBIN0001234" data-testid="input-ifsc"
                              className={`${inputBase} border-[#E5EAE3] text-xs`}
                            />
                          </div>
                          <div>
                            <label className="block font-['Figtree'] text-xs font-medium text-[#1B2E1B] mb-1">Bank Name</label>
                            <input type="text" name="bank_name" value={formData.bank_name} onChange={handleInputChange} placeholder="State Bank of India" className={`${inputBase} border-[#E5EAE3] text-xs`} />
                          </div>
                        </div>

                        {/* Skippable — GSTIN / Udyam / RCMC collapsed */}
                        <div className="rounded-lg border border-dashed border-[#E5EAE3] bg-[#F8FAF7] p-3">
                          <button type="button" onClick={() => setSkippableOpen((v) => !v)} aria-expanded={skippableOpen} data-testid="skippable-form-toggle" className="w-full text-left font-['Figtree'] text-sm font-medium text-[#1B2E1B] flex items-center justify-between">
                            <span>बाद में — Optional (GSTIN / Udyam / RCMC) — Skip for now</span>
                            <span className="text-xs text-[#6B7568]">{skippableOpen ? "▲ Hide" : "▼ Show"}</span>
                          </button>
                          {skippableOpen && (
                            <div className="mt-3 space-y-3" data-testid="skippable-form-fields">
                              <div>
                                <label className="block font-['Figtree'] text-xs font-medium text-[#1B2E1B] mb-1">GSTIN <span className="text-[10px] font-normal text-[#6B7568]">बाद में — skip allowed</span></label>
                                <input type="text" name="gstin" value={formData.gstin} onChange={handleInputChange} onFocus={() => onFocusField("gstin")} onMouseEnter={() => onHoverField("gstin")} placeholder="22ABCDE1234F1Z5" data-testid="input-gstin" className={`${inputBase} border-[#E5EAE3] text-xs`} />
                              </div>
                              <div>
                                <label className="block font-['Figtree'] text-xs font-medium text-[#1B2E1B] mb-1">Udyam <span className="text-[10px] font-normal text-[#6B7568]">बाद में — skip allowed</span></label>
                                <input type="text" name="udyam" value={formData.udyam} onChange={handleInputChange} onFocus={() => onFocusField("udyam")} onMouseEnter={() => onHoverField("udyam")} placeholder="UDYAM-XX-00-0000000" data-testid="input-udyam" className={`${inputBase} border-[#E5EAE3] text-xs`} />
                              </div>
                              <div>
                                <label className="block font-['Figtree'] text-xs font-medium text-[#1B2E1B] mb-1">RCMC <span className="text-[10px] font-normal text-[#6B7568]">बाद में — skip allowed</span></label>
                                <input type="text" name="rcmc" value={formData.rcmc} onChange={handleInputChange} onFocus={() => onFocusField("rcmc")} onMouseEnter={() => onHoverField("rcmc")} placeholder="RCMC-EPCH-... " data-testid="input-rcmc" className={`${inputBase} border-[#E5EAE3] text-xs`} />
                              </div>
                            </div>
                          )}
                          {!skippableOpen && <p className="font-['Figtree'] text-xs text-[#6B7568] mt-2">These 3 fields are skippable at signup — fill बाद में from Profile. Verification still mocked (mocked:true).</p>}
                        </div>
                      </div>
                    </>
                  )}

                  <button type="submit" disabled={loading || demoLoading} data-testid="create-account" className="w-full px-6 py-3 bg-[#A8C3A0] text-[#1B2E1B] font-['Figtree'] font-medium rounded-lg hover:bg-[#98B890] transition-colors disabled:opacity-60 disabled:cursor-not-allowed">
                    {loading ? "Creating account..." : "Create Account"}
                  </button>
                  <p className="text-center font-['Figtree'] text-xs text-[#6B7568]">By signing up, you agree to our <a href="#" className="text-[#6FAF6F] hover:text-[#5A9A5A] transition-colors">Terms of Service</a> and <a href="#" className="text-[#6FAF6F] hover:text-[#5A9A5A] transition-colors">Privacy Policy</a></p>
                </form>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default SignUp;
