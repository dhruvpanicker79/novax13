/**
 * KSHETRA mark.
 *
 * kshetra (क्षेत्र) is Sanskrit for field, area, domain — so the mark is a
 * parcel being subdivided: an outer holding, a boundary drawn through it, and
 * a survey control point at the intersection. That is literally what the
 * system does, and it stays legible at 18px in a toolbar, which a more
 * pictorial mark would not.
 *
 * Geometry only, no gradients, no rounded corners — it should read as
 * something a survey office would put on a document.
 */
export function Logo({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none"
         aria-hidden="true" style={{ display: "block", flex: "0 0 auto" }}>
      {/* parent holding */}
      <rect x="2.5" y="2.5" width="27" height="27" rx="1"
            stroke="currentColor" strokeWidth="2" />
      {/* the subdivision: one cut vertical, one horizontal, meeting off-centre
          the way a real plot split does rather than quartering it */}
      <path d="M12.5 2.5V29.5" stroke="currentColor" strokeWidth="1.6"
            opacity="0.75" />
      <path d="M12.5 19H29.5" stroke="currentColor" strokeWidth="1.6"
            opacity="0.75" />
      {/* the surveyed corner */}
      <circle cx="12.5" cy="19" r="3.6" fill="var(--acc)" />
      <circle cx="12.5" cy="19" r="1.35" fill="#fff" />
    </svg>
  );
}

/** Full lockup for the sign-in screen: mark, name, and what it is. */
export function LogoLockup({ size = 46 }: { size?: number }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
      <span style={{ color: "var(--ink)" }}><Logo size={size} /></span>
      <div>
        <div style={{
          fontSize: size * 0.62, fontWeight: 600, letterSpacing: "0.05em",
          lineHeight: 1.05,
        }}>
          KSHETRA
        </div>
        <div style={{
          fontSize: 11, color: "var(--ink-faint)", letterSpacing: "0.11em",
          textTransform: "uppercase", marginTop: 3,
        }}>
          Cadastral Harmonization
        </div>
      </div>
    </div>
  );
}
