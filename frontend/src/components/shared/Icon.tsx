import React from 'react';

const ICONS: Record<string, string> = {
  dashboard: 'M3 13h8V3H3v10zM13 21h8V11h-8v10zM3 21h8v-6H3v6zM13 3v6h8V3h-8z',
  graph: 'M5 5a3 3 0 1 0 0 6 3 3 0 0 0 0-6zm14 0a3 3 0 1 0 0 6 3 3 0 0 0 0-6zM12 14a3 3 0 1 0 0 6 3 3 0 0 0 0-6zM7 8l4 4M17 8l-4 4',
  stock: 'M3 3v18h18M7 14l4-4 4 4 6-6',
  news: 'M4 4h13v16H4zM7 8h7M7 12h7M7 16h5M17 8h3v10a2 2 0 0 1-2 2',
  chat: 'M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z',
  bell: 'M18 16v-5a6 6 0 0 0-12 0v5l-2 2v1h16v-1zM10 21a2 2 0 0 0 4 0',
  pipe: 'M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6zM10 7h4M10 17h4M7 10v4M17 10v4',
  cog: 'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zm9 5l-2-1 1-2-2-2-2 1-1-2h-3l-1 2-2-1-2 2 1 2-2 1v3l2 1-1 2 2 2 2-1 1 2h3l1-2 2 1 2-2-1-2 2-1z',
  search: 'M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14zm5.5 12L21 21',
  ext: 'M14 3h7v7M10 14L21 3M19 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h6',
  filter: 'M4 4h16l-6 8v6l-4 2v-8z',
  refresh: 'M3 12a9 9 0 0 1 15.5-6.36L21 8M21 4v4h-4M21 12a9 9 0 0 1-15.5 6.36L3 16M3 20v-4h4',
  plus: 'M12 5v14M5 12h14',
  caret: 'M6 9l6 6 6-6',
  caretR: 'M9 6l6 6-6 6',
  check: 'M5 12l5 5L20 7',
  x: 'M6 6l12 12M6 18L18 6',
  send: 'M22 2L11 13M22 2l-7 20-4-9-9-4z',
  bolt: 'M13 2L3 14h7l-1 8 10-12h-7z',
  shield: 'M12 2L4 5v6c0 5 3.5 9.4 8 11 4.5-1.6 8-6 8-11V5z',
  doc: 'M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9zM14 3v6h6',
  fire: 'M12 22c4 0 8-3 8-8 0-5-4-7-4-12 0 0-4 4-4 8 0-2-2-3-2-3s-6 4-6 9 4 6 8 6z',
  trend: 'M3 17l6-6 4 4 8-8M14 7h7v7',
  trendDown: 'M3 7l6 6 4-4 8 8M14 17h7v-7',
  globe: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18',
  zap: 'M13 2L3 14h7l-1 8 10-12h-7z',
  user: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM4 21v-1a6 6 0 0 1 6-6h4a6 6 0 0 1 6 6v1',
  logout: 'M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9',
  copy: 'M16 3H8a2 2 0 0 0-2 2v10h2V5h8zM20 7H12a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2z',
  database: 'M12 3c-4.4 0-8 1.3-8 3v12c0 1.7 3.6 3 8 3s8-1.3 8-3V6c0-1.7-3.6-3-8-3zM4 6c0 1.7 3.6 3 8 3s8-1.3 8-3M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3',
  link: 'M10 14a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1M14 10a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1',
  sparkle: 'M12 2l2 6 6 2-6 2-2 6-2-6-6-2 6-2zM19 14l1 3 3 1-3 1-1 3-1-3-3-1 3-1z',
  more: 'M5 12h.01M12 12h.01M19 12h.01',
  arrowR: 'M5 12h14M13 5l7 7-7 7',
  alert: 'M12 9v4M12 17h.01M10.3 3.86L1.82 18a2 2 0 0 0 1.72 3h16.92a2 2 0 0 0 1.72-3L13.71 3.86a2 2 0 0 0-3.42 0z',
  download: 'M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3',
  key: 'M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4',
  mail: 'M4 6h16a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2zM22 8l-10 7L2 8',
  clock: 'M12 6v6l4 2M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z',
  lock: 'M5 11h14v10H5zM8 11V7a4 4 0 0 1 8 0v4',
  server: 'M3 4h18v6H3zM3 14h18v6H3zM7 7h.01M7 17h.01M11 7h6M11 17h6',
  upload: 'M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12',
  rotate: 'M21 2v6h-6M3 12a9 9 0 0 1 15-6.7L21 8M3 22v-6h6M21 12a9 9 0 0 1-15 6.7L3 16',
  webhook: 'M18 16.98h-5.99c-1.1 0-1.95.94-2.48 1.9A4 4 0 1 1 2 16h.5M14 7a4 4 0 1 1 8 0 4 4 0 0 1-8 0zM10.46 6.46a4 4 0 1 0-5.92 5.39M14.5 17.5l-2.5-4.33',
  trash: 'M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m3 0v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6h14zM10 11v6M14 11v6',
  eye: 'M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7zM12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z',
  eyeOff: 'M17.94 17.94A10.1 10.1 0 0 1 12 19c-6.5 0-10-7-10-7a16.7 16.7 0 0 1 4.06-5.06M9.9 4.24A9.1 9.1 0 0 1 12 4c6.5 0 10 7 10 7a16.7 16.7 0 0 1-1.51 2.36M1 1l22 22M14.12 14.12A3 3 0 1 1 9.88 9.88',
  edit: 'M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z',
};

interface IconProps {
  name?: string;
  k?: string;
  size?: number;
  stroke?: number;
  className?: string;
  style?: React.CSSProperties;
}

export function Icon({ name, k, size = 16, stroke = 1.75, className, style }: IconProps) {
  const iconName = name || k;
  if (!iconName) return null;
  const d = ICONS[iconName];
  if (!d) return null;
  return (
    <span className={className} style={{ display: 'inline-flex', width: size, height: size, ...style }}>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round">
        <path d={d} />
      </svg>
    </span>
  );
}

export { ICONS };
