import React, { useState } from 'react';
import { Sparkles, Plus, Settings2, ChevronDown, Mic, Search, MapPin, Loader2, ExternalLink, Zap, Building2, Users } from 'lucide-react';

export default function Home() {
    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState("");
    const [resultLink, setResultLink] = useState("");
    const [industry, setIndustry] = useState("");
    const [location, setLocation] = useState("");

    const runScraper = async () => {
        if (!industry || !location) {
            setStatus("error:Please enter both industry and location");
            return;
        }

        setLoading(true);
        setStatus("pending:Waking up server (this may take 50s)...");

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
                setStatus(`success:Scraping ${industry} in ${location}... Check your sheet in 60s!`);
                setResultLink("https://docs.google.com/spreadsheets/u/0/");
            } else {
                setStatus("error:" + data.detail);
            }
        } catch (e) {
            setStatus("error:Failed to connect. Is the server running?");
        } finally {
            setLoading(false);
        }
    };

    const quickFill = (ind, loc) => {
        setIndustry(ind);
        setLocation(loc);
    };

    const getStatusClass = () => {
        if (status.startsWith('success:')) return 'status-success';
        if (status.startsWith('error:')) return 'status-error';
        return 'status-pending';
    };

    const getStatusText = () => {
        return status.replace(/^(success:|error:|pending:)/, '');
    };

    return (
        <div className="main-container">
            {/* Header */}
            <div className="header">
                <div className="greeting">
                    <Sparkles className="greeting-icon" style={{ color: '#4285f4' }} />
                    <span className="greeting-text">Lead Finder</span>
                </div>
                <h1 className="headline">What leads can I find for you?</h1>
            </div>

            {/* Main Input Container */}
            <div className="input-container">
                <input
                    type="text"
                    className="input-field"
                    placeholder="Enter industry and location (e.g. Plumbers in Miami)"
                    value={industry && location ? `${industry} in ${location}` : industry || ''}
                    onChange={(e) => {
                        const val = e.target.value;
                        if (val.includes(' in ')) {
                            const parts = val.split(' in ');
                            setIndustry(parts[0]);
                            setLocation(parts.slice(1).join(' in '));
                        } else {
                            setIndustry(val);
                            setLocation('');
                        }
                    }}
                />

                {/* Toolbar */}
                <div className="toolbar">
                    <div className="toolbar-left">
                        <button className="toolbar-btn">
                            <Plus size={18} />
                        </button>
                        <button className="toolbar-btn">
                            <Settings2 size={18} />
                            <span>Tools</span>
                        </button>
                    </div>
                    <div className="toolbar-right">
                        <button className="model-selector">
                            <span>Pro</span>
                            <ChevronDown size={16} />
                        </button>
                        <button
                            className="mic-btn"
                            onClick={runScraper}
                            disabled={loading || (!industry && !location)}
                            style={loading ? { background: '#4285f4' } : {}}
                        >
                            {loading ? <Loader2 size={20} className="animate-spin" /> : <Zap size={20} />}
                        </button>
                    </div>
                </div>
            </div>

            {/* Quick Action Pills */}
            <div className="action-pills">
                <button className="pill" onClick={() => quickFill('Dentists', 'Los Angeles, CA')}>
                    <Building2 className="pill-icon" />
                    <span>Dentists in LA</span>
                </button>
                <button className="pill" onClick={() => quickFill('Plumbers', 'Chicago, IL')}>
                    <Users className="pill-icon" />
                    <span>Plumbers in Chicago</span>
                </button>
                <button className="pill" onClick={() => quickFill('HVAC', 'Miami, FL')}>
                    <Search className="pill-icon" />
                    <span>HVAC in Miami</span>
                </button>
                <button className="pill" onClick={() => quickFill('Lawyers', 'New York, NY')}>
                    <MapPin className="pill-icon" />
                    <span>Lawyers in NYC</span>
                </button>
            </div>

            {/* Primary Action Button */}
            <button
                className="primary-btn"
                onClick={runScraper}
                disabled={loading || !industry || !location}
            >
                {loading ? (
                    <>
                        <Loader2 size={20} className="animate-spin" />
                        <span>Finding leads...</span>
                    </>
                ) : (
                    <>
                        <Zap size={20} />
                        <span>Find Leads</span>
                    </>
                )}
            </button>

            {/* Status Message */}
            {status && (
                <div className="status-message">
                    <p className={getStatusClass()}>
                        {getStatusText()}
                    </p>
                    {resultLink && (
                        <a href={resultLink} target="_blank" rel="noopener noreferrer" className="status-link">
                            <ExternalLink size={14} />
                            Open Google Sheets
                        </a>
                    )}
                </div>
            )}
        </div>
    );
}
