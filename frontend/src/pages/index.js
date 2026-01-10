import React, { useState } from 'react';
import { Loader2, Sparkles, ExternalLink } from 'lucide-react';

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
        setStatus("Connecting...");

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
                setStatus(`Started. Retrieving results for ${industry}...`);
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
        <div className="flex flex-col items-center justify-center min-h-screen px-6 animate-fade-in">

            {/* Centered content block constrained to 640px */}
            <div className="w-full max-w-[580px] flex flex-col gap-10">

                {/* Hero / Headline */}
                <div className="text-center space-y-4">
                    <h1 className="text-[48px] md:text-[56px] font-light tracking-tight text-[#edEEF0] leading-[1.05]">
                        Where should we start?
                    </h1>
                    <p className="text-[#8E8E93] text-lg font-light">
                        Verified B2B leads, generated in seconds.
                    </p>
                </div>

                {/* Form Group */}
                <div className="flex flex-col gap-5">

                    {/* Industry Input */}
                    <div>
                        <label className="minimal-label">INDUSTRY / BUSINESS TYPE</label>
                        <input
                            type="text"
                            value={industry}
                            onChange={(e) => setIndustry(e.target.value)}
                            className="minimal-input"
                            placeholder="e.g. Dentists, SaaS, Plumbers"
                        />
                    </div>

                    {/* Location Input */}
                    <div>
                        <label className="minimal-label">TARGET LOCATION</label>
                        <input
                            type="text"
                            value={location}
                            onChange={(e) => setLocation(e.target.value)}
                            className="minimal-input"
                            placeholder="e.g. Austin, TX"
                        />
                    </div>

                    {/* Vertical Rhythm Spacer */}
                    <div className="h-2"></div>

                    {/* Primary Button (Dark Surface) */}
                    <button
                        onClick={runScraper}
                        disabled={loading}
                        className="minimal-btn group"
                    >
                        {loading ? (
                            <>
                                <Loader2 className="w-5 h-5 animate-spin text-[#8E8E93]" />
                                <span className="text-[#edEEF0]">Processing...</span>
                            </>
                        ) : (
                            <>
                                <Sparkles className="w-5 h-5 text-[#8E8E93] group-hover:text-white transition-colors" />
                                <span>Find Leads</span>
                            </>
                        )}
                    </button>

                </div>

                {/* Minimal Status Feedback */}
                {status && (
                    <div className="text-center animate-fade-in">
                        <p className={`text-sm font-medium ${status.includes('Error') || status.includes('failed') ? "text-red-400" : "text-[#edEEF0]"}`}>
                            {status}
                        </p>
                        {resultLink && (
                            <a
                                href={resultLink}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-2 mt-3 text-sm text-[#8E8E93] hover:text-[#edEEF0] transition-colors"
                            >
                                Open Google Sheets <ExternalLink className="w-3 h-3" />
                            </a>
                        )}
                    </div>
                )}

            </div>

        </div>
    );
}
