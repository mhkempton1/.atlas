import React, { useState, useEffect } from 'react';
import {
    Search, Book, FileText, ChevronRight, ChevronDown,
    Sparkles, Command, Zap, Layers, Info, RefreshCw, Database
} from 'lucide-react';
import { SYSTEM_API } from '../../services/api';
import ReactMarkdown from 'react-markdown';
import { PageHeader, Spinner, EmptyState } from '../shared/UIComponents';
import { motion as Motion, AnimatePresence } from 'framer-motion';

const KnowledgeDashboard = () => {
    const [documents, setDocuments] = useState([]);
    const [searchResults, setSearchResults] = useState(null);
    const [selectedDoc, setSelectedDoc] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [activeTab, setActiveTab] = useState('browse'); // browse, search

    // Initial Load
    useEffect(() => {
        loadDocuments();
    }, []);

    // Reactive URL parameter handling (Deep Linking)
    useEffect(() => {
        const handleDeepLink = async () => {
            const params = new URLSearchParams(window.location.search);
            const pathFilter = params.get('path');

            if (pathFilter && documents.length > 0) {
                // 1. Try to find in already loaded documents
                const doc = documents.find(d => d.path === pathFilter || d.id === pathFilter || d.full_path === pathFilter);
                if (doc) {
                    handleDocClick(doc);
                } else {
                    // 2. Fallback: Load content directly if it's a raw path
                    try {
                        setIsLoading(true);
                        const content = await SYSTEM_API.getKnowledgeContent(pathFilter);
                        setSelectedDoc({
                            id: 'temp-' + Date.now(),
                            path: pathFilter,
                            content,
                            title: pathFilter.split('/').pop().replace('.md', ''),
                            category: 'Direct Link'
                        });
                    } catch (e) {
                        console.error("Direct link load failed", e);
                    } finally {
                        setIsLoading(false);
                    }
                }
            }
        };

        handleDeepLink();

        // Listen for internal navigation events
        window.addEventListener('popstate', handleDeepLink);
        return () => window.removeEventListener('popstate', handleDeepLink);
    }, [documents]);

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

    const handleSearch = async (e) => {
        if (e) e.preventDefault();
        if (!searchQuery.trim()) {
            setSearchResults(null);
            return;
        }

        setIsLoading(true);
        setActiveTab('search');
        try {
            const results = await SYSTEM_API.searchKnowledge(searchQuery);
            setSearchResults(results);
        } catch (error) {
            console.error("Semantic search failed", error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleDocClick = async (doc) => {
        try {
            setIsLoading(true);
            const content = await SYSTEM_API.getKnowledgeContent(doc.path || doc.full_path || doc.metadata?.full_path);
            setSelectedDoc({ ...doc, content });
        } catch (error) {
            console.error("Failed to load content", error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleReindex = async () => {
        if (!confirm("Reindexing will scan all documents and update the search index. This may take a moment. Continue?")) return;

        setIsLoading(true);
        try {
            await SYSTEM_API.reindexKnowledgeBase();
            await loadDocuments(); // Reload list
            alert("Knowledge Base reindexed successfully.");
        } catch (error) {
            alert("Reindexing failed: " + error.message);
        } finally {
            setIsLoading(false);
        }
    };

    const Folder = ({ name, children, depth = 0 }) => {
        const [isExpanded, setIsExpanded] = useState(depth === 0);
        return (
            <div className="select-none">
                <div
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="flex items-center gap-2 p-2 hover:bg-white/5 rounded-lg cursor-pointer group"
                    style={{ paddingLeft: `${(depth * 12) + 8}px` }}
                >
                    {isExpanded ? <ChevronDown className="w-3.5 h-3.5 text-slate-500" /> : <ChevronRight className="w-3.5 h-3.5 text-slate-500" />}
                    <Book className={`w-3.5 h-3.5 ${isExpanded ? 'text-purple-400' : 'text-slate-500'}`} />
                    <span className={`text-[11px] font-bold uppercase tracking-wider ${isExpanded ? 'text-white' : 'text-slate-400 group-hover:text-slate-200'}`}>{name}</span>
                </div>
                {isExpanded && <div className="mt-1">{children}</div>}
            </div>
        );
    };

    const buildTree = (docs) => {
        const tree = {};
        docs.forEach(doc => {
            const parts = (doc.category || 'General').split('/');
            let current = tree;
            parts.forEach(part => {
                if (!current[part]) current[part] = { _docs: [], _sub: {} };
                current = current[part]._sub;
            });
            // Re-find the leaf node to add the doc
            let leaf = tree;
            parts.forEach(part => leaf = leaf[part]);
            leaf._docs.push(doc);
        });
        return tree;
    };

    const renderTree = (node, depth = 0) => {
        return Object.entries(node).map(([name, data]) => (
            <Folder key={name} name={name} depth={depth}>
                {Object.keys(data._sub).length > 0 && renderTree(data._sub, depth + 1)}
                {data._docs.map(doc => (
                    <div
                        key={doc.id}
                        onClick={() => handleDocClick(doc)}
                        className={`flex items-center gap-3 p-2 rounded-lg transition-all cursor-pointer group mb-1 ${selectedDoc?.id === doc.id ? 'bg-purple-600/20 text-white' : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'}`}
                        style={{ marginLeft: `${((depth + 1) * 12) + 8}px` }}
                    >
                        <FileText className={`w-3.5 h-3.5 ${selectedDoc?.id === doc.id ? 'text-purple-400' : 'text-slate-600'}`} />
                        <span className="text-xs truncate">{doc.title}</span>
                    </div>
                ))}
            </Folder>
        ));
    };

    return (
        <div className="h-full flex flex-col space-y-6 animate-slide-in p-6">
            <PageHeader
                icon={Book}
                title="Knowledge Strategy"
                subtitle="Semantic Intelligence & Procedure Repository"
            >
                <button
                    onClick={handleReindex}
                    className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-purple-500/10 text-purple-400 hover:bg-purple-500/20 text-xs font-bold uppercase tracking-wider border border-purple-500/30 transition-all"
                >
                    <RefreshCw className="w-3.5 h-3.5" /> Reindex
                </button>
            </PageHeader>

            <div className="grid grid-cols-1 md:grid-cols-12 gap-6 flex-1 overflow-hidden">
                {/* Left Panel */}
                <div className="md:col-span-4 flex flex-col space-y-4 overflow-hidden">
                    <div className="glass-panel p-4 rounded-2xl border border-white/10 bg-white/[0.02] backdrop-blur-xl">
                        <form onSubmit={handleSearch} className="relative group">
                            <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none">
                                <Sparkles className="w-4 h-4 text-purple-400 group-focus-within:animate-pulse" />
                            </div>
                            <input
                                type="text"
                                className="w-full bg-white/[0.02] border border-white/10 rounded-xl pl-10 pr-4 py-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-purple-500/30 transition-all placeholder:text-slate-600 backdrop-blur-sm"
                                placeholder="Ask Atlas about procedures..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                            />
                        </form>
                        <div className="flex items-center gap-2 mt-4 px-2">
                            <button
                                onClick={() => setActiveTab('browse')}
                                className={`flex-1 py-1.5 text-[10px] font-bold uppercase tracking-widest rounded-lg border transition-all ${activeTab === 'browse' ? 'bg-white/10 border-white/20 text-white' : 'text-slate-500 border-transparent hover:text-slate-300'}`}
                            >
                                <Layers className="w-3 h-3 inline-block mr-1" /> Browse
                            </button>
                            <button
                                onClick={() => setActiveTab('search')}
                                className={`flex-1 py-1.5 text-[10px] font-bold uppercase tracking-widest rounded-lg border transition-all ${activeTab === 'search' ? 'bg-purple-500/20 border-purple-500/30 text-purple-400' : 'text-slate-500 border-transparent hover:text-slate-300'}`}
                            >
                                <Command className="w-3 h-3 inline-block mr-1" /> Semantic
                            </button>
                        </div>
                    </div>

                    <div className="flex-1 overflow-y-auto space-y-2 custom-scrollbar glass-panel rounded-2xl p-2 bg-white/[0.01] border border-white/5">
                        <AnimatePresence mode="wait">
                            {isLoading ? (
                                <Motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="p-8"><Spinner label="Consulting Codex..." /></Motion.div>
                            ) : activeTab === 'search' ? (
                                <Motion.div key="search-results" initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} className="space-y-3 p-2">
                                    {searchResults?.length > 0 ? searchResults.map(res => (
                                        <div key={res.id} onClick={() => handleDocClick(res)} className={`p-4 rounded-xl border transition-all cursor-pointer group ${selectedDoc?.id === res.id ? 'bg-purple-500/10 border-purple-500/40 transform scale-[1.02]' : 'bg-white/[0.02] border-white/5 hover:border-white/20'}`}>
                                            <div className="flex justify-between items-start mb-2">
                                                <span className="text-[9px] font-black text-purple-400 uppercase tracking-tighter bg-purple-400/10 px-1.5 py-0.5 rounded">Match Score: {(1 - res.score).toFixed(2)}</span>
                                                {getIcon(res.metadata?.category)}
                                            </div>
                                            <h4 className="text-sm font-semibold text-white group-hover:text-purple-300 transition-colors">{res.metadata?.title}</h4>
                                            <p className="text-[11px] text-slate-500 mt-1 line-clamp-2 italic">"...{res.content_snippet}..."</p>
                                        </div>
                                    )) : <div className="text-center p-8 text-slate-600 italic text-sm">No semantic matches found.</div>}
                                </Motion.div>
                            ) : (
                                <Motion.div key="browse-list" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-1">
                                    {renderTree(buildTree(documents))}
                                </Motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                </div>

                {/* Right Panel: Content View */}
                <div className="md:col-span-8 flex flex-col overflow-hidden bg-white/[0.01] border border-white/5 rounded-3xl relative backdrop-blur-md shadow-2xl">
                    <AnimatePresence mode="wait">
                        {selectedDoc ? (
                            <Motion.div
                                key={selectedDoc.id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -20 }}
                                className="h-full flex flex-col"
                            >
                                <div className="p-8 border-b border-white/5 bg-white/[0.02]">
                                    <div className="flex items-center gap-2 mb-4">
                                        <span className="px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/20 text-[10px] font-bold text-purple-400 uppercase tracking-widest">
                                            {selectedDoc.category || selectedDoc.metadata?.category || "Standard Procedure"}
                                        </span>
                                        <span className="flex items-center gap-1.5 text-[10px] font-mono text-slate-500 bg-white/[0.05] px-3 py-1 rounded-full">
                                            <Database className="w-3 h-3" />
                                            {selectedDoc.source || selectedDoc.metadata?.source || "Internal Store"}
                                        </span>
                                    </div>
                                    <h2 className="text-3xl font-black text-white tracking-tight leading-none mb-4">
                                        {selectedDoc.title || selectedDoc.metadata?.title}
                                    </h2>
                                </div>

                                <div className="flex-1 overflow-y-auto p-10 custom-scrollbar bg-transparent">
                                    <div className="prose prose-invert prose-slate max-w-none prose-headings:text-purple-400 prose-strong:text-amber-500 prose-code:text-emerald-400 prose-code:bg-white/5 prose-code:rounded prose-code:px-1">
                                        <ReactMarkdown
                                            components={{
                                                h1: ({ ...props }) => <h1 className="text-3xl font-black mb-8 pb-4 border-b border-white/10" {...props} />,
                                                h2: ({ ...props }) => <h2 className="text-xl font-bold mt-10 mb-4 flex items-center gap-3"><Info className="w-5 h-5 text-purple-500" />{props.children}</h2>,
                                                p: ({ ...props }) => <p className="text-slate-400 leading-relaxed mb-6" {...props} />,
                                                ul: ({ ...props }) => <ul className="list-disc pl-5 space-y-3 mb-6 border-l border-white/5" {...props} />,
                                                li: ({ ...props }) => <li className="text-slate-400 marker:text-purple-500" {...props} />,
                                                blockquote: ({ ...props }) => (
                                                    <div className="my-8 p-6 bg-white/[0.02] border-l-4 border-amber-500/50 rounded-r-xl italic text-slate-300 backdrop-blur-sm">
                                                        {props.children}
                                                    </div>
                                                )
                                            }}
                                        >
                                            {selectedDoc.content || "*Initializing vector content...*"}
                                        </ReactMarkdown>
                                    </div>
                                </div>
                            </Motion.div>
                        ) : (
                            <div className="h-full flex items-center justify-center p-12 text-center">
                                <Motion.div
                                    initial={{ opacity: 0, scale: 0.9 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    className="max-w-md"
                                >
                                    <div className="mb-6 inline-flex p-6 rounded-3xl bg-white/[0.02] border border-white/5 relative backdrop-blur-sm">
                                        <Book className="w-16 h-16 text-slate-700" />
                                        <div className="absolute -top-2 -right-2 p-2 rounded-xl bg-purple-600 border border-purple-400 animate-bounce">
                                            <Sparkles className="w-4 h-4 text-white" />
                                        </div>
                                    </div>
                                    <h3 className="text-xl font-bold text-white mb-2">Knowledge Base Idle</h3>
                                    <p className="text-slate-500 text-sm italic">
                                        Select a specific document or perform a semantic query to explore company SOPs, safety talks, and technical training modules.
                                    </p>
                                </Motion.div>
                            </div>
                        )}
                    </AnimatePresence>
                </div>
            </div>
        </div>
    );
};

export default KnowledgeDashboard;
