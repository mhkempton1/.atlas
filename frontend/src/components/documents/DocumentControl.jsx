import React, { useState, useEffect } from 'react';
import { SYSTEM_API } from '../../services/api';
import {
    FileText,
    ArrowRight,
    Lock,
    AlertCircle,
    Plus,
    Trash2,
    Edit,
    Search,
    ShieldCheck,
    FolderKanban,
    MessageSquare,
    Eye,
    CornerUpLeft
} from 'lucide-react';
import { AnimatePresence, motion as Motion } from 'framer-motion';
import DocumentEditor from './DocumentEditor';
import DocumentCommentPanel from './DocumentCommentPanel';

const DocumentControl = () => {
    const [sortConfig, setSortConfig] = useState({ key: 'modified', direction: 'desc' });
    const [docs, setDocs] = useState({ draft: [], review: [], locked: [] });
    const [isLoading, setIsLoading] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [editingDoc, setEditingDoc] = useState(null);
    const [activeTab, setActiveTab] = useState('draft');
    const [commentPanelDoc, setCommentPanelDoc] = useState(null);

    const loadDocs = async () => {
        setIsLoading(true);
        try {
            const data = await SYSTEM_API.getControlledDocs();
            setDocs(data);
        } catch (err) {
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        loadDocs();
    }, []);

    // --- Actions ---

    const handleSort = (key) => {
        let direction = 'asc';
        if (sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc';
        }
        setSortConfig({ key, direction });
    };

    const sortedData = (data) => {
        const items = [...data];
        if (sortConfig.key) {
            items.sort((a, b) => {
                let aVal = a[sortConfig.key];
                let bVal = b[sortConfig.key];

                if (sortConfig.key === 'filename') {
                    aVal = aVal.toLowerCase();
                    bVal = bVal.toLowerCase();
                }

                if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
                if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
                return 0;
            });
        }
        return items.filter(d =>
            d.filename.toLowerCase().includes(searchQuery.toLowerCase())
        );
    };

    const handleCreateNew = async () => {
        const title = prompt("Enter Document Title (e.g., Safety Policy 2026):");
        if (!title) return;

        try {
            await SYSTEM_API.createDraft(title, "# " + title + "\n\nSet content here...");
            loadDocs();
        } catch (err) {
            alert(err.response?.data?.detail || "Failed to create draft");
        }
    };

    const handleEdit = async (doc) => {
        try {
            const content = await SYSTEM_API.getDocContent(doc.path);
            setEditingDoc({ ...doc, content });
        } catch {
            alert("Failed to load document content");
        }
    };

    const handleSaveEdit = async (content) => {
        try {
            await SYSTEM_API.saveDraft(editingDoc.path, content);
            setEditingDoc(null);
            loadDocs();
        } catch {
            alert("Failed to save changes");
        }
    };

    const handleDemote = async (doc) => {
        if (!confirm(`Return '${doc.filename}' to Draft status?`)) return;
        try {
            await SYSTEM_API.demoteToDraft(doc.path);
            loadDocs();
        } catch (err) {
            alert(err.response?.data?.detail || "Failed to return to draft");
        }
    };

    const handleView = async (doc) => {
        try {
            const content = await SYSTEM_API.getDocContent(doc.path);
            // We reuse the editor but pass a readOnly flag if supported, or just let them see it.
            // For now, let's just open the editor. If we want read-only we can add a flag later
            // but the user just wants to see it.
            setEditingDoc({ ...doc, content, readOnly: true });
        } catch {
            alert("Failed to load document content");
        }
    };

    const handleDelete = async (doc) => {
        if (!confirm(`Are you sure you want to delete the draft '${doc.filename}'?`)) return;
        try {
            await SYSTEM_API.deleteDraft(doc.path);
            loadDocs();
        } catch {
            alert("Failed to delete draft");
        }
    };

    const handlePromote = async (doc) => {
        if (!confirm(`Promote '${doc.filename}' to official Review status?`)) return;
        try {
            await SYSTEM_API.promoteToReview(doc.path);
            loadDocs();
            setActiveTab('review');
        } catch {
            alert("Failed to promote document");
        }
    };

    const handleSignOff = async (doc) => {
        const approver = prompt("Enter your Administrator Name for signing off:");
        if (!approver) return;

        try {
            await SYSTEM_API.lockDocument(doc.path, approver);
            loadDocs();
            setActiveTab('codex');
        } catch {
            alert("Approval failed");
        }
    };

    const handleViewComments = (doc) => {
        setCommentPanelDoc(doc);
    };

    const renderSortIcon = (key) => {
        if (sortConfig.key !== key) return null;
        return sortConfig.direction === 'asc' ? <ArrowRight className="w-3 h-3 -rotate-90" /> : <ArrowRight className="w-3 h-3 rotate-90" />;
    };

    const renderTable = (items, type) => {
        const data = sortedData(items);

        if (data.length === 0 && searchQuery === '') {
            return (
                <div className="h-64 flex flex-col items-center justify-center text-slate-600 border-2 border-dashed border-slate-800 rounded-xl m-6">
                    <Plus className="w-12 h-12 mb-2 opacity-20" />
                    <p>No documents found in this category.</p>
                </div>
            );
        }

        return (
            <div className="flex-1 flex flex-col overflow-hidden">
                <div className="overflow-y-auto px-6 pb-6 scrollbar-thin">
                    <table className="w-full text-left border-separate border-spacing-y-2">
                        <thead className="sticky top-0 bg-[#0f172a] z-10">
                            <tr className="text-[10px] text-slate-500 uppercase font-mono tracking-widest">
                                <th onClick={() => handleSort('filename')} className="pb-4 pl-4 font-normal cursor-pointer hover:text-slate-300 transition-colors">
                                    <div className="flex items-center gap-1">Identifier {renderSortIcon('filename')}</div>
                                </th>
                                {type !== 'draft' && (
                                    <th onClick={() => handleSort('version')} className="pb-4 font-normal cursor-pointer hover:text-slate-300 transition-colors text-center w-24">
                                        <div className="flex items-center justify-center gap-1">Version {renderSortIcon('version')}</div>
                                    </th>
                                )}
                                <th onClick={() => handleSort('modified')} className="pb-4 font-normal cursor-pointer hover:text-slate-300 transition-colors">
                                    <div className="flex items-center gap-1">{type === 'codex' ? 'Published' : 'Modified'} {renderSortIcon('modified')}</div>
                                </th>
                                <th className="pb-4 text-right pr-4 font-normal w-32">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="">
                            {data.map(doc => (
                                <Motion.tr
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    key={doc.id}
                                    className="group bg-slate-900/40 hover:bg-slate-800/60 transition-all rounded-lg"
                                >
                                    <td className="py-4 pl-4 rounded-l-lg border-y border-l border-white/5">
                                        <div className="flex items-center gap-3">
                                            {type === 'draft' ? <Edit className="w-4 h-4 text-purple-400" /> :
                                                type === 'review' ? <AlertCircle className="w-4 h-4 text-yellow-500" /> :
                                                    <Lock className="w-4 h-4 text-emerald-500" />}
                                            <span className="text-sm font-bold text-slate-200">{doc.filename}</span>
                                        </div>
                                    </td>
                                    {type !== 'draft' && (
                                        <td className="py-4 border-y border-white/5 text-center">
                                            <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${type === 'codex' ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' : 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20'}`}>
                                                v{doc.version}
                                            </span>
                                        </td>
                                    )}
                                    <td className="py-4 border-y border-white/5 text-xs text-slate-400 font-mono">
                                        {new Date(doc.modified * 1000).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })}
                                    </td>
                                    <td className="py-4 text-right pr-4 rounded-r-lg border-y border-r border-white/5">
                                        <div className="flex justify-end gap-2">
                                            <button
                                                onClick={() => handleViewComments(doc)}
                                                title="View Comments"
                                                className="p-1.5 hover:bg-blue-500/20 rounded-md text-slate-400 hover:text-blue-400 transition-all"
                                            >
                                                <MessageSquare className="w-4 h-4" />
                                            </button>
                                            {type === 'draft' && (
                                                <>
                                                    <button onClick={() => handleEdit(doc)} title="Edit Draft" className="p-1.5 hover:bg-purple-500/20 rounded-md text-slate-400 hover:text-purple-400 transition-all"><Edit className="w-4 h-4" /></button>
                                                    <button onClick={() => handleDelete(doc)} title="Delete Draft" className="p-1.5 hover:bg-red-500/20 rounded-md text-slate-400 hover:text-red-400 transition-all"><Trash2 className="w-4 h-4" /></button>
                                                    <button onClick={() => handlePromote(doc)} title="Promote to Review" className="p-1.5 hover:bg-emerald-500/20 rounded-md text-slate-400 hover:text-emerald-400 transition-all"><ArrowRight className="w-4 h-4" /></button>
                                                </>
                                            )}
                                            {type === 'review' && (
                                                <>
                                                    <button
                                                        onClick={() => handleView(doc)}
                                                        title="View Document"
                                                        className="p-1.5 hover:bg-slate-500/20 rounded-md text-slate-400 hover:text-slate-200 transition-all"
                                                    >
                                                        <Eye className="w-4 h-4" />
                                                    </button>
                                                    <button
                                                        onClick={() => handleDemote(doc)}
                                                        title="Return to Draft"
                                                        className="p-1.5 hover:bg-red-500/20 rounded-md text-slate-400 hover:text-red-400 transition-all"
                                                    >
                                                        <CornerUpLeft className="w-4 h-4" />
                                                    </button>
                                                    <button
                                                        onClick={() => handleSignOff(doc)}
                                                        className="px-3 py-1 bg-yellow-500 text-black font-black text-[9px] uppercase rounded hover:bg-yellow-400 transition-all shadow-lg shadow-yellow-500/20"
                                                    >
                                                        Sign-Off
                                                    </button>
                                                </>
                                            )}
                                            {type === 'codex' && (
                                                <button className="text-[10px] font-bold text-emerald-500 hover:text-emerald-400 uppercase tracking-tighter">View Official</button>
                                            )}
                                        </div>
                                    </td>
                                </Motion.tr>
                            ))}
                        </tbody>
                    </table>
                    {data.length === 0 && searchQuery !== '' && (
                        <div className="text-center py-20 text-slate-600">
                            No matches for <span className="text-slate-400 italic">"{searchQuery}"</span>
                        </div>
                    )}
                </div>
            </div>
        );
    };

    return (
        <div className="h-[calc(100vh-100px)] flex flex-col">
            {/* Header */}
            <div className="mb-6 flex justify-between items-end bg-slate-900/30 p-4 rounded-xl border border-white/5 backdrop-blur-md">
                <div>
                    <h1 className="text-2xl font-bold text-white mb-2">Document Control Center</h1>
                    <div className="flex items-center gap-6 text-slate-400 text-sm">
                        <span className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-purple-500 animate-pulse" /> Draft Lifecycle
                        </span>
                        <span className="flex items-center gap-2 text-yellow-400/80 font-medium">
                            <ShieldCheck className="w-4 h-4" /> System Review
                        </span>
                    </div>
                </div>
                <div className="flex gap-3">
                    <button onClick={() => onNavigate('procedures')} className="btn btn-primary px-6 py-2.5 text-xs flex items-center gap-2 shadow-emerald-500/10">
                        <Plus className="w-4 h-4" /> New Standard/SOP
                    </button>
                    <button onClick={loadDocs} className="btn btn-secondary px-4 py-2.5 text-xs bg-slate-800/50 hover:bg-slate-800">
                        {isLoading ? 'Scanning...' : 'Refresh'}
                    </button>
                </div>
            </div>

            {/* Controls Row */}
            <div className="flex justify-between items-center mb-6 gap-4">
                <div className="flex gap-1 bg-slate-950/50 p-1.5 rounded-xl border border-white/5 shadow-inner">
                    <button
                        onClick={() => setActiveTab('draft')}
                        className={`px-6 py-2.5 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${activeTab === 'draft' ? 'bg-purple-600/90 text-white shadow-lg' : 'text-slate-500 hover:text-slate-200'}`}
                    >
                        <FileText className="w-3.5 h-3.5" /> DRAFTS <span className="opacity-50 ml-1">[{docs.draft.length}]</span>
                    </button>
                    <button
                        onClick={() => setActiveTab('review')}
                        className={`px-6 py-2.5 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${activeTab === 'review' ? 'bg-yellow-600/90 text-white shadow-lg' : 'text-slate-500 hover:text-slate-200'}`}
                    >
                        <AlertCircle className="w-3.5 h-3.5" /> IN REVIEW <span className="opacity-50 ml-1">[{docs.review.length}]</span>
                    </button>
                    <button
                        onClick={() => setActiveTab('codex')}
                        className={`px-6 py-2.5 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${activeTab === 'codex' ? 'bg-emerald-600/90 text-white shadow-lg' : 'text-slate-500 hover:text-slate-200'}`}
                    >
                        <FolderKanban className="w-3.5 h-3.5" /> KNOWLEDGE BASE <span className="opacity-50 ml-1">[{docs.locked.length}]</span>
                    </button>
                </div>

                <div className="relative flex-1 max-w-sm">
                    <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                    <input
                        type="text"
                        placeholder={`Search ${activeTab === 'codex' ? 'Knowledge Base' : activeTab === 'review' ? 'Review Queue' : 'Drafts'}...`}
                        className="w-full bg-slate-950/50 border border-white/5 rounded-xl py-2.5 pl-11 pr-4 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-primary/50 transition-all"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>
            </div>

            {/* Content Area */}
            <div className="flex-1 glass-panel overflow-hidden flex flex-col p-0 bg-slate-950/20 border border-white/5 backdrop-blur-sm rounded-2xl">
                <AnimatePresence mode="wait">
                    <Motion.div
                        key={activeTab}
                        initial={{ opacity: 0, scale: 0.98 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 1.02 }}
                        transition={{ duration: 0.2 }}
                        className="flex-1 flex flex-col overflow-hidden"
                    >
                        {activeTab === 'draft' && renderTable(docs.draft, 'draft')}
                        {activeTab === 'review' && renderTable(docs.review, 'review')}
                        {activeTab === 'codex' && renderTable(docs.locked, 'codex')}
                    </Motion.div>
                </AnimatePresence>
            </div>

            {/* Status Footer */}
            <div className="mt-4 flex justify-between items-center text-[10px] text-slate-500 font-mono uppercase tracking-widest px-2">
                <div className="flex gap-4">
                    <span>Total Managed Assets: {docs.draft.length + docs.review.length + docs.locked.length}</span>
                    <span>System Status: Operational</span>
                </div>
                <div>Last Synchronized: {new Date().toLocaleTimeString()}</div>
            </div>

            {/* Editor Modal */}
            {editingDoc && (
                <DocumentEditor
                    doc={editingDoc}
                    onSave={handleSaveEdit}
                    onCancel={() => setEditingDoc(null)}
                />
            )}

            {/* Comment Panel */}
            {commentPanelDoc && (
                <DocumentCommentPanel
                    documentPath={commentPanelDoc.path}
                    onClose={() => setCommentPanelDoc(null)}
                />
            )}
        </div>
    );
};

export default DocumentControl;
