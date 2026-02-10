import React from 'react';

const ActiveEmployeesView = () => {
    // Mock data for now, as requested in plan
    const EMPLOYEES = [
        { id: 1, name: "Michael Kempton", role: "Administrator", status: "Active", location: "HQ" },
        { id: 2, name: "Sarah Connor", role: "Project Manager", status: "Active", location: "Field - Site A" },
        { id: 3, name: "John Smith", role: "Electrician Lead", status: "Active", location: "Field - Site B" },
        { id: 4, name: "Jane Doe", role: "Design Engineer", status: "Remote", location: "Home Office" },
        { id: 5, name: "Robert Tech", role: "Technician", status: "On Leave", location: "N/A" },
    ];

    return (
        <div className="space-y-4">
            <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold text-white">Active Employees Directory</h3>
                <div className="text-sm text-slate-400">Total: {EMPLOYEES.length}</div>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                    <thead>
                        <tr className="border-b border-white/5 text-slate-400 text-sm uppercase tracking-wider">
                            <th className="p-3">Name</th>
                            <th className="p-3">Role</th>
                            <th className="p-3">Status</th>
                            <th className="p-3">Current Location</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                        {EMPLOYEES.map(emp => (
                            <tr key={emp.id} className="hover:bg-white/5 transition-colors text-sm">
                                <td className="p-3 text-white font-medium">{emp.name}</td>
                                <td className="p-3 text-slate-300">{emp.role}</td>
                                <td className="p-3">
                                    <span className={`px-2 py-1 rounded text-xs font-bold ${emp.status === 'Active' ? 'bg-emerald-500/20 text-emerald-400' :
                                        emp.status === 'On Leave' ? 'bg-yellow-500/20 text-yellow-400' :
                                            'bg-slate-600 text-slate-300'
                                        }`}>
                                        {emp.status}
                                    </span>
                                </td>
                                <td className="p-3 text-slate-400 font-mono">{emp.location}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default ActiveEmployeesView;
