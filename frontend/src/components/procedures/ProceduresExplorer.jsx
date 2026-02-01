import React, { useState, useEffect } from 'react';
import { Search, Book, FileText, ChevronRight, ChevronDown, Folder, FolderOpen, Database, Shield, GraduationCap, FileCheck } from 'lucide-react';
import { SYSTEM_API } from '../../services/api';
import ReactMarkdown from 'react-markdown';
import { PageHeader, Spinner, EmptyState, Section } from '../shared/UIComponents';

const ProceduresExplorer = () => {
    const [searchTerm, setSearchTerm] = useState('');
    const [documents, setDocuments] = useState([]);
    const [selectedDoc, setSelectedDoc] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [openCategories, setOpenCategories] = useState({ 'Toolbox Talks': true });

    // Initial Load
    useEffect(() => {
        loadDocuments();
    }, []);

    const loadDocuments = async () => {
        setIsLoading(true);
        try {
            const docs = await SYSTEM_API.getKnowledgeDocs();
            setDocuments(docs);
        } catch (error) {
            console.error("Failed to load documents", error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleDocClick = async (doc) => {
        try {
            setIsLoading(true);
            const content = await SYSTEM_API.getKnowledgeContent(doc.full_path);
            setSelectedDoc({ ...doc, content });
        } catch (error) {
            console.error("Failed to load content", error);
        } finally {
            setIsLoading(false);
        }
    };

    const toggleCategory = (cat) => {
        setOpenCategories(prev => ({ ...prev, [cat]: !prev[cat] }));
    };

    const handleImportToWorkflow = async (doc) => {
        if (!confirm(`Import "${doc.title}" into the Document Control workflow for official review and publication?`)) return;

        try {
            const section = doc.category === 'SKILLS' ? 'SKILLS' : doc.category === 'TRAINING' ? 'TRAINING' : 'GUIDELINES';
            await SYSTEM_API.importToReview(doc.full_path, section);
            alert(`Successfully imported "${doc.title}" to Document Control Review queue!`);
        } catch (error) {
            alert(`Failed to import document: ${error.message}`);
        }
    };

    // Filtering
    const filteredDocs = documents.filter(doc =>
        doc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        doc.category?.toLowerCase().includes(searchTerm.toLowerCase())
    );

    // Grouping Logic
    const groups = filteredDocs.reduce((acc, doc) => {
        let cat = doc.category || 'Uncategorized';

        // Special case for Toolbox Talks
        if (doc.title.toLowerCase().includes('toolbox') || doc.title.toLowerCase().includes('week')) {
            cat = 'Toolbox Talks';
        } else if (cat === 'GUIDELINES') {
            cat = 'Guidelines & Policies';
        } else if (cat === 'TRAINING') {
            cat = 'Training Modules';
        } else if (cat === 'SKILLS') {
            cat = 'Skills & Expertise';
        }

        if (!acc[cat]) acc[cat] = [];
        acc[cat].push(doc);
        return acc;
    }, {});

    const getCategoryIcon = (cat) => {
        if (cat === 'Toolbox Talks') return <Shield className="w-4 h-4 text-amber-400" />;
        if (cat === 'Guidelines & Policies') return <FileCheck className="w-4 h-4 text-blue-400" />;
        if (cat === 'Training Modules') return <GraduationCap className="w-4 h-4 text-emerald-400" />;
        return <Folder className="w-4 h-4 text-gray-400" />;
    };

    return (
        <div className="h-[calc(100vh-140px)] flex flex-col space-y-4 animate-slide-in">
            <PageHeader
                icon={Book}
                title="Knowledge Base"
                subtitle="Procedures, SOPs & Safety Talks"
            />

            <div className="flex gap-6 flex-1 overflow-hidden">
                {/* Left Sidebar: Search & Grouped List */}
                <div className="w-1/3 bg-slate-900/50 rounded-xl flex flex-col overflow-hidden border border-white/5">
                    <div className="p-4 border-b border-white/5">
                        <div className="relative">
                            <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-500" />
                            <input
                                type="text"
                                placeholder="Filter knowledge..."
                                className="w-full bg-slate-800 border border-white/10 rounded-lg pl-10 pr-4 py-2 text-sm text-white focus:outline-none focus:border-purple-500/50"
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="flex-1 overflow-y-auto p-2 space-y-2 custom-scrollbar">
                        {isLoading && !selectedDoc ? (
                            <Spinner label="Indexing..." />
                        ) : Object.keys(groups).length === 0 ? (
                            <div className="text-center p-8 text-gray-500 text-sm italic">No records matches your search.</div>
                        ) : (
                            Object.entries(groups).sort((a, b) => b[1].length - a[1].length).map(([cat, docs]) => (
                                <div key={cat} className="mb-1">
                                    <button
                                        onClick={() => toggleCategory(cat)}
                                        className="w-full flex items-center gap-2 p-3 rounded-lg hover:bg-slate-800/80 transition-colors text-left group"
                                    >
                                        <div className="flex-shrink-0">
                                            {openCategories[cat] ? <ChevronDown className="w-4 h-4 text-gray-600" /> : <ChevronRight className="w-4 h-4 text-gray-600" />}
                                        </div>
                                        {getCategoryIcon(cat)}
                                        <span className="text-xs font-bold text-gray-400 uppercase tracking-widest">{cat}</span>
                                        <span className="ml-auto text-[10px] bg-slate-800 px-2 py-0.5 rounded-full text-gray-500 group-hover:text-purple-400 transition-colors">{docs.length}</span>
                                    </button>

                                    {openCategories[cat] && (
                                        <div className="ml-6 pl-2 border-l border-white/5 mt-1 space-y-1">
                                            {docs.map(doc => (
                                                <div
                                                    key={doc.id}
                                                    onClick={() => handleDocClick(doc)}
                                                    className={`p-2.5 rounded-lg cursor-pointer transition-all border text-sm flex items-center gap-2 ${selectedDoc?.id === doc.id
                                                        ? 'bg-purple-500/10 border-purple-500/50 text-purple-400'
                                                        : 'border-transparent text-gray-400 hover:text-gray-200 hover:bg-white/5'
                                                        }`}
                                                >
                                                    <FileText className={`w-3.5 h-3.5 ${doc.is_draft ? 'text-amber-500/50' : ''}`} />
                                                    <span className="truncate flex-1">{doc.title}</span>
                                                    {doc.is_draft && <span className="text-[8px] px-1 bg-amber-500/10 text-amber-500 rounded border border-amber-500/20 uppercase font-bold">Draft</span>}
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            ))
                        )}
                    </div>
                </div>

                {/* Right Panel: Content Reading View */}
                <div className="w-2/3 bg-slate-900/30 rounded-xl border border-white/5 flex flex-col overflow-hidden relative backdrop-blur-sm">
                    {selectedDoc ? (
                        <>
                            <div className="p-6 border-b border-white/5 bg-slate-900/50 flex justify-between items-start">
                                <div>
                                    <div className="flex items-center gap-2 mb-2">
                                        <span className="text-[10px] font-bold text-purple-400 uppercase tracking-widest bg-purple-400/10 px-2 py-0.5 rounded">
                                            {selectedDoc.category || "Documentation"}
                                        </span>
                                        {selectedDoc.is_draft && (
                                            <span className="text-[10px] font-bold text-amber-500 uppercase tracking-widest bg-amber-500/10 px-2 py-0.5 rounded animate-pulse">
                                                In Review/Draft
                                            </span>
                                        )}
                                    </div>
                                    <h1 className="text-2xl font-bold text-white mb-2">{selectedDoc.title}</h1>
                                    <div className="flex items-center gap-4 text-[11px] text-gray-500 font-mono">
                                        <span className="flex items-center gap-1">
                                            <Database className="w-3 h-3" />
                                            {selectedDoc.source}
                                        </span>
                                        <span className="flex items-center gap-1">
                                            <FileText className="w-3 h-3" />
                                            {selectedDoc.path}
                                        </span>
                                    </div>
                                </div>
                                {selectedDoc.is_draft && selectedDoc.source === 'Knowledge Base' && (
                                    <button
                                        onClick={() => handleImportToWorkflow(selectedDoc)}
                                        className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-lg transition-all shadow-lg shadow-emerald-500/20"
                                    >
                                        <ChevronRight className="w-4 h-4" />
                                        Import to Workflow
                                    </button>
                                )}
                            </div>

                            <div className="flex-1 overflow-y-auto p-8 custom-markdown bg-slate-950/20 custom-scrollbar">
                                <div className="prose prose-invert prose-slate max-w-none">
                                    <ReactMarkdown
                                        components={{
                                            h1: ({ ...props }) => <h1 className="text-2xl font-bold text-purple-400 mt-6 mb-4 border-b border-white/10 pb-2" {...props} />,
                                            h2: ({ ...props }) => <h2 className="text-xl font-semibold text-white mt-8 mb-4 border-l-4 border-purple-500 pl-4" {...props} />,
                                            h3: ({ ...props }) => <h3 className="text-lg font-medium text-purple-300 mt-6 mb-2" {...props} />,
                                            p: ({ ...props }) => <p className="mb-4 text-gray-400 leading-relaxed text-sm" {...props} />,
                                            ul: ({ ...props }) => <ul className="list-disc pl-6 mb-4 space-y-2 text-gray-400 text-sm" {...props} />,
                                            ol: ({ ...props }) => <ol className="list-decimal pl-6 mb-4 space-y-2 text-gray-400 text-sm" {...props} />,
                                            li: ({ ...props }) => <li className="pl-1" {...props} />,
                                            code: ({ inline, children, ...props }) =>
                                                inline
                                                    ? <code className="bg-slate-800 px-1 py-0.5 rounded text-amber-500 font-mono text-xs" {...props}>{children}</code>
                                                    : <code className="block bg-slate-950 p-4 rounded-lg border border-white/10 text-gray-300 font-mono text-xs overflow-x-auto my-4 leading-relaxed" {...props}>{children}</code>,
                                            blockquote: ({ ...props }) => <blockquote className="border-l-4 border-slate-700 pl-4 italic text-gray-500 my-4" {...props} />
                                        }}
                                    >
                                        {selectedDoc.content || "*No content available*"}
                                    </ReactMarkdown>
                                </div>
                            </div>
                        </>
                    ) : (
                        <EmptyState
                            icon={Book}
                            title="Procedures & Safety Knowledge"
                            description="Select a document from the left to begin review. Use the filters to narrow down by category or title."
                        />
                    )}
                </div>
            </div>
        </div>
    );
};

export default ProceduresExplorer;
