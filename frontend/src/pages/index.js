import React, { useState } from 'react';
import { Search, MapPin, Sparkles, Loader2, ExternalLink, Zap } from 'lucide-react';

export default function Home() {
    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState("");
    const [resultLink, setResultLink] = useState("");
    const [industry, setIndustry] = useState("");
    const [location, setLocation] = useState("");

    const runScraper = async () => {
        if (!industry || !location) {
            setStatus("Please enter both industry and location");
            return;
        }

        setLoading(true);
        setStatus("🔄 Waking up server (this may take 50s on free tier)...");

        const API_URL = "https://b2b-scraper-4nme.onrender.com";

        try {
            const res = await fetch(`${API_URL}/api/run-lead-gen`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    industry: industry,
                    location: location,
                    limit: 50
                })
            });

            const data = await res.json();

            if (res.ok) {
                setStatus(`✅ Scraping ${industry} in ${location}... Check your sheet in 60s!`);
                setResultLink("https://docs.google.com/spreadsheets/u/0/");
            } else {
                setStatus("❌ Error: " + data.detail);
            }
        } catch (e) {
            setStatus("❌ Failed to connect. Is the server running?");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center p-6 relative">
            {/* Animated background orbs */}
            <div className="bg-orb bg-orb-1"></div>
            <div className="bg-orb bg-orb-2"></div>
            <div className="bg-orb bg-orb-3"></div>

            {/* Main card */}
            <div className="glass-card w-full max-w-lg p-8 md:p-10 relative z-10">
                {/* Header */}
                <div className="text-center mb-10">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-[#00f5a0] to-[#00d9f5] mb-6 shadow-lg shadow-[#00f5a0]/30">
                        <Zap className="w-8 h-8 text-black" />
                    </div>
                    <h1 className="text-3xl md:text-4xl font-bold text-white mb-3 tracking-tight">
                        Lead Finder
                    </h1>
                    <p className="text-gray-400 text-sm md:text-base">
                        Turn Google Maps into actionable leads in seconds
                    </p>
                </div>

                {/* Form */}
                <div className="space-y-5">
                    {/* Industry Input */}
                    <div>
                        <label className="floating-label">Industry / Business Type</label>
                        <div className="premium-input flex items-center">
                            <Search className="input-icon icon-green" />
                            <input
                                type="text"
                                value={industry}
                                onChange={(e) => setIndustry(e.target.value)}
                                placeholder="e.g. Dentists, Plumbers, Lawyers"
                            />
                        </div>
                    </div>

                    {/* Location Input */}
                    <div>
                        <label className="floating-label">Target Location</label>
                        <div className="premium-input flex items-center">
                            <MapPin className="input-icon icon-blue" />
                            <input
                                type="text"
                                value={location}
                                onChange={(e) => setLocation(e.target.value)}
                                placeholder="e.g. Miami, FL or Chicago"
                            />
                        </div>
                    </div>

                    {/* Submit Button */}
                    <button
                        onClick={runScraper}
                        disabled={loading}
                        className={`gradient-btn w-full flex items-center justify-center gap-3 mt-8 ${loading ? 'loading-pulse' : ''}`}
                    >
                        {loading ? (
                            <>
                                <Loader2 className="w-5 h-5 animate-spin" />
                                <span>Scraping...</span>
                            </>
                        ) : (
                            <>
                                <Sparkles className="w-5 h-5" />
                                <span>Find Leads</span>
                            </>
                        )}
                    </button>
                </div>

                {/* Status Terminal */}
                {status && (
                    <div className="terminal mt-8">
                        <p className={`text-sm ${status.includes('❌') ? 'text-red-400' : status.includes('✅') ? 'text-green-400' : 'text-yellow-400'}`}>
                            {status}
                        </p>
                        {resultLink && (
                            <a
                                href={resultLink}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-2 mt-3 text-[#00d9f5] hover:text-[#00f5a0] transition-colors text-sm"
                            >
                                <ExternalLink className="w-4 h-4" />
                                Open Google Sheets
                            </a>
                        )}
                    </div>
                )}

                {/* Footer */}
                <p className="text-center text-gray-600 text-xs mt-8">
                    Powered by Apify • Results delivered to Google Sheets
                </p>
            </div>
        </div>
    );
}
