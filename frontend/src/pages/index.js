import React, { useState } from 'react';
import { Loader2, ArrowRight, ExternalLink } from 'lucide-react';

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
        setStatus("Approaching server...");

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
                setStatus(`Search started for ${industry} in ${location}.`);
                setResultLink("https://docs.google.com/spreadsheets/u/0/");
            } else {
                setStatus("Error: " + data.detail);
            }
        } catch (e) {
            setStatus("Connection failed. Server may be sleeping.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex flex-col items-center justify-center p-6 animate-fade-in text-center">

            {/* Hero Section */}
            <div className="max-w-xl w-full mb-12">
                <h1 className="text-[42px] md:text-[52px] font-light tracking-tight text-[#edEEF0] mb-3 leading-[1.1]">
                    Where should we start?
                </h1>
                <p className="text-[#8E8E93] text-lg font-light">
                    Generate verified B2B leads in seconds.
                </p>
            </div>

            {/* Form Section */}
            <div className="w-full max-w-[400px] flex flex-col gap-6">

                {/* Input 1 */}
                <div className="text-left">
                    <label className="gemini-label">INDUSTRY / BUSINESS TYPE</label>
                    <input
                        type="text"
                        value={industry}
                        onChange={(e) => setIndustry(e.target.value)}
                        className="gemini-input"
                        placeholder="e.g. Dentists, SaaS, Plumbers"
                    />
                </div>

                {/* Input 2 */}
                <div className="text-left">
                    <label className="gemini-label">TARGET LOCATION</label>
                    <input
                        type="text"
                        value={location}
                        onChange={(e) => setLocation(e.target.value)}
                        className="gemini-input"
                        placeholder="e.g. Austin, TX"
                    />
                </div>

                {/* Spacer */}
                <div className="h-2"></div>

                {/* CTA Button */}
                <button
                    onClick={runScraper}
                    disabled={loading}
                    className="gemini-btn flex items-center justify-center gap-2"
                >
                    {loading ? (
                        <>
                            <Loader2 className="w-5 h-5 animate-spin" />
                            <span>Processing...</span>
                        </>
                    ) : (
                        <>
                            <span>Find Leads</span>
                            <ArrowRight className="w-4 h-4" />
                        </>
                    )}
                </button>

                {/* Minimal Status Message */}
                {status && (
                    <div className="mt-4 text-sm font-medium animate-fade-in">
                        <span className={status.includes('Error') || status.includes('failed') ? "text-red-400" : "text-[#edEEF0]"}>
                            {status}
                        </span>
                        {resultLink && (
                            <div className="mt-2">
                                <a
                                    href={resultLink}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-[#8E8E93] hover:text-[#edEEF0] underline transition-colors inline-flex items-center gap-1"
                                >
                                    Open Google Sheets <ExternalLink className="w-3 h-3" />
                                </a>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Footer */}
            <div className="fixed bottom-6 text-[#444446] text-xs">
                AI Native Lead Generation
            </div>

        </div>
    );
}
