import React, { useState } from 'react';
import { Play, MapPin, Calendar, Loader2 } from 'lucide-react';

export default function Home() {
    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState("Idle");
    const [resultLink, setResultLink] = useState("");
    const [industry, setIndustry] = useState("Plumbers");
    const [location, setLocation] = useState("Los Angeles, CA");

    const runScraper = async () => {
        setLoading(true);
        setStatus("Waking up server (this may take 50s)...");

        // Hardcoded for stability
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
                setStatus(`Job Started! Scraping ${industry} in ${location}...`);
                // Mocking the result link for immediate gratification in this MVP
                // In real life, we'd poll for completion.
                // We use the same sheet URL because push_to_sheets.py outputs to a single spreadsheet (or creates new ones).
                // Since we don't have the dynamic sheet ID here without polling, we can link to the Sheets home or the likely URL if known.
                // For MVP, assume one main sheet or user checks their Drive.
                setResultLink("https://docs.google.com/spreadsheets/u/0/");
            } else {
                setStatus("Error: " + data.detail);
            }
        } catch (e) {
            setStatus("Error: Failed to connect to backend. Is it running?");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-black text-gray-100 font-sans p-8 flex flex-col items-center justify-center">
            <div className="max-w-md w-full bg-gray-900 border border-gray-800 rounded-2xl p-8 shadow-2xl">
                <div className="mb-8 text-center">
                    <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-green-400 to-blue-500">
                        B2B Lead Scraper
                    </h1>
                    <p className="text-gray-500 mt-2 text-sm">Convert Google Maps into Leads</p>
                </div>

                <div className="space-y-4">
                    <div className="space-y-2">
                        <label className="text-xs font-mono text-gray-400">INDUSTRY / KEYWORD</label>
                        <div className="flex items-center bg-gray-800 rounded-lg px-4 py-3 border border-gray-700">
                            <Play className="w-5 h-5 text-green-400 mr-3" />
                            <input
                                type="text"
                                value={industry}
                                onChange={(e) => setIndustry(e.target.value)}
                                className="bg-transparent w-full outline-none text-white placeholder-gray-600"
                                placeholder="e.g. Dentists, HVAC, Lawyers"
                            />
                        </div>
                    </div>

                    <div className="space-y-2">
                        <label className="text-xs font-mono text-gray-400">LOCATION</label>
                        <div className="flex items-center bg-gray-800 rounded-lg px-4 py-3 border border-gray-700">
                            <MapPin className="w-5 h-5 text-blue-400 mr-3" />
                            <input
                                type="text"
                                value={location}
                                onChange={(e) => setLocation(e.target.value)}
                                className="bg-transparent w-full outline-none text-white"
                                placeholder="e.g. New York, NY"
                            />
                        </div>
                    </div>

                    <button
                        onClick={runScraper}
                        disabled={loading}
                        className={`w-full mt-6 py-4 rounded-xl font-bold text-lg flex items-center justify-center transition-all ${loading
                            ? 'bg-gray-700 cursor-not-allowed text-gray-400'
                            : 'bg-gradient-to-r from-green-600 to-blue-600 hover:scale-[1.02] shadow-lg shadow-green-500/20'
                            }`}
                    >
                        {loading ? <Loader2 className="w-6 h-6 animate-spin" /> : <Play className="w-5 h-5 mr-2 fill-current" />}
                        {loading ? "SCRAPING..." : "FIND LEADS"}
                    </button>
                </div>

                {status !== "Idle" && (
                    <div className="mt-8 p-4 bg-black/50 rounded-lg border border-gray-800 font-mono text-sm">
                        <p className={status.includes('Error') ? 'text-red-400' : 'text-green-400'}>
                            &gt; {status}
                        </p>
                        {resultLink && (
                            <div className="mt-2 text-blue-400 break-all">
                                <a href={resultLink} target="_blank" className="underline hover:text-blue-300">Open Google Sheets</a>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
