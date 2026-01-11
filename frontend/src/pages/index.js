import React, { useState, useEffect } from 'react';
import { Loader2, Sparkles, ExternalLink, Clock } from 'lucide-react';

export default function Home() {
    const [loading, setLoading] = useState(false);
    const [jobStarted, setJobStarted] = useState(false);
    const [jobId, setJobId] = useState(null);
    const [status, setStatus] = useState("");
    const [industry, setIndustry] = useState("");
    const [location, setLocation] = useState("");
    const [numLeads, setNumLeads] = useState(50);

    // Master sheet URL - user must create this sheet and share with Service Account
    const SHEET_URL = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID_HERE/edit";

    // Countdown timer
    // Poll job status
    useEffect(() => {
        let interval;
        if (jobStarted && jobId) {
            const API_URL = "https://b2b-scraper-4nme.onrender.com";
            interval = setInterval(async () => {
                try {
                    console.log(`Polling job: ${jobId}`);
                    const res = await fetch(`${API_URL}/api/job-status/${jobId}`);
                    const data = await res.json();

                    if (data.status === "completed") {
                        setJobStarted(false);
                        setJobId(null);
                        setStatus("✅ Results are ready! Check the spreadsheet.");
                    } else if (data.status === "failed") {
                        setJobStarted(false);
                        setJobId(null);
                        setStatus(`❌ Job failed: ${data.error || "Unknown error"}`);
                    }
                } catch (e) {
                    console.error("Polling error:", e);
                }
            }, 3000); // Poll every 3 seconds
        }
        return () => clearInterval(interval);
    }, [jobStarted, jobId]);

    const runScraper = async () => {
        if (!industry || !location) {
            setStatus("Please enter both fields");
            return;
        }

        setLoading(true);
        setJobStarted(false);
        setStatus("🔄 Connecting...");

        const API_URL = "https://b2b-scraper-4nme.onrender.com";

        try {
            const res = await fetch(`${API_URL}/api/run-lead-gen`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    industry: industry,
                    location: location,
                    limit: parseInt(numLeads)
                })
            });

            const data = await res.json();

            if (res.ok) {
                setJobStarted(true);
                setJobId(data.job_id); // Backend must return this!
                setStatus(`🔄 Scraping ${industry} in ${location}...`);
            } else {
                setStatus("❌ " + (data.detail || "Unknown error"));
            }
        } catch (e) {
            setStatus("❌ Connection failed. Server may be sleeping.");
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
                            disabled={loading || jobStarted}
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
                            disabled={loading || jobStarted}
                        />
                    </div>

                    <div>
                        <label className="minimal-label">NUMBER OF LEADS (5-50)</label>
                        <input
                            type="number"
                            min="5"
                            max="50"
                            value={numLeads}
                            onChange={(e) => setNumLeads(e.target.value)}
                            className="minimal-input"
                            placeholder="50"
                            disabled={loading || jobStarted}
                        />
                    </div>

                    <div className="h-2"></div>

                    {/* Button states */}
                    {!jobStarted ? (
                        <button
                            onClick={runScraper}
                            disabled={loading}
                            className="minimal-btn group"
                        >
                            {loading ? (
                                <>
                                    <Loader2 className="w-5 h-5 animate-spin text-[#8E8E93]" />
                                    <span className="text-[#edEEF0]">Connecting...</span>
                                </>
                            ) : (
                                <>
                                    <Sparkles className="w-5 h-5 text-[#8E8E93] group-hover:text-white transition-colors" />
                                    <span>Find Leads</span>
                                </>
                            )}
                        </button>
                    ) : (
                        <div className="flex flex-col gap-3">
                            {/* Countdown */}
                            <div className="flex items-center justify-center gap-3 py-4 px-6 bg-[#1a1a1d] rounded-xl">
                                <Clock className="w-5 h-5 text-[#8E8E93] animate-pulse" />
                                <span className="text-[#edEEF0]">
                                    Processing... <span className="font-mono text-[#8E8E93] animate-pulse">Please wait</span>
                                </span>
                            </div>

                            {/* Sheet Link */}
                            <a
                                href="https://docs.google.com/spreadsheets/d/1b9DrDkl1eUKKtyFFxXd_xt-3IaVObV25tKsTE0bn2xY/edit?usp=sharing"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="minimal-btn flex items-center justify-center gap-2 no-underline"
                            >
                                <ExternalLink className="w-5 h-5 text-[#8E8E93]" />
                                <span className="text-center">Open B2B Scraper Results Sheet</span>
                            </a>
                        </div>
                    )}

                </div>

                {/* Status */}
                {status && (
                    <div className="text-center animate-fade-in">
                        <p className={`text-sm font-medium ${status.includes('❌') ? "text-red-400" : status.includes('✅') ? "text-green-400" : "text-[#edEEF0]"}`}>
                            {status}
                        </p>
                    </div>
                )}

            </div>

        </div>
    );
}
