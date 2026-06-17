import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import type { KGNode, KGEdge } from '../lib/mockData';

const TYPE_STYLE: Record<string, { fill: string; stroke: string; text: string }> = {
  Event:   { fill: '#FCAF16', stroke: '#a36f00',  text: '#3b2a05' },
  Sector:  { fill: '#7C6CF5', stroke: '#3a31a1',  text: '#fff' },
  Stock:   { fill: '#2A2B86', stroke: '#16175A',  text: '#fff' },
  Leader:  { fill: '#10b981', stroke: '#0a5f44',  text: '#fff' },
};

const EDGE_STYLE: Record<string, { color: string; dash: string }> = {
  IMPACTS_POS:  { color: '#10b981', dash: '0' },
  IMPACTS_NEG:  { color: '#ef4444', dash: '0' },
  AMPLIFIES:    { color: '#ef4444', dash: '0' },
  REDUCES:      { color: '#10b981', dash: '4 4' },
  PRESSURES:    { color: '#f59e0b', dash: '0' },
  BELONGS_TO:   { color: '#cbd5f1', dash: '0' },
  CORRELATES:   { color: '#a3a8d8', dash: '4 3' },
  SUPPLIES:     { color: '#7C6CF5', dash: '0' },
  MANAGES:      { color: '#10b981', dash: '0' },
  INFLUENCES:   { color: '#7C6CF5', dash: '4 3' },
};

interface LayoutNode extends KGNode {
  x: number;
  y: number;
}

interface ForceLayoutOpts {
  cx?: number;
  cy?: number;
  iters?: number;
  linkDist?: number;
  repulsion?: number;
}

function runForceLayout(nodes: KGNode[], edges: KGEdge[], opts: ForceLayoutOpts): LayoutNode[] {
  const N = nodes.length;
  const idx = new Map<string, number>();
  nodes.forEach((n, i) => idx.set(n.id, i));
  
  const pos = nodes.map((n, i) => {
    const ang = (i / N) * Math.PI * 2;
    const radius = 220 + (n.type === 'Stock' ? 90 : 0);
    return {
      x: 500 + Math.cos(ang) * radius + ((i * 53) % 47 - 23),
      y: 320 + Math.sin(ang) * radius + ((i * 71) % 53 - 26),
      vx: 0,
      vy: 0,
    };
  });
  
  const links = edges.map(e => ({
    s: idx.get(e.s)!,
    t: idx.get(e.t)!,
    w: e.w || 0.5
  })).filter(l => l.s !== undefined && l.t !== undefined);

  const iters = opts.iters || 220;
  const center = { x: opts.cx || 500, y: opts.cy || 320 };
  const linkDist = opts.linkDist || 110;
  const repulsion = opts.repulsion || 2400;

  for (let it = 0; it < iters; it++) {
    const cooling = 1 - it / iters;
    // repulsion
    for (let i = 0; i < N; i++) {
      for (let j = i + 1; j < N; j++) {
        const dx = pos[j].x - pos[i].x;
        const dy = pos[j].y - pos[i].y;
        let dist2 = dx*dx + dy*dy;
        if (dist2 < 1) dist2 = 1;
        const dist = Math.sqrt(dist2);
        const force = repulsion / dist2;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        pos[i].vx -= fx; pos[i].vy -= fy;
        pos[j].vx += fx; pos[j].vy += fy;
      }
    }
    // attraction via links (Hooke)
    for (const l of links) {
      const a = pos[l.s], b = pos[l.t];
      const dx = b.x - a.x, dy = b.y - a.y;
      const dist = Math.sqrt(dx*dx + dy*dy) || 1;
      const k = 0.04 * l.w;
      const diff = dist - linkDist;
      const fx = (dx / dist) * diff * k;
      const fy = (dy / dist) * diff * k;
      a.vx += fx; a.vy += fy;
      b.vx -= fx; b.vy -= fy;
    }
    // gravity to center
    for (let i = 0; i < N; i++) {
      pos[i].vx += (center.x - pos[i].x) * 0.003;
      pos[i].vy += (center.y - pos[i].y) * 0.003;
    }
    // integrate
    for (let i = 0; i < N; i++) {
      pos[i].vx *= 0.78 * cooling;
      pos[i].vy *= 0.78 * cooling;
      pos[i].x += pos[i].vx;
      pos[i].y += pos[i].vy;
    }
  }
  return nodes.map((n, i) => ({ ...n, x: pos[i].x, y: pos[i].y }));
}

