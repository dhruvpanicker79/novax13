import { useEffect } from "react";
import MapView from "./components/MapView";
import Dock from "./components/Dock";
import { TopBar, Rail, Readout } from "./components/Chrome";
import { SourceCards } from "./components/Panels";
import DemoMode from "./components/DemoMode";
import Palette from "./components/Palette";
import SignIn from "./components/SignIn";
import { Boundary, OfflineBanner } from "./components/Guards";
import { useStore } from "./lib/store";

export default function App() {
  const { load, loaded, error, toggleLayer, layers, setDockTab, playAlignment,
          runPipeline, selectConflict, conflicts, selectedConflict,
          signedIn } = useStore();

  useEffect(() => { load(); }, []);

  // Keyboard-first: a GIS operator's hands stay on the keyboard.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.target as HTMLElement)?.tagName === "INPUT") return;
      const n = Number(e.key);
      if (n >= 1 && n <= layers.length) { toggleLayer(layers[n - 1].id); return; }
      if (e.key === " ") { e.preventDefault(); runPipeline(); }
      if (e.key === "\\") playAlignment();
      if (e.key === "[" || e.key === "]") {
        const open = conflicts.filter((c) => c.status === "open");
        if (!open.length) return;
        const i = open.findIndex((c) => c.id === selectedConflict);
        const j = e.key === "]" ? (i + 1) % open.length
                                : (i <= 0 ? open.length - 1 : i - 1);
        selectConflict(open[j].id);
      }
      if (e.key === "Escape") { useStore.getState().select(null); selectConflict(null); }
      if (e.key === "c") setDockTab("conflicts");
      if (e.key === "v") setDockTab("validate");
      if (e.key === "t") setDockTab("survey");
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [layers, conflicts, selectedConflict]);

  return (
    <div className="app">
      <TopBar />
      <div className="body">
        <Rail />
        <div className="stage">
          <Boundary label="Map"><MapView /></Boundary>
          <OfflineBanner />
          {loaded && signedIn && <Boundary label="Demo mode"><DemoMode /></Boundary>}
          {loaded && signedIn && <Boundary label="Command palette"><Palette /></Boundary>}
          {loaded && !signedIn && <Boundary label="Sign in"><SignIn /></Boundary>}
          {loaded && <Boundary label="Panels"><SourceCards /></Boundary>}
          <Readout />
          {loaded && <Boundary label="Data dock"><Dock /></Boundary>}
          {!loaded && !error && (
            <div style={{ position: "absolute", inset: 0, display: "grid",
                          placeItems: "center", color: "var(--ink-faint)" }}>
              <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: 13 }}>Loading harmonization artifacts…</div>
                <div style={{ fontSize: 11, marginTop: 6 }}>
                  3,047 parcels · 50k candidate pairs
                </div>
              </div>
            </div>
          )}
          {error && (
            <div style={{ position: "absolute", inset: 0, display: "grid",
                          placeItems: "center" }}>
              <div className="card" style={{ padding: 20, maxWidth: 440 }}>
                <div style={{ color: "var(--crit)", fontWeight: 600, marginBottom: 6 }}>
                  Could not load pipeline artifacts
                </div>
                <div className="num" style={{ fontSize: 12, color: "var(--ink-dim)" }}>
                  {error}
                </div>
                <div style={{ fontSize: 12, color: "var(--ink-faint)", marginTop: 10,
                              lineHeight: 1.6 }}>
                  Run <span className="num">PYTHONPATH=backend python
                  scripts/build_demo.py</span> and copy <span className="num">data/demo</span>
                  {" "}into <span className="num">frontend/public/data</span>.
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
