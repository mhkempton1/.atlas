import React, { useState } from 'react';
import { Shield, Map, AlertTriangle, Navigation, Globe } from 'lucide-react';

const PortcullisView = () => {
    const [formData, setFormData] = useState({
        targetId: '',
        coordinates: '',
        clearanceLevel: '3',
        scopeNotes: ''
    });
    const [error, setError] = useState(null);

    React.useEffect(() => {
        // Fetch real status from backend
        // Assuming api.js is imported or fetch is used
        fetch('http://127.0.0.1:4201/api/v1/system/geo/status')
            .then(res => res.json())
            .then(data => {
                if (data.status !== 'online') {
                    setError(data.message || "Connection to Geospatial Service failed.");
                }
            })
            .catch(() => setError("Connection to Geospatial Service failed. Map tiles are currently offline."));
    }, []);

    return (
        <div className="h-full flex flex-col space-y-6">
            <div className="flex items-center gap-3">
                <Shield className="w-6 h-6 text-primary" />
                <h2 className="text-xl font-bold text-text-bright">Portcullis Gatekeeper</h2>
            </div>

            {/* Alert Banner - Top Aligned */}
            {error && (
                <div className="w-full bg-danger/10 border border-danger/20 rounded-lg p-4 flex items-center gap-3 animate-in fade-in slide-in-from-top-2">
                    <AlertTriangle className="w-5 h-5 text-danger" />
                    <div>
                        <h4 className="text-sm font-bold text-danger">System Alert: Geospatial Uplink Severed</h4>
                        <p className="text-xs text-text-muted">{error}</p>
                    </div>
                    <button
                        onClick={() => setError(null)}
                        className="ml-auto text-xs font-bold text-danger hover:text-white uppercase"
                    >
                        Dismiss
                    </button>
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 min-h-0">
                {/* Left Column: Form Controls */}
                <div className="card h-full flex flex-col gap-6">
                    <h3 className="uppercase-header flex items-center gap-2">
                        <Navigation className="w-4 h-4" /> Mission Parameters
                    </h3>

                    <div className="space-y-4">
                        <div className="space-y-1">
                            <label className="text-xs font-semibold text-text-muted uppercase">Target Identifier</label>
                            <input
                                className="input-field font-mono"
                                placeholder="e.g. ALPHA-CTOR-99"
                                value={formData.targetId}
                                onChange={e => setFormData({ ...formData, targetId: e.target.value })}
                            />
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1">
                                <label className="text-xs font-semibold text-text-muted uppercase">Latitude</label>
                                <input className="input-field font-mono" placeholder="34.0522° N" />
                            </div>
                            <div className="space-y-1">
                                <label className="text-xs font-semibold text-text-muted uppercase">Longitude</label>
                                <input className="input-field font-mono" placeholder="118.2437° W" />
                            </div>
                        </div>

                        <div className="space-y-1">
                            <label className="text-xs font-semibold text-text-muted uppercase">Clearance Protocol</label>
                            <select className="input-field appearance-none cursor-pointer">
                                <option>Level 5 - Eyes Only</option>
                                <option>Level 4 - Command Staff</option>
                                <option>Level 3 - Field Ops</option>
                            </select>
                        </div>
                    </div>

                    <div className="flex-1 flex flex-col">
                        <label className="text-xs font-semibold text-text-muted uppercase mb-1">Scope Notes (Intel)</label>
                        <textarea
                            className="input-field h-full min-h-[150px] p-3 resize-none bg-bg-app"
                            placeholder="Enter mission constraints and operational boundaries..."
                            value={formData.scopeNotes}
                            onChange={e => setFormData({ ...formData, scopeNotes: e.target.value })}
                        />
                    </div>

                    <div className="pt-4 border-t border-border flex gap-3">
                        <button
                            className="btn btn-primary flex-1"
                            onClick={() => window.open('http://127.0.0.1:4204', '_blank')}
                        >
                            Access Altimeter Portal
                        </button>
                        <button className="btn btn-secondary" onClick={() => setFormData({ targetId: '', coordinates: '', clearanceLevel: '3', scopeNotes: '' })}>Reset</button>
                    </div>
                </div>

                {/* Right Column: Map Visualization */}
                <div className="lg:col-span-2 card p-0 overflow-hidden relative group">
                    {/* Map Placeholder */}
                    <div className="absolute inset-0 bg-slate-900 flex items-center justify-center opacity-50">
                        <div className="text-center">
                            <Globe className="w-16 h-16 text-slate-700 mx-auto mb-4" />
                            <p className="text-slate-600 font-mono text-sm">Waiting for Coordinates...</p>
                        </div>
                    </div>

                    {/* Grid Pattern Overlay */}
                    <div className="absolute inset-0" style={{
                        backgroundImage: `linear-gradient(rgba(255, 255, 255, 0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 255, 255, 0.05) 1px, transparent 1px)`,
                        backgroundSize: '40px 40px'
                    }} />

                    {/* HUD Overlay */}
                    <div className="absolute top-4 left-4 bg-bg-card/90 backdrop-blur border border-border p-3 rounded-lg shadow-xl">
                        <div className="flex items-center gap-2 mb-1">
                            <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                            <span className="text-xs font-bold text-red-400 uppercase">Live Feed Unavailable</span>
                        </div>
                        <div className="text-[10px] font-mono text-text-muted">SAT-LINK: DISCONNECTED</div>
                    </div>

                    <div className="absolute bottom-4 right-4 flex gap-2">
                        <div className="bg-bg-app/80 backdrop-blur border border-border rounded px-2 py-1 text-[10px] font-mono text-text-muted">
                            ZOOM: 100%
                        </div>
                        <div className="bg-bg-app/80 backdrop-blur border border-border rounded px-2 py-1 text-[10px] font-mono text-text-muted">
                            GRID: WGS-84
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default PortcullisView;