interface KGViewerProps {
  nodes: KGNode[];
  edges: KGEdge[];
  selectedId: string;
  onSelect: (id: string) => void;
  height?: number;
}

export function KGViewer({ nodes, edges, selectedId, onSelect, height = 600 }: KGViewerProps) {
  const layoutNodes = useMemo(() => runForceLayout(nodes, edges, { cx: 500, cy: height/2, iters: 240 }), [nodes, edges, height]);
  const [pan, setPan] = useState({ x: 0, y: 0, scale: 1 });
  const [drag, setDrag] = useState<{ startX: number, startY: number, panX: number, panY: number } | null>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  function startPan(e: React.MouseEvent<SVGSVGElement>) {
    if (e.button !== 0) return;
    setDrag({ startX: e.clientX, startY: e.clientY, panX: pan.x, panY: pan.y });
  }

  function movePan(e: React.MouseEvent<SVGSVGElement>) {
    if (!drag) return;
    setPan(p => ({ ...p, x: drag.panX + (e.clientX - drag.startX), y: drag.panY + (e.clientY - drag.startY) }));
  }

  function endPan() { setDrag(null); }

  const wheel = useCallback((e: WheelEvent) => {
    e.preventDefault();
    const next = Math.max(0.4, Math.min(2.5, pan.scale * (1 - e.deltaY * 0.0012)));
    setPan(p => ({ ...p, scale: next }));
  }, [pan.scale]);

  useEffect(() => {
    const el = svgRef.current;
    if (!el) return;
    const handler = (e: WheelEvent) => wheel(e);
    el.addEventListener('wheel', handler, { passive: false });
    return () => el.removeEventListener('wheel', handler);
  }, [wheel]);

  const nMap = useMemo(() => new Map<string, LayoutNode>(layoutNodes.map((n) => [n.id, n])), [layoutNodes]);
  
  const linkList = useMemo(() => {
    return edges.map((e) => ({ ...e, a: nMap.get(e.s), b: nMap.get(e.t) })).filter((l): l is (KGEdge & { a: LayoutNode; b: LayoutNode }) => !!l.a && !!l.b);
  }, [edges, nMap]);

  const highlightSet = useMemo(() => {
    const set = new Set<string>();
    if (selectedId) {
      set.add(selectedId);
      for (const e of edges) {
        if (e.s === selectedId) set.add(e.t);
        if (e.t === selectedId) set.add(e.s);
      }
    }
    return set;
  }, [selectedId, edges]);

  const isDim = (id: string) => selectedId && !highlightSet.has(id);

  return (
    <svg
      ref={svgRef}
      viewBox={`0 0 1000 ${height}`}
      onMouseDown={startPan}
      onMouseMove={movePan}
      onMouseUp={endPan}
      onMouseLeave={endPan}
      style={{ width: '100%', height }}
    >
      <defs>
        <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
          <path d="M0,0 L10,5 L0,10 Z" fill="currentColor" />
        </marker>
        <radialGradient id="kgbg" cx="50%" cy="40%" r="80%">
          <stop offset="0%" stopColor="rgba(124,108,245,0.06)" />
          <stop offset="60%" stopColor="rgba(124,108,245,0)" />
        </radialGradient>
      </defs>
      <rect width="1000" height={height} fill="url(#kgbg)" />
      
      <g opacity="0.4">
        {Array.from({ length: 12 }).map((_, i) => (
          <line key={'h'+i} x1="0" x2="1000" y1={i * 60} y2={i * 60} stroke="var(--border-light)" strokeWidth="0.5" />
        ))}
        {Array.from({ length: 20 }).map((_, i) => (
          <line key={'v'+i} x1={i * 60} x2={i * 60} y1="0" y2={height} stroke="var(--border-light)" strokeWidth="0.5" />
        ))}
      </g>

      <g transform={`translate(${pan.x},${pan.y}) scale(${pan.scale})`}>
        {/* edges */}
        {linkList.map((l, i) => {
          const es = EDGE_STYLE[l.kind] || { color: '#a3a8d8', dash: '0' };
          const dim = isDim(l.s) || isDim(l.t);
          const isHL = selectedId && (l.s === selectedId || l.t === selectedId);
          return (
            <g key={i} opacity={dim ? 0.15 : 1}>
              <line
                x1={l.a.x} y1={l.a.y} x2={l.b.x} y2={l.b.y}
                stroke={es.color}
                strokeWidth={isHL ? 2.4 : Math.max(0.8, l.w * 2)}
                strokeDasharray={es.dash}
                opacity={isHL ? 1 : 0.55}
              />
            </g>
          );
        })}

        {/* nodes */}
        {layoutNodes.map((n) => {
          const st = TYPE_STYLE[n.type] || TYPE_STYLE.Stock;
          const dim = isDim(n.id);
          const isSel = n.id === selectedId;
          const r = n.size || 18;
          return (
            <g key={n.id} transform={`translate(${n.x},${n.y})`} opacity={dim ? 0.25 : 1} style={{ cursor: 'pointer' }} onClick={(e) => { e.stopPropagation(); onSelect(n.id); }}>
              {isSel && <circle r={r + 8} fill="none" stroke={st.fill} strokeWidth="2" opacity="0.5" />}
              {n.type === 'Stock' ? (
                <rect x={-r} y={-r * 0.55} width={r * 2} height={r * 1.1} rx="4" fill={st.fill} stroke={st.stroke} strokeWidth="1.2" />
              ) : (
                <circle r={r} fill={st.fill} stroke={st.stroke} strokeWidth="1.2" />
              )}
              
              {n.type === 'Stock' && (
                <text
                  textAnchor="middle"
                  dominantBaseline="central"
                  fontSize="10"
                  fontWeight="700"
                  fill={st.text}
                  fontFamily="var(--font-mono)"
                  style={{ pointerEvents: 'none' }}
                >
                  {n.label}
                </text>
              )}
              {n.type === 'Event' && (
                <text
                  textAnchor="middle"
                  dominantBaseline="central"
                  fontSize="9"
                  fontWeight="800"
                  fill={st.text}
                  fontFamily="var(--font-mono)"
                  style={{ pointerEvents: 'none' }}
                >
                  {n.short || n.label.slice(0, 3).toUpperCase()}
                </text>
              )}
              {n.type === 'Sector' && (
                <text
                  textAnchor="middle"
                  dominantBaseline="central"
                  fontSize="11"
                  fontWeight="700"
                  fill={st.text}
                  fontFamily="var(--font-body)"
                  style={{ pointerEvents: 'none' }}
                >
                  {n.label.length > 8 ? n.label.split(' ').map(w => w[0]).join('').toUpperCase() : n.label}
                </text>
              )}
              {n.type === 'Leader' && (
                <text
                  textAnchor="middle"
                  dominantBaseline="central"
                  fontSize="9"
                  fontWeight="700"
                  fill={st.text}
                  fontFamily="var(--font-body)"
                  style={{ pointerEvents: 'none' }}
                >
                  {n.label.split(' ').map(w => w[0]).join('').slice(0, 3).toUpperCase()}
                </text>
              )}
              
              {n.type !== 'Stock' && (
                <text
                  textAnchor="middle"
                  y={r + 14}
                  fontSize="10.5"
                  fill="var(--fg-1)"
                  fontFamily="var(--font-body)"
                  fontWeight="500"
                  style={{ pointerEvents: 'none' }}
                >
                  {n.label}
                </text>
              )}
            </g>
          );
        })}
      </g>
    </svg>
  );
}
