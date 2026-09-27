/* Inline stroke icons. No icon library and no emoji — emoji as UI glyphs is
   one of the clearest tells of a generated interface. */
const S = ({ d, size = 17 }: { d: string; size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
       stroke="currentColor" strokeWidth="1.6"
       strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d={d} />
  </svg>
);

export const Menu = () => <S d="M3 6h18M3 12h18M3 18h18" />;
export const Search = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor"
       strokeWidth="1.8" aria-hidden="true">
    <circle cx="11" cy="11" r="7" /><path d="M20 20l-3.5-3.5" />
  </svg>
);
export const Layers = () => <S d="M12 3l9 5-9 5-9-5 9-5zM3 13l9 5 9-5M3 17l9 5 9-5" />;
export const Report = () => <S d="M7 3h8l4 4v14H7zM15 3v4h4M10 12h6M10 16h6" />;
export const Edit = () => <S d="M4 20h4L19 9a2.1 2.1 0 00-3-3L5 17v3z" />;
export const Kebab = () => <S d="M12 5.5v.01M12 12v.01M12 18.5v.01" />;
export const Eye = () => <S d="M2 12s3.6-6.5 10-6.5S22 12 22 12s-3.6 6.5-10 6.5S2 12 2 12z M12 14.5a2.5 2.5 0 100-5 2.5 2.5 0 000 5z" size={15} />;
export const Check = () => <S d="M4 12.5l5 5L20 6.5" size={14} />;
export const Drone = () => <S d="M5 5l3.5 3.5M19 5l-3.5 3.5M5 19l3.5-3.5M19 19l-3.5-3.5M9 9h6v6H9zM5 5a2 2 0 100-.01M19 5a2 2 0 100-.01M5 19a2 2 0 100-.01M19 19a2 2 0 100-.01" size={18} />;
export const Pin = () => <S d="M12 21s7-6.2 7-11a7 7 0 10-14 0c0 4.8 7 11 7 11z M12 12a2.2 2.2 0 100-4.4 2.2 2.2 0 000 4.4z" />;
export const Poly = () => <S d="M4 7l8-4 8 4v10l-8 4-8-4z" />;
export const Ruler = () => <S d="M3 15L15 3l6 6L9 21zM7 11l2 2M10 8l2 2M13 5l2 2" />;
export const Grid = () => <S d="M3 3h18v18H3zM9 3v18M15 3v18M3 9h18M3 15h18" />;
export const Target = () => <S d="M12 3v3M12 18v3M3 12h3M18 12h3M12 17.5a5.5 5.5 0 100-11 5.5 5.5 0 000 11z" />;
export const Warn = () => <S d="M12 4l9 16H3zM12 10v4M12 17v.01" />;
export const Chart = () => <S d="M4 20V10M10 20V4M16 20v-7M22 20H2" />;
export const Shield = () => <S d="M12 3l8 3v6c0 5-3.4 8.3-8 9.5C7.4 20.3 4 17 4 12V6z M9 12l2 2 4-4" />;
export const Play = () => <S d="M7 4.5l12 7.5-12 7.5z" size={14} />;
export const Undo = () => <S d="M9 7L4 12l5 5M4 12h11a5 5 0 010 10h-2" />;
export const Close = () => <S d="M6 6l12 12M18 6L6 18" size={14} />;
export const Chevron = ({ open }: { open?: boolean }) => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor"
       strokeWidth="2" strokeLinecap="round" aria-hidden="true"
       style={{ transform: open ? "rotate(180deg)" : "none", transition: "transform .15s" }}>
    <path d="M6 9l6 6 6-6" />
  </svg>
);
export const Sun = () => <S d="M12 17a5 5 0 100-10 5 5 0 000 10zM12 1v3M12 20v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M1 12h3M20 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1" size={16} />;
export const Mountain = () => <S d="M3 19l6-9 4 6 2-3 6 6z" size={16} />;
export const Export = () => <S d="M12 15V3M8 7l4-4 4 4M4 15v4a2 2 0 002 2h12a2 2 0 002-2v-4" />;
