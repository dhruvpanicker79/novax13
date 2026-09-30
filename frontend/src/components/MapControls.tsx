import { useStore } from "../lib/store";
import * as I from "../lib/icons";

/**
 * Map controls, docked bottom-right above the scale bar.
 *
 * Basemap and camera are view settings, not data layers, so they sit on the
 * map rather than in the layer tree — mixing "what am I looking at" with
 * "what is drawn" is what makes GIS layer panels unusable.
 */
export default function MapControls() {
  const { basemap, setBasemap, pitched, setPitched, layers, toggleLayer,
          dockOpen } = useStore();

  const conf = layers.find((l) => l.id === "confidence")!;
  const legacy = layers.find((l) => l.id === "legacy")!;

  const Btn = ({ on, onClick, title, children, wide }: any) => (
    <button
      onClick={onClick}
      title={title}
      style={{
        padding: wide ? "5px 10px" : "5px 8px",
        fontSize: 11.5, fontWeight: on ? 600 : 400,
        borderRadius: 3,
        border: `1px solid ${on ? "var(--acc)" : "var(--line)"}`,
        background: on ? "var(--acc)" : "var(--panel)",
        color: on ? "var(--on-acc)" : "var(--ink-dim)",
        display: "flex", alignItems: "center", gap: 5, whiteSpace: "nowrap",
      }}>
      {children}
    </button>
  );

  return (
    <div style={{
      position: "absolute", right: 10, zIndex: 26,
      // The dock occupies the bottom ~46% when open, so a fixed offset
      // puts these controls underneath it and out of reach.
      bottom: dockOpen ? "calc(46% + 16px)" : 58,
      display: "flex", flexDirection: "column", gap: 6, alignItems: "flex-end",
    }}>
      <div style={{ display: "flex", gap: 4, padding: 4,
                    background: "rgba(255,255,255,.93)",
                    border: "1px solid var(--line)", borderRadius: 4,
                    boxShadow: "0 1px 3px rgba(23,27,32,.12)" }}>
        {(["imagery", "light", "dark"] as const).map((b) => (
          <Btn key={b} on={basemap === b} onClick={() => setBasemap(b)}
               title={`${b} basemap`} wide>
            {b === "imagery" ? "Imagery" : b === "light" ? "Canvas" : "Dark"}
          </Btn>
        ))}
      </div>

      <div style={{ display: "flex", gap: 4, padding: 4,
                    background: "rgba(255,255,255,.93)",
                    border: "1px solid var(--line)", borderRadius: 4,
                    boxShadow: "0 1px 3px rgba(23,27,32,.12)" }}>
        <Btn on={pitched} onClick={() => setPitched(!pitched)}
             title="Tilt the camera and extrude buildings to their surveyed height  (p)"
             wide>
          <I.Mountain /> 3D
        </Btn>
        <Btn on={conf.on} onClick={() => toggleLayer("confidence")}
             title="Shade every parcel by its calibrated confidence" wide>
          Confidence
        </Btn>
        <Btn on={legacy.on} onClick={() => toggleLayer("legacy")}
             title="Show the 1987 sheet over the harmonized output" wide>
          Legacy
        </Btn>
      </div>
    </div>
  );
}
