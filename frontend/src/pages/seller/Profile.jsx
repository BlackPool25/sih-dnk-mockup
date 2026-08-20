// src/pages/seller/Profile.jsx
import { useState, useEffect } from "react";
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
  LogOut
} from "lucide-react";

function Profile() {
  const navigate = useNavigate();
  const { loadProfile, updateProfile, profile: apiProfile, loading, error } = useData();
  const [isEditing, setIsEditing] = useState(false);
  const [showDocumentModal, setShowDocumentModal] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState(null);
  
  // Get user data from localStorage
  const [userData, setUserData] = useState(() => {
    const stored = localStorage.getItem("user");
    return stored ? JSON.parse(stored) : { name: "Aarav Kumar", email: "aarav@kumarhandloom.in" };
  });

  // Local profile state - initialized from API or defaults
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

  const [documents, setDocuments] = useState([
    { 
      id: 1, 
      name: "IEC Certificate", 
      status: "Pending Verification", 
      uploaded: true,
      fileName: "iec_certificate.pdf",
      fileSize: "2.4 MB",
      uploadDate: "15 Jan 2026",
      documentNumber: "IECKU0012345"
    },
    { 
      id: 2, 
      name: "GSTIN Certificate", 
      status: "Verified", 
      uploaded: true,
      fileName: "gstin_certificate.pdf",
      fileSize: "1.8 MB",
      uploadDate: "15 Jan 2026",
      documentNumber: "09AABCK1234Z1Z5"
    },
    { 
      id: 3, 
      name: "AD Code Document", 
      status: "Verified", 
      uploaded: true,
      fileName: "ad_code_document.pdf",
      fileSize: "0.9 MB",
      uploadDate: "20 Jan 2026",
      documentNumber: "SBI001234567"
    },
    { 
      id: 4, 
      name: "LUT / Export Bond", 
      status: "Optional", 
      uploaded: false,
      fileName: null,
      fileSize: null,
      uploadDate: null,
      documentNumber: null
    },
  ]);

  const [editForm, setEditForm] = useState(profile);
  const [uploadingDoc, setUploadingDoc] = useState(null);

  // Load profile data from API on mount
  useEffect(() => {
    loadProfile().then((data) => {
      if (data) {
        setProfile(prev => ({
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
        setEditForm(prev => ({
          ...prev,
          name: data.name || prev.name,
          business: data.business || prev.business,
          phone: data.phone || prev.phone,
          email: data.email || prev.email,
          address: data.address || prev.address,
        }));
      }
    }).catch(console.error);
  }, []);

  // Update profile when user data changes in localStorage
  useEffect(() => {
    const stored = localStorage.getItem("user");
    if (stored) {
      const user = JSON.parse(stored);
      setProfile(prev => ({
        ...prev,
        name: user.name || prev.name,
        email: user.email || prev.email,
      }));
      setEditForm(prev => ({
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
    // Update profile state
    setProfile(editForm);
    
    // Update localStorage user data
    const stored = localStorage.getItem("user");
    if (stored) {
      const user = JSON.parse(stored);
      user.name = editForm.name;
      user.email = editForm.email;
      localStorage.setItem("user", JSON.stringify(user));
    }
    
    // Save to API
    try {
      await updateProfile(editForm);
      setIsEditing(false);
    } catch (err) {
      console.error("Error saving profile:", err);
      alert("Failed to save profile. Please try again.");
    }
  };

  const handleCancel = () => {
    setIsEditing(false);
  };

  const handleLogout = () => {
    localStorage.removeItem("user");
    localStorage.removeItem("token");
    navigate("/signin");
  };

  const extractDocumentNumber = (docName) => {
    const mockNumbers = {
      "IEC Certificate": "IECKU0012345",
      "GSTIN Certificate": "09AABCK1234Z1Z5",
      "AD Code Document": "SBI001234567",
      "LUT / Export Bond": null
    };
    return mockNumbers[docName] || null;
  };

  const updateProfileFromDocuments = (updatedDocs) => {
    const newProfile = { ...profile };
    
    updatedDocs.forEach(doc => {
      if (doc.status === "Verified" && doc.documentNumber) {
        switch(doc.name) {
          case "IEC Certificate":
            newProfile.iec = doc.documentNumber;
            break;
          case "GSTIN Certificate":
            newProfile.gstin = doc.documentNumber;
            break;
          case "AD Code Document":
            newProfile.adCode = doc.documentNumber;
            break;
          case "LUT / Export Bond":
            newProfile.lut = doc.documentNumber || "Submitted";
            break;
          default:
            break;
        }
      }
    });
    
    setProfile(newProfile);
  };

  const handleViewDocument = (doc) => {
    if (doc.uploaded) {
      setSelectedDocument(doc);
      setShowDocumentModal(true);
    }
  };

  const handleUploadDocument = (docId) => {
    setUploadingDoc(docId);
    setTimeout(() => {
      const updatedDocs = documents.map(doc => {
        if (doc.id === docId) {
          const docNumber = extractDocumentNumber(doc.name);
          const newStatus = doc.name === "LUT / Export Bond" ? "Verified" : "Pending Verification";
          return { 
            ...doc, 
            uploaded: true, 
            status: newStatus,
            fileName: `${doc.name.toLowerCase().replace(/\s/g, '_')}.pdf`,
            fileSize: "1.2 MB",
            uploadDate: new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }),
            documentNumber: docNumber
          };
        }
        return doc;
      });
      
      setDocuments(updatedDocs);
      updateProfileFromDocuments(updatedDocs);
      setUploadingDoc(null);
    }, 2000);
  };

  const handleVerifyDocument = (docId) => {
    const updatedDocs = documents.map(doc => {
      if (doc.id === docId && doc.uploaded) {
        return { 
          ...doc, 
          status: "Verified"
        };
      }
      return doc;
    });
    
    setDocuments(updatedDocs);
    updateProfileFromDocuments(updatedDocs);
  };

  const getStatusColor = (status) => {
    if (status === "Verified") return "text-green-600";
    if (status === "Pending Verification") return "text-amber-600";
    if (status === "Optional") return "text-[#6B7568]";
    return "text-[#6B7568]";
  };

  const getStatusIcon = (status) => {
    if (status === "Verified") return "✅";
    if (status === "Pending Verification") return "⏳";
    if (status === "Optional") return "📄";
    return "📄";
  };

  const getStatusBadgeColor = (status) => {
    if (status === "Verified") return "bg-green-100 text-green-700 border-green-200";
    if (status === "Pending Verification") return "bg-amber-100 text-amber-700 border-amber-200";
    if (status === "Optional") return "bg-gray-100 text-gray-600 border-gray-200";
    return "bg-gray-100 text-gray-600 border-gray-200";
  };

  const requiredDocs = documents.filter(d => d.name !== "LUT / Export Bond");
  const allVerified = requiredDocs.every(doc => doc.status === "Verified");
  const exportReady = allVerified;

  // Show loading state
  if (loading) {
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

  // Show error state
  if (error) {
    return (
      <Layout pageTitle="Seller Profile" pageSubtitle="Manage your account and export information.">
        <div className="flex items-center justify-center min-h-[300px]">
          <div className="text-center">
            <p className="font-['Figtree'] text-red-600">Error: {error}</p>
            <button 
              onClick={() => loadProfile()}
              className="mt-4 px-4 py-2 bg-[#A8C3A0] text-[#1B2E1B] rounded-lg font-['Figtree'] hover:bg-[#98B890] transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout pageTitle="Seller Profile" pageSubtitle="Manage your account and export information.">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Profile Card */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl border border-[#E1E7DF] overflow-hidden sticky top-6">
            {/* Header with Avatar */}
            <div className="bg-gradient-to-r from-[#E8F0E6] to-[#F0F7EE] p-6 text-center">
              <div className="w-24 h-24 rounded-full bg-[#A8C3A0] flex items-center justify-center mx-auto text-3xl font-['Fraunces'] font-semibold text-[#1B2E1B]">
                {profile.name.split(' ').map(n => n[0]).join('')}
              </div>
              <h2 className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B] mt-3">
                {profile.name}
              </h2>
              <p className="font-['Figtree'] text-sm text-[#6B7568]">
                Seller since {profile.since}
              </p>
              <div className="inline-flex items-center gap-1.5 mt-2 px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs font-['Figtree'] font-medium">
                <CheckCircle className="w-3.5 h-3.5" />
                Active
              </div>
            </div>

            {/* Profile Info */}
            <div className="p-4 space-y-4">
              <div>
                <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider">
                  Business
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <Briefcase className="w-4 h-4 text-[#6B7568]" />
                  <span className="font-['Figtree'] text-sm text-[#1B2E1B]">{profile.business}</span>
                </div>
              </div>
              <div>
                <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider">
                  Phone
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <Phone className="w-4 h-4 text-[#6B7568]" />
                  <span className="font-['Figtree'] text-sm text-[#1B2E1B]">{profile.phone}</span>
                </div>
              </div>
              <div>
                <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider">
                  Email
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <Mail className="w-4 h-4 text-[#6B7568]" />
                  <span className="font-['Figtree'] text-sm text-[#1B2E1B]">{profile.email}</span>
                </div>
              </div>
              <div>
                <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider">
                  Address
                </p>
                <div className="flex items-start gap-2 mt-1">
                  <MapPin className="w-4 h-4 text-[#6B7568] flex-shrink-0 mt-0.5" />
                  <span className="font-['Figtree'] text-sm text-[#1B2E1B]">{profile.address}</span>
                </div>
              </div>
              
              {/* Action Buttons */}
              <div className="space-y-2">
                <button
                  onClick={handleEdit}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 border border-[#E5EAE3] rounded-lg font-['Figtree'] text-sm text-[#1B2E1B] hover:bg-[#F8FAF7] transition-colors"
                >
                  <Edit className="w-4 h-4" />
                  Edit Profile
                </button>
                <button
                  onClick={() => setShowLogoutConfirm(true)}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 border border-red-200 rounded-lg font-['Figtree'] text-sm text-red-600 hover:bg-red-50 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  Logout
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column - Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Export Readiness */}
          <div className="bg-white rounded-xl border border-[#E1E7DF] p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B]">
                Export Readiness
              </h3>
              <span className={`text-xs font-['Figtree'] px-3 py-1 rounded-full border ${
                exportReady 
                  ? "bg-green-100 text-green-700 border-green-200" 
                  : "bg-amber-100 text-amber-700 border-amber-200"
              }`}>
                {exportReady ? "✅ Export setup ready" : "⏳ Pending verification"}
              </span>
            </div>
            <div className="flex flex-wrap gap-3">
              {documents.map(doc => (
                <span key={doc.id} className={`px-3 py-1.5 rounded-lg font-['Figtree'] text-sm border ${
                  doc.status === "Verified" 
                    ? "bg-green-50 text-green-700 border-green-200" 
                    : doc.status === "Pending Verification"
                    ? "bg-amber-50 text-amber-700 border-amber-200"
                    : "bg-gray-50 text-gray-500 border-gray-200"
                }`}>
                  {doc.name} {doc.status === "Verified" && "✅"}
                  {doc.status === "Pending Verification" && "⏳"}
                </span>
              ))}
            </div>
          </div>

          {/* Business & Export Details */}
          <div className="bg-white rounded-xl border border-[#E1E7DF] p-6">
            <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B] mb-4">
              Business & Export Details
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider">
                  IEC Number
                </p>
                <p className={`font-['Figtree'] text-sm font-medium mt-1 ${
                  profile.iec !== "Not available" ? "text-[#1B2E1B]" : "text-[#6B7568]"
                }`}>
                  {profile.iec}
                  {profile.iec !== "Not available" && (
                    <span className="ml-2 text-xs text-green-600">✅ Verified</span>
                  )}
                </p>
              </div>
              <div>
                <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider">
                  GSTIN
                </p>
                <p className={`font-['Figtree'] text-sm font-medium mt-1 ${
                  profile.gstin !== "Not available" ? "text-[#1B2E1B]" : "text-[#6B7568]"
                }`}>
                  {profile.gstin}
                  {profile.gstin !== "Not available" && (
                    <span className="ml-2 text-xs text-green-600">✅ Verified</span>
                  )}
                </p>
              </div>
              <div>
                <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider">
                  AD Code
                </p>
                <p className={`font-['Figtree'] text-sm font-medium mt-1 ${
                  profile.adCode !== "Not available" ? "text-[#1B2E1B]" : "text-[#6B7568]"
                }`}>
                  {profile.adCode}
                  {profile.adCode !== "Not available" && (
                    <span className="ml-2 text-xs text-green-600">✅ Verified</span>
                  )}
                </p>
              </div>
              <div>
                <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider">
                  LUT / Bond
                </p>
                <p className={`font-['Figtree'] text-sm font-medium mt-1 ${
                  profile.lut !== "Not submitted" ? "text-[#1B2E1B]" : "text-[#6B7568]"
                }`}>
                  {profile.lut}
                  {profile.lut !== "Not submitted" && profile.lut !== "Not available" && (
                    <span className="ml-2 text-xs text-green-600">✅ Verified</span>
                  )}
                </p>
              </div>
            </div>
            {!exportReady && (
              <div className="mt-4 p-3 bg-amber-50 rounded-lg border border-amber-200">
                <p className="font-['Figtree'] text-xs text-amber-700">
                  ⏳ Upload and verify all documents to complete your export profile.
                </p>
              </div>
            )}
            {exportReady && (
              <div className="mt-4 p-3 bg-green-50 rounded-lg border border-green-200">
                <p className="font-['Figtree'] text-xs text-green-700">
                  ✅ All documents verified. Your export profile is complete!
                </p>
              </div>
            )}
          </div>

          {/* Documents */}
          <div className="bg-white rounded-xl border border-[#E1E7DF] p-6">
            <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B] mb-4">
              Documents
            </h3>
            <div className="space-y-3">
              {documents.map((doc) => (
                <div key={doc.id} className="flex items-center justify-between py-2 border-b border-[#E8ECE7] last:border-0">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-[#F8FAF7] rounded-lg">
                      <File className="w-4 h-4 text-[#6B7568]" />
                    </div>
                    <div>
                      <p className="font-['Figtree'] text-sm text-[#1B2E1B]">{doc.name}</p>
                      <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                        <span className={`text-xs font-['Figtree'] ${getStatusColor(doc.status)}`}>
                          {getStatusIcon(doc.status)} {doc.status}
                        </span>
                        {doc.uploaded && (
                          <>
                            <span className="text-xs text-[#6B7568]">·</span>
                            <span className="text-xs text-[#6B7568]">{doc.fileName}</span>
                            <span className="text-xs text-[#6B7568]">·</span>
                            <span className="text-xs text-[#6B7568]">{doc.fileSize}</span>
                          </>
                        )}
                        {doc.documentNumber && doc.status === "Verified" && (
                          <>
                            <span className="text-xs text-[#6B7568]">·</span>
                            <span className="text-xs text-green-600">✅ {doc.documentNumber}</span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {doc.uploaded ? (
                      <>
                        <button
                          onClick={() => handleViewDocument(doc)}
                          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-['Figtree'] text-[#6B7568] hover:text-[#1B2E1B] transition-colors bg-[#F8FAF7] rounded-lg hover:bg-[#E8F0E6]"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          View
                        </button>
                        {doc.status === "Pending Verification" && (
                          <button
                            onClick={() => handleVerifyDocument(doc.id)}
                            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-['Figtree'] text-green-700 hover:text-green-800 transition-colors bg-green-50 rounded-lg hover:bg-green-100"
                          >
                            <CheckCircle className="w-3.5 h-3.5" />
                            Verify
                          </button>
                        )}
                      </>
                    ) : (
                      <button
                        onClick={() => handleUploadDocument(doc.id)}
                        disabled={uploadingDoc === doc.id}
                        className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-['Figtree'] font-medium rounded-lg transition-colors ${
                          uploadingDoc === doc.id
                            ? "bg-gray-200 text-gray-500 cursor-not-allowed"
                            : "bg-[#A8C3A0] text-[#1B2E1B] hover:bg-[#98B890]"
                        }`}
                      >
                        {uploadingDoc === doc.id ? (
                          <>
                            <span className="animate-spin rounded-full h-3 w-3 border-2 border-[#1B2E1B] border-t-transparent"></span>
                            Uploading...
                          </>
                        ) : (
                          <>
                            <Upload className="w-3.5 h-3.5" />
                            Upload
                          </>
                        )}
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Bank & Settlement */}
          <div className="bg-white rounded-xl border border-[#E1E7DF] p-6">
            <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B] mb-4">
              Bank & Settlement
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider">
                  Account
                </p>
                <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B] mt-1">
                  {profile.bankAccount}
                </p>
              </div>
              <div>
                <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider">
                  Holder
                </p>
                <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B] mt-1">
                  {profile.bankHolder}
                </p>
              </div>
              <div>
                <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider">
                  Bank
                </p>
                <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B] mt-1">
                  {profile.bankName}
                </p>
              </div>
              <div>
                <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider">
                  AD Code
                </p>
                <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B] mt-1">
                  {profile.bankAdCode}
                </p>
              </div>
            </div>
            <div className="mt-4 pt-4 border-t border-[#E8ECE7]">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs font-['Figtree'] font-medium">
                <CheckCircle className="w-3.5 h-3.5" />
                Linked
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Document View Modal - Same as before */}
      {showDocumentModal && selectedDocument && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full">
            <div className="flex items-center justify-between p-6 border-b border-[#E8ECE7]">
              <div>
                <h3 className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B]">
                  {selectedDocument.name}
                </h3>
                <p className="font-['Figtree'] text-sm text-[#6B7568]">
                  Uploaded: {selectedDocument.uploadDate}
                </p>
              </div>
              <button
                onClick={() => setShowDocumentModal(false)}
                className="p-2 rounded-lg hover:bg-[#F0F5EE] transition-colors"
              >
                <X className="w-5 h-5 text-[#6B7568]" />
              </button>
            </div>
            <div className="p-6">
              <div className="bg-[#F8FAF7] rounded-xl p-8 text-center border-2 border-dashed border-[#E5EAE3]">
                <FileText className="w-16 h-16 text-[#6B7568] mx-auto mb-4" />
                <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">
                  {selectedDocument.fileName}
                </p>
                <p className="font-['Figtree'] text-xs text-[#6B7568] mt-1">
                  {selectedDocument.fileSize} · {selectedDocument.uploadDate}
                </p>
                {selectedDocument.documentNumber && (
                  <p className="font-['Figtree'] text-xs text-[#6B7568] mt-1">
                    Document No: {selectedDocument.documentNumber}
                  </p>
                )}
                <div className="mt-4 flex items-center justify-center gap-2">
                  <span className={`text-xs font-['Figtree'] px-2.5 py-1 rounded-full border ${getStatusBadgeColor(selectedDocument.status)}`}>
                    {selectedDocument.status}
                  </span>
                </div>
              </div>
            </div>
            <div className="flex items-center justify-end gap-3 p-6 border-t border-[#E8ECE7]">
              <button
                onClick={() => setShowDocumentModal(false)}
                className="px-4 py-2 font-['Figtree'] text-sm text-[#6B7568] hover:text-[#1B2E1B] transition-colors"
              >
                Close
              </button>
              <button className="flex items-center gap-2 px-6 py-2.5 bg-[#A8C3A0] text-[#1B2E1B] font-['Figtree'] text-sm font-medium rounded-lg hover:bg-[#98B890] transition-colors">
                <Download className="w-4 h-4" />
                Download
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Profile Modal - Same as before */}
      {isEditing && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b border-[#E8ECE7]">
              <h3 className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B]">
                Edit Profile
              </h3>
              <button
                onClick={handleCancel}
                className="p-2 rounded-lg hover:bg-[#F0F5EE] transition-colors"
              >
                <X className="w-5 h-5 text-[#6B7568]" />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                  Full Name
                </label>
                <input
                  type="text"
                  value={editForm.name}
                  onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
                />
              </div>
              <div>
                <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                  Business Name
                </label>
                <input
                  type="text"
                  value={editForm.business}
                  onChange={(e) => setEditForm({ ...editForm, business: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
                />
              </div>
              <div>
                <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                  Phone
                </label>
                <input
                  type="text"
                  value={editForm.phone}
                  onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
                />
              </div>
              <div>
                <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                  Email
                </label>
                <input
                  type="email"
                  value={editForm.email}
                  onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
                />
              </div>
              <div>
                <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                  Address
                </label>
                <textarea
                  value={editForm.address}
                  onChange={(e) => setEditForm({ ...editForm, address: e.target.value })}
                  rows="2"
                  className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent resize-none"
                />
              </div>
            </div>
            <div className="flex items-center justify-end gap-3 p-6 border-t border-[#E8ECE7]">
              <button
                onClick={handleCancel}
                className="px-4 py-2 font-['Figtree'] text-sm text-[#6B7568] hover:text-[#1B2E1B] transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                className="flex items-center gap-2 px-6 py-2.5 bg-[#A8C3A0] text-[#1B2E1B] font-['Figtree'] text-sm font-medium rounded-lg hover:bg-[#98B890] transition-colors"
              >
                <Save className="w-4 h-4" />
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Logout Confirmation Modal - Same as before */}
      {showLogoutConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <LogOut className="w-8 h-8 text-red-600" />
              </div>
              <h3 className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B] mb-2">
                Logout Confirmation
              </h3>
              <p className="font-['Figtree'] text-sm text-[#6B7568] mb-6">
                Are you sure you want to logout? You will need to sign in again to access your account.
              </p>
              <div className="flex gap-3">
                <button
                  onClick={() => setShowLogoutConfirm(false)}
                  className="flex-1 px-4 py-2 border border-[#E5EAE3] text-[#6B7568] font-['Figtree'] font-medium rounded-lg hover:bg-[#F0F4EE] transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleLogout}
                  className="flex-1 px-4 py-2 bg-red-600 text-white font-['Figtree'] font-medium rounded-lg hover:bg-red-700 transition-colors"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
}

export default Profile;