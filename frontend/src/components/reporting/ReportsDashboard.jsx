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
                    <p className="text-sm text-slate-400">Operational intelligence and status reporting</p>
                </div>
            </div>

            <div className="flex gap-2 border-b border-slate-700 pb-1 overflow-x-auto">
                {TABS.map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`flex items-center gap-2 px-4 py-2 rounded-t-lg font-medium transition-colors whitespace-nowrap ${activeTab === tab.id
                            ? 'bg-slate-700 text-white border-b-2 border-indigo-500'
                            : 'text-slate-400 hover:text-white hover:bg-slate-800'
                            }`}
                    >
                        <tab.icon className="w-4 h-4" />
                        {tab.label}
                    </button>
                ))}
            </div>

            <div className="flex-1 bg-slate-800 rounded-b-xl rounded-tr-xl p-6 shadow-lg border border-slate-700 min-h-0 overflow-auto">
                {renderContent()}
            </div>
        </div>
    );
};

export default ReportsDashboard;
