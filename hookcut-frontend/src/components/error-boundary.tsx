"use client";

import React from "react";

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export class ErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("[ErrorBoundary] Caught error:", error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-[60vh] flex items-center justify-center px-6">
          <div
            className="max-w-md w-full rounded-2xl p-8 text-center"
            style={{
              background: "rgba(6, 6, 14, 0.85)",
              backdropFilter: "blur(24px) saturate(1.4)",
              border: "1px solid rgba(255, 255, 255, 0.06)",
              boxShadow: "0 8px 40px rgba(0, 0, 0, 0.5)",
            }}
          >
            {/* Error icon */}
            <div className="w-14 h-14 rounded-2xl bg-red-500/10 border border-red-500/15 flex items-center justify-center mx-auto mb-5">
              <svg
                className="w-7 h-7 text-red-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
                />
              </svg>
            </div>

            <h2 className="text-xl font-bold text-white/90 mb-2">
              Something went wrong
            </h2>
            <p className="text-sm text-white/40 mb-6 leading-relaxed">
              An unexpected error occurred while rendering this page. You can
              try again or refresh the page.
            </p>

            {/* Error details (collapsed) */}
            {this.state.error && (
              <div className="mb-6 p-3 rounded-xl bg-red-500/[0.05] border border-red-500/10 text-left">
                <p className="text-xs text-red-400/70 font-mono break-all">
                  {this.state.error.message}
                </p>
              </div>
            )}

            <button
              onClick={this.handleReset}
              className="btn-primary text-sm inline-flex items-center gap-2"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              Try Again
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
