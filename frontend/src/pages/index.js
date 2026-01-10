import React, { useState } from 'react';
import { Loader2, Sparkles, ExternalLink, CheckCircle } from 'lucide-react';

export default function Home() {
    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState("");
    const [sheetUrl, setSheetUrl] = useState("");
    const [industry, setIndustry] = useState("");
    const [location, setLocation] = useState("");

    const runScraper = async () => {
        if (!industry || !location) {
            setStatus("Please enter both fields");
            return;
        }

        setLoading(true);
        setSheetUrl("");
        setStatus("🔄 Connecting to server...");

        const API_URL = "https://b2b-scraper-4nme.onrender.com";

        try {
            // Update status during long wait
            const statusUpdates = [
                "🔄 Waking up server...",
                "🔄 Searching Google Maps...",
                "🔄 Processing results...",
                "🔄 Creating your spreadsheet..."
            ];

            let updateIndex = 0;
            const statusInterval = setInterval(() => {
                updateIndex = (updateIndex + 1) % statusUpdates.length;
                setStatus(statusUpdates[updateIndex]);
            }, 15000); // Update every 15 seconds

            const res = await fetch(`${API_URL}/api/run-lead-gen`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    industry: industry,
                    location: location,
                    limit: 50
                })
            });

            clearInterval(statusInterval);
            const data = await res.json();

            if (res.ok && data.sheet_url) {
                setStatus(`✅ Found leads for ${industry} in ${location}!`);
                setSheetUrl(data.sheet_url);
            } else if (data.status === "Error") {
                setStatus(`❌ ${data.message}`);
            } else {
                setStatus("❌ " + (data.detail || "Unknown error"));
            }
        } catch (e) {
            setStatus("❌ Connection failed. Server may be sleeping (wait 60s and retry).");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col items-center justify-center min-h-screen px-6 animate-fade-in">

            <div className="w-full max-w-[580px] flex flex-col gap-10">

                {/* Hero */}
                <div className="text-center space-y-4">
                    <h1 className="text-[48px] md:text-[56px] font-light tracking-tight text-[#edEEF0] leading-[1.05]">
                        Where should we start?
                    </h1>
                    <p className="text-[#8E8E93] text-lg font-light">
                        Verified B2B leads, generated in seconds.
                    </p>
                </div>

                {/* Form */}
                <div className="flex flex-col gap-5">

                    <div>
                        <label className="minimal-label">INDUSTRY / BUSINESS TYPE</label>
                        <input
                            type="text"
                            value={industry}
                            onChange={(e) => setIndustry(e.target.value)}
                            className="minimal-input"
                            placeholder="e.g. Dentists, SaaS, Plumbers"
                            disabled={loading}
                        />
                    </div>

                    <div>
                        <label className="minimal-label">TARGET LOCATION</label>
                        <input
                            type="text"
                            value={location}
                            onChange={(e) => setLocation(e.target.value)}
                            className="minimal-input"
                            placeholder="e.g. Austin, TX"
                            disabled={loading}
                        />
                    </div>

                    <div className="h-2"></div>

                    {/* Primary Button */}
                    <button
                        onClick={runScraper}
                        disabled={loading}
                        className="minimal-btn group"
                    >
                        {loading ? (
                            <>
                                <Loader2 className="w-5 h-5 animate-spin text-[#8E8E93]" />
                                <span className="text-[#edEEF0]">Finding leads (60-90s)...</span>
                            </>
                        ) : (
                            <>
                                <Sparkles className="w-5 h-5 text-[#8E8E93] group-hover:text-white transition-colors" />
                                <span>Find Leads</span>
                            </>
                        )}
                    </button>

                </div>

                {/* Status Message */}
                {status && (
                    <div className="text-center animate-fade-in">
                        <p className={`text-sm font-medium ${status.includes('❌') ? "text-red-400" : status.includes('✅') ? "text-green-400" : "text-[#edEEF0]"}`}>
                            {status}
                        </p>
                    </div>
                )}

                {/* Sheet URL - Big Prominent Button */}
                {sheetUrl && (
                    <div className="animate-fade-in">
                        <a
                            href={sheetUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center justify-center gap-3 w-full py-5 px-6 bg-green-600 hover:bg-green-500 rounded-xl text-white font-medium text-lg transition-all no-underline"
                        >
                            <CheckCircle className="w-6 h-6" />
                            <span>Open Your Results Spreadsheet</span>
                            <ExternalLink className="w-5 h-5" />
                        </a>
                        <p className="text-center text-[#8E8E93] text-xs mt-3">
                            This is your unique link. Bookmark it or share it!
                        </p>
                    </div>
                )}

            </div>

        </div>
    );
}
