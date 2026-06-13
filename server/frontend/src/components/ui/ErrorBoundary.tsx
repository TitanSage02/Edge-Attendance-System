import React from "react";

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundary extends React.Component<React.PropsWithChildren<{}>, ErrorBoundaryState> {
  constructor(props: React.PropsWithChildren<{}>) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log l'erreur si besoin
    console.error("Erreur capturée par ErrorBoundary :", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 32, textAlign: "center" }}>
          <h1 style={{ color: "#b91c1c", fontSize: 28, marginBottom: 16 }}>Une erreur inattendue est survenue</h1>
          <p style={{ color: "#555", marginBottom: 24 }}>
            Désolé, une erreur s'est produite dans l'application.<br />
            Veuillez recharger la page ou contacter le support si le problème persiste.
          </p>
          <details style={{ whiteSpace: "pre-wrap", color: "#888", fontSize: 14 }}>
            {this.state.error?.toString()}
          </details>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary; 