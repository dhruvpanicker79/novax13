import { Component, type ReactNode } from "react";
import { useStore } from "../lib/store";

/**
 * Keeps one failing panel from taking the whole application down.
 *
 * Without this, an exception anywhere in the tree unmounts everything and the
 * operator is left with a white page and no way back. A demo does not get a
 * second chance at that. The map and the rest of the chrome stay alive; only
 * the broken panel is replaced, and it says what broke.
 */
export class Boundary extends Component<
  { children: ReactNode; label: string },
  { error: Error | null }
> {
  state: { error: Error | null } = { error: null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  componentDidCatch(error: Error, info: unknown) {
    console.error(`[${this.props.label}]`, error, info);
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div style={{ padding: "14px 16px", fontSize: 12,
                    color: "var(--ink-dim)" }}>
        <div style={{ color: "var(--crit)", fontWeight: 600, marginBottom: 5 }}>
          {this.props.label} could not render
        </div>
        <div className="num" style={{ fontSize: 11, marginBottom: 8 }}>
          {this.state.error.message}
        </div>
        <button
          onClick={() => this.setState({ error: null })}
          style={{ border: "1px solid var(--line)", borderRadius: 3,
                   padding: "5px 11px", fontSize: 12,
                   background: "var(--panel-hi)" }}>
          Retry this panel
        </button>
        <div style={{ fontSize: 11, color: "var(--ink-faint)", marginTop: 8 }}>
          Everything else, including the map, is unaffected.
        </div>
      </div>
    );
  }
}

/** Tells the operator the basemap is unreachable rather than letting them
 *  wonder why the imagery vanished. Vector layers are unaffected, and saying
 *  so is the point: the analysis does not depend on the tiles. */
export function OfflineBanner() {
  const offline = useStore((s) => s.basemapOffline);
  if (!offline) return null;
  return (
    <div className="float" style={{
      top: 10, left: "50%", transform: "translateX(-50%)",
      background: "var(--warn-ghost)", border: "1px solid var(--warn)",
      borderRadius: 3, padding: "6px 13px", fontSize: 12,
      color: "var(--warn)", display: "flex", alignItems: "center", gap: 9,
      boxShadow: "0 2px 8px rgba(23,27,32,.12)",
    }}>
      <span style={{ fontWeight: 600 }}>Basemap offline</span>
      <span style={{ color: "var(--ink-dim)" }}>
        satellite tiles unreachable — all cadastral layers and analysis
        are unaffected
      </span>
    </div>
  );
}
