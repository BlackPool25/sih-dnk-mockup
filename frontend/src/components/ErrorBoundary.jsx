import React from 'react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    // prevent white-screen; log for debugging
    console.error('ErrorBoundary caught', error, info);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    // hard reload to recover route
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      const fallback = this.props.fallback;
      if (fallback) return fallback;

      return (
        <div className="min-h-screen flex items-center justify-center p-8 bg-[#F8FAF7]">
          <div className="max-w-md w-full bg-white rounded-xl border border-[#E1E7DF] p-6 text-center">
            <h2 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B]">Something went wrong</h2>
            <p className="font-['Figtree'] text-sm text-[#6B7568] mt-2">
              An unexpected error occurred. Your data is safe. Try reloading.
            </p>
            {this.state.error && (
              <pre className="mt-3 text-xs text-left bg-[#F8FAF7] p-2 rounded border overflow-auto max-h-32">
                {String(this.state.error.message || this.state.error)}
              </pre>
            )}
            <button
              onClick={this.handleReset}
              className="mt-4 px-4 py-2 bg-[#A8C3A0] text-[#1B2E1B] rounded-lg font-['Figtree'] text-sm"
            >
              Reload page
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
