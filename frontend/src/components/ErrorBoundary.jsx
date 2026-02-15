import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error(`ErrorBoundary caught an error in ${this.props.name}:`, error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center h-full w-full p-8 text-center bg-white/[0.02] border border-white/5 backdrop-blur-2xl rounded-3xl min-h-[400px]">
          <div className="p-4 rounded-full bg-red-500/10 mb-6 border border-red-500/20">
            <AlertTriangle className="w-12 h-12 text-red-400" />
          </div>
          <h2 className="text-2xl font-mono font-medium text-white mb-4 tracking-tight">
            System Module Failure
          </h2>
          <p className="text-white/60 mb-8 font-mono text-sm max-w-md">
            Something went wrong in <span className="text-red-400 font-bold">{this.props.name || 'Unknown Module'}</span>.
            <br />
            Diagnostic data has been logged.
          </p>
          <button
            onClick={this.handleReset}
            className="px-6 py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-sm font-mono text-white/80 transition-all flex items-center gap-3 group"
          >
            <RefreshCw className="w-4 h-4 group-hover:rotate-180 transition-transform duration-500" />
            REINITIALIZE MODULE
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
