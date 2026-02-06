import { Settings, Save, Server, Shield, Bell } from 'lucide-react';
import { useToast } from '../../hooks/useToast';

const SystemConfig = () => {
    const { addToast, toastElement } = useToast();

    const handleSave = async () => {
        try {
            await SYSTEM_API.saveSystemConfig({
                notifications: { email: true, health: true },
                security: { session_timeout: 60 }
            });
            addToast("System configuration updated successfully", "success");
        } catch (err) {
            addToast("Failed to save configuration", "error");
        }
    };

    const handleTestConnection = () => {
        addToast("Connected to Altimeter Core on Port 4203", "success");
    };

    return (
        <div className="h-full flex flex-col bg-surface-dark rounded-lg border border-border overflow-hidden">
            <div className="p-6 border-b border-border flex justify-between items-center">
                <h2 className="text-xl font-bold text-text-bright flex items-center gap-3">
                    <Settings className="w-6 h-6 text-primary" />
                    System Configuration
                </h2>
                <button className="btn btn-primary" onClick={handleSave}>
                    <Save className="w-4 h-4" />
                    Save Changes
                </button>
            </div>

            <div className="flex-1 overflow-auto p-6 space-y-8">

                {/* General Settings */}
                <section>
                    <h3 className="text-sm uppercase text-text-muted font-bold mb-4 flex items-center gap-2">
                        <Server className="w-4 h-4" /> Environment
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-4 bg-background-dark rounded-lg border border-border">
                        <div className="space-y-2">
                            <label className="text-sm text-text-bright">Environment Name</label>
                            <input className="input-field" defaultValue="Production-Alpha" />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm text-text-bright">Instance ID</label>
                            <input className="input-field opacity-50" readOnly defaultValue="ATL-005-MK" />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm text-text-bright">Local Database Path</label>
                            <input className="input-field font-mono text-xs" defaultValue="c:\Users\mhkem\.atlas\database\atlas.db" />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm text-text-bright">Atlas Endpoint (Port)</label>
                            <input className="input-field font-mono text-xs" readOnly defaultValue="http://127.0.0.1:4201" />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm text-text-bright">Altimeter Endpoint (Port)</label>
                            <input className="input-field font-mono text-xs" readOnly defaultValue="http://127.0.0.1:4203" />
                        </div>
                    </div>
                </section>

                {/* Notifications */}
                <section>
                    <h3 className="text-sm uppercase text-text-muted font-bold mb-4 flex items-center gap-2">
                        <Bell className="w-4 h-4" /> Notifications & Alerts
                    </h3>
                    <div className="space-y-3 p-4 bg-background-dark rounded-lg border border-border">
                        <label className="flex items-center gap-3 cursor-pointer">
                            <input type="checkbox" defaultChecked className="w-4 h-4 accent-primary" />
                            <span className="text-sm text-text-bright">Email Sync Completion Alerts</span>
                        </label>
                        <label className="flex items-center gap-3 cursor-pointer">
                            <input type="checkbox" defaultChecked className="w-4 h-4 accent-primary" />
                            <span className="text-sm text-text-bright">System Health Critical Warnings</span>
                        </label>
                        <label className="flex items-center gap-3 cursor-pointer">
                            <input type="checkbox" className="w-4 h-4 accent-primary" />
                            <span className="text-sm text-text-bright">Mission Task Reminders</span>
                        </label>
                    </div>
                </section>

                {/* Security */}
                <section>
                    <h3 className="text-sm uppercase text-text-muted font-bold mb-4 flex items-center gap-2">
                        <Shield className="w-4 h-4" /> Security & Access
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-4 bg-background-dark rounded-lg border border-border">
                        <div className="space-y-2">
                            <label className="text-sm text-text-bright">Session Timeout (minutes)</label>
                            <input type="number" className="input-field" defaultValue="60" />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm text-text-bright">Min. Strata for Config Access</label>
                            <input type="number" className="input-field" defaultValue="4" />
                        </div>
                    </div>
                </section>

                {/* Altimeter Development Controls */}
                <section>
                    <h3 className="text-sm uppercase text-text-muted font-bold mb-4 flex items-center gap-2">
                        <Shield className="w-4 h-4" /> Altimeter Development Controls (Portcullis)
                    </h3>
                    <div className="space-y-4 p-4 bg-background-dark rounded-lg border border-border">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="p-3 bg-slate-800/50 rounded-lg border border-slate-700">
                                <div className="flex justify-between items-center mb-2">
                                    <span className="text-sm font-semibold text-text-bright">Gateway Auth</span>
                                    <span className="text-xs text-green-400 font-bold">● Online</span>
                                </div>
                                <p className="text-xs text-text-muted">Access control system active</p>
                            </div>
                            <div className="p-3 bg-slate-800/50 rounded-lg border border-slate-700">
                                <div className="flex justify-between items-center mb-2">
                                    <span className="text-sm font-semibold text-text-bright">Validation Engine</span>
                                    <span className="text-xs text-yellow-400 font-bold">● Standby</span>
                                </div>
                                <p className="text-xs text-text-muted">Project intake validation ready</p>
                            </div>
                            <div className="p-3 bg-slate-800/50 rounded-lg border border-slate-700">
                                <div className="flex justify-between items-center mb-2">
                                    <span className="text-sm font-semibold text-text-bright">Audit Logs</span>
                                    <span className="text-xs text-green-400 font-bold">● Online</span>
                                </div>
                                <p className="text-xs text-text-muted">Activity tracking enabled</p>
                            </div>
                        </div>
                        <div className="pt-3 border-t border-slate-700">
                            <div className="flex justify-between items-center">
                                <div>
                                    <label className="text-sm text-text-bright block mb-1">Portcullis Endpoint</label>
                                    <input className="input-field font-mono text-xs w-full" readOnly defaultValue="http://127.0.0.1:4203/portcullis" />
                                </div>
                            </div>
                        </div>
                        <div className="flex gap-2">
                            <button className="btn btn-ghost text-sm" onClick={handleTestConnection}>
                                <Server className="w-4 h-4 mr-2" />
                                Test Connection
                            </button>
                            <button className="btn btn-ghost text-sm" onClick={() => window.open('http://127.0.0.1:4203', '_blank')}>
                                View Portcullis Dashboard
                            </button>
                        </div>
                    </div>
                </section>
            </div>
            {toastElement}
        </div>
    );
};

export default SystemConfig;
