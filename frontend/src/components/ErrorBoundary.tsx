import { Component, type ReactNode } from 'react';
import { Button } from '@/components/ui/Button';

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
      <div className="flex h-full flex-col items-center justify-center gap-4 p-10">
        <h2 className="text-lg font-semibold text-ink-100">Something went wrong.</h2>
        <pre className="max-w-3xl overflow-auto rounded-md border border-ink-700 bg-ink-900 p-4 text-xs text-ink-300">
          {this.state.error.message}
        </pre>
        <Button variant="primary" onClick={this.handleReset}>
          Reset and try another file
        </Button>
      </div>
    );
  }
}
