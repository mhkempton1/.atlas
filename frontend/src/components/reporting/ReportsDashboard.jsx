import React, { useState } from 'react';
import { Users, Clock, Briefcase, Box, Truck } from 'lucide-react';
import ActiveEmployeesView from './ActiveEmployeesView';
import TimeCardsView from './TimeCardsView';
import ActiveProjectsView from './ActiveProjectsView';
import WorkflowView from './WorkflowView';
import SupplyChainView from './SupplyChainView';

const ReportsDashboard = () => {
    const [activeTab, setActiveTab] = useState('employees');

    const TABS = [
        { id: 'employees', label: 'Active Employees', icon: Users },
        { id: 'timecards', label: 'Time Cards', icon: Clock },
        { id: 'projects', label: 'Active Projects', icon: Briefcase },
        { id: 'workflow', label: 'Workflow (Boxes)', icon: Box },
        { id: 'supply', label: 'Supply Chain / Production', icon: Truck },
    ];

    const renderContent = () => {
        switch (activeTab) {
            case 'employees': return <ActiveEmployeesView />;
            case 'timecards': return <TimeCardsView />;
            case 'projects': return <ActiveProjectsView />;
            case 'workflow': return <WorkflowView />;
            case 'supply': return <SupplyChainView />;
            default: return <ActiveEmployeesView />;
        }
    };

    return (
        <div className="h-full flex flex-col space-y-6">
            <div className="flex items-center gap-3">
                <div className="p-2 bg-indigo-500/20 rounded-lg">
                    <Box className="w-6 h-6 text-indigo-400" />
                </div>
                <div>
                    <h2 className="text-xl font-bold text-white">Atlas Reports</h2>
                    <p className="text-sm text-white/40">Operational intelligence and status reporting</p>
                </div>
            </div>


            <div className="flex gap-2 border-b border-white/5 pb-1 overflow-x-auto">
                {TABS.map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`flex items-center gap-2 px-4 py-2 rounded-t-lg font-medium transition-all whitespace-nowrap ${activeTab === tab.id
                            ? 'bg-white/10 text-white border-b-2 border-purple-500 backdrop-blur-md'
                            : 'text-slate-400 hover:text-white hover:bg-white/5'
                            }`}
                    >
                        <tab.icon className="w-4 h-4" />
                        {tab.label}
                    </button>
                ))}
            </div>

            <div className="flex-1 bg-white/[0.02] backdrop-blur-xl rounded-b-xl rounded-tr-xl p-6 shadow-2xl border border-white/10 min-h-0 overflow-auto">
                {renderContent()}
            </div>
        </div>
    );
};

export default ReportsDashboard;
