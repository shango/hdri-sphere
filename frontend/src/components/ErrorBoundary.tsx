import { Component, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
  onReset?: () => void;
}

interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: { componentStack?: string | null }): void {
    console.error('ErrorBoundary caught error:', error, info);
  }

  private handleReset = (): void => {
    this.setState({ error: null });
    this.props.onReset?.();
  };

  render(): ReactNode {
    if (!this.state.error) return this.props.children;
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4 p-8">
        <h2 className="text-xl font-semibold">Something went wrong.</h2>
        <pre className="max-w-3xl overflow-auto rounded bg-ink-800 p-4 text-sm text-ink-200">
          {this.state.error.message}
        </pre>
        <button
          type="button"
          onClick={this.handleReset}
          className="rounded bg-accent-500 px-4 py-2 font-medium text-ink-900 hover:bg-accent-600"
        >
          Reset and try another file
        </button>
      </div>
    );
  }
}
