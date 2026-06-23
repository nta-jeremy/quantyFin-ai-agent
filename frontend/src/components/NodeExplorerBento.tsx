import React, { useState, useMemo, useCallback } from 'react';
import { KGViewer } from './KGViewer';
import { Icon } from '@/components/shared';
import { KG_NODES, KG_EDGES } from '../lib/mockData';
import type { KGNode, KGEdge } from '../lib/mockData';

// ── helpers ──────────────────────────────────────────────────────────

/** Deterministic pseudo-random sentiment score từ nodeId */
function mockSentimentForNode(nodeId: string): number {
  let hash = 0;
  for (let i = 0; i < nodeId.length; i++) {
    hash = (hash * 31 + nodeId.charCodeAt(i)) | 0;
  }
  const normalized = ((hash >>> 0) % 1000) / 1000;
  return +(normalized * 1.8 - 0.9).toFixed(2);
}

/** Deterministic mock nguồn bài báo từ nodeId */
function mockNewsSourceForNode(nodeId: string): string {
  const sources = ['VnExpress', 'Vietstock', 'Cafef', 'Tin nhanh chứng khoán', 'Báo Đầu tư'];
  let hash = 0;
  for (let i = 0; i < nodeId.length; i++) {
    hash = (hash * 31 + nodeId.charCodeAt(i)) | 0;
  }
  return sources[Math.abs(hash) % sources.length];
}

function sentimentColor(score: number): string {
  if (score > 0.1) return 'var(--mint)';
  if (score < -0.1) return 'var(--gap)';
  return 'var(--fg-3)';
}

// ── Types ─────────────────────────────────────────────────────────────

interface NodeExplorerBentoProps {
  onTicker: (ticker: string) => void;
  onExpandKG: () => void;
}

// ── Component ─────────────────────────────────────────────────────────

export function NodeExplorerBento({ onTicker, onExpandKG }: NodeExplorerBentoProps) {
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedNodeId, setSelectedNodeId] = useState<string>('');
  const [isFocused, setIsFocused] = useState<boolean>(false);

  // ── filter logic ──────────────────────────────────────────────────
  const visibleNodes: KGNode[] = useMemo(() => {
    if (!searchQuery.trim()) return KG_NODES;
    const q = searchQuery.toLowerCase();
    const initialMatched = new Set(
      KG_NODES
        .filter((n) => ((n.label || '').toLowerCase().includes(q) || (n.id || '').toLowerCase().includes(q)))
        .map((n) => n.id)
    );
    const matched = new Set(initialMatched);
    // Include directly connected nodes (1-hop only)
    KG_EDGES.forEach((e: KGEdge) => {
      if (initialMatched.has(e.s)) matched.add(e.t);
      if (initialMatched.has(e.t)) matched.add(e.s);
    });
    return KG_NODES.filter((n) => matched.has(n.id));
  }, [searchQuery]);

  const visibleEdges: KGEdge[] = useMemo(() => {
    const ids = new Set(visibleNodes.map((n) => n.id));
    return KG_EDGES.filter((e: KGEdge) => ids.has(e.s) && ids.has(e.t));
  }, [visibleNodes]);

  // ── selected node info ────────────────────────────────────────────
  const selectedNode = useMemo(() => {
    if (!selectedNodeId) return null;
    return KG_NODES.find((n) => n.id === selectedNodeId) ?? null;
  }, [selectedNodeId]);

  const relatedEdges = useMemo(() => {
    if (!selectedNodeId) return [];
    return KG_EDGES.filter(
      (e: KGEdge) => e.s === selectedNodeId || e.t === selectedNodeId
    );
  }, [selectedNodeId]);

  const sentimentScore = useMemo(() => {
    return selectedNodeId ? mockSentimentForNode(selectedNodeId) : 0;
  }, [selectedNodeId]);

  // ── handlers ──────────────────────────────────────────────────────
  const handleSelect = useCallback((id: string) => {
    setSelectedNodeId((prev) => (prev === id ? '' : id));
  }, []);

  const handleClear = useCallback(() => {
    setSearchQuery('');
  }, []);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Escape') setSearchQuery('');
    },
    []
  );

  // ── render ────────────────────────────────────────────────────────
  return (
    <div
      style={{
        border: '1px solid var(--border-hairline)',
        borderRadius: 'var(--radius-card)',
        overflow: 'hidden',
        background: 'var(--surface-app)',
        marginTop: 16,
      }}
    >
      {/* ── Header ── */}
      <div
        data-testid="node-explorer-header"
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          padding: '10px 14px',
          borderBottom: '1px solid var(--border-hairline)',
        }}
      >
        <Icon k="graph" size={14} style={{ color: 'var(--iris)' }} />
        <span style={{ font: '600 13px/1 var(--font-body)', color: 'var(--fg-1)', flex: 1 }}>
          Node Explorer
        </span>
        <span
          data-testid="node-explorer-node-count"
          style={{ font: '12px/1 var(--font-mono)', color: 'var(--fg-3)' }}
        >
          {visibleNodes.length} thực thể · {visibleEdges.length} quan hệ
        </span>

        {/* Search input */}
        <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
          <Icon
            k="search"
            size={13}
            style={{
              position: 'absolute',
              left: 8,
              color: 'var(--fg-3)',
              pointerEvents: 'none',
            }}
          />
          <input
            data-testid="node-explorer-search"
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Tìm mã cổ phiếu hoặc thực thể..."
            aria-label="Tìm kiếm node trong đồ thị tri thức"
            style={{
              width: 230,
              paddingLeft: 28,
              paddingRight: searchQuery ? 28 : 8,
              height: 30,
              border: isFocused ? '1px solid var(--iris)' : '1px solid var(--border-hairline)',
              borderRadius: 6,
              background: 'var(--surface-app)',
              font: '12px/1 var(--font-body)',
              color: 'var(--fg-1)',
              outline: 'none',
            }}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
          />
          {searchQuery && (
            <button
              data-testid="node-explorer-clear-btn"
              onClick={handleClear}
              aria-label="Xóa tìm kiếm"
              style={{
                position: 'absolute',
                right: 4,
                top: 0,
                bottom: 0,
                width: 30,
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--fg-3)',
              }}
            >
              <Icon k="x" size={12} />
            </button>
          )}
        </div>

        {/* Expand button */}
        <button
          data-testid="node-explorer-expand-btn"
          onClick={onExpandKG}
          aria-label="Mở màn hình đồ thị tri thức đầy đủ"
          title="Mở rộng"
          className="btn ghost"
          style={{ minHeight: 30, padding: '0 8px', display: 'flex', alignItems: 'center', gap: 4 }}
        >
          <Icon k="ext" size={13} />
          <span style={{ font: '12px/1 var(--font-body)' }}>Mở rộng</span>
        </button>
      </div>

      {/* ── Body: canvas + sidebar ── */}
      <div style={{ display: 'flex', height: 420, overflow: 'hidden' }}>
        {/* KGViewer canvas */}
        <div
          data-testid="node-explorer-canvas"
          style={{ flex: 1, minWidth: 0, overflow: 'hidden' }}
        >
          <KGViewer
            nodes={visibleNodes}
            edges={visibleEdges}
            selectedId={selectedNodeId}
            onSelect={handleSelect}
            height={420}
          />
        </div>

        {/* Focus Sidebar — slide-in */}
        <div
          data-testid="node-explorer-sidebar"
          style={{
            width: selectedNode ? 220 : 0,
            opacity: selectedNode ? 1 : 0,
            overflow: 'hidden',
            transition: 'width 0.2s ease-out, opacity 0.15s ease-out',
            borderLeft: selectedNode ? '1px solid var(--border-hairline)' : 'none',
            background: 'var(--surface-app)',
            flexShrink: 0,
          }}
          aria-hidden={!selectedNode}
        >
          {selectedNode && (
            <div style={{ padding: 14, height: '100%', overflow: 'auto' }}>
              {/* Type badge */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                <span
                  style={{
                    font: '700 10px/1 var(--font-mono)',
                    background: 'var(--iris-tint)',
                    color: 'var(--iris-deep)',
                    padding: '4px 8px',
                    borderRadius: 4,
                    textTransform: 'uppercase',
                    letterSpacing: '0.12em',
                  }}
                >
                  {selectedNode.type}
                </span>
                <button
                  onClick={() => setSelectedNodeId('')}
                  aria-label="Đóng panel chi tiết"
                  style={{
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    padding: 4,
                    marginLeft: 'auto',
                    color: 'var(--fg-3)',
                    display: 'flex',
                    alignItems: 'center',
                    minHeight: 28,
                  }}
                >
                  <Icon k="x" size={13} />
                </button>
              </div>

              {/* Node label */}
              <h4 style={{ margin: '0 0 6px', font: '600 13px/1.4 var(--font-body)', color: 'var(--fg-1)' }}>
                {selectedNode.label}
              </h4>

              {/* Node ID */}
              <div
                style={{
                  font: '11px/1 var(--font-mono)',
                  color: 'var(--fg-3)',
                  marginBottom: 12,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                {selectedNode.id}
              </div>

              {/* Sentiment Score */}
              <div style={{ marginBottom: 10 }}>
                <div
                  style={{
                    font: '700 10px/1 var(--font-mono)',
                    color: 'var(--fg-3)',
                    letterSpacing: '0.12em',
                    textTransform: 'uppercase',
                    marginBottom: 4,
                  }}
                >
                  Sentiment Score
                </div>
                <div
                  style={{
                    font: '600 18px/1 var(--font-mono)',
                    color: sentimentColor(sentimentScore),
                  }}
                >
                  {sentimentScore > 0 ? '+' : ''}{sentimentScore.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </div>
              </div>

              {/* Nguồn bài báo */}
              <div style={{ marginBottom: 10 }}>
                <div
                  style={{
                    font: '700 10px/1 var(--font-mono)',
                    color: 'var(--fg-3)',
                    letterSpacing: '0.12em',
                    textTransform: 'uppercase',
                    marginBottom: 4,
                  }}
                >
                  Nguồn bài báo
                </div>
                <div
                  style={{
                    font: '500 12px/1.4 var(--font-body)',
                    color: 'var(--fg-2)',
                  }}
                >
                  {mockNewsSourceForNode(selectedNode.id)}
                </div>
              </div>

              {/* Relations count */}
              <div style={{ marginBottom: 12 }}>
                <div
                  style={{
                    font: '700 10px/1 var(--font-mono)',
                    color: 'var(--fg-3)',
                    letterSpacing: '0.12em',
                    textTransform: 'uppercase',
                    marginBottom: 4,
                  }}
                >
                  Quan hệ ({relatedEdges.length})
                </div>
                {relatedEdges.slice(0, 5).map((e: KGEdge, i) => {
                  const otherId = e.s === selectedNodeId ? e.t : e.s;
                  const otherNode = KG_NODES.find((n) => n.id === otherId);
                  const dir = e.s === selectedNodeId ? '→' : '←';
                  return (
                    <div
                      key={`${e.s}-${e.t}-${e.kind}-${i}`}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'flex-start',
                        gap: 4,
                        padding: '4px 0',
                        borderBottom: '1px solid var(--border-hairline)',
                        font: '11px/1.4 var(--font-body)',
                        color: 'var(--fg-2)',
                      }}
                    >
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <span
                          style={{
                            font: '10px/1 var(--font-mono)',
                            color: 'var(--iris)',
                            display: 'block',
                            marginBottom: 2,
                          }}
                        >
                          {e.kind}
                        </span>
                        <span style={{ color: 'var(--fg-2)' }}>
                          {dir} {otherNode?.label ?? otherId}
                        </span>
                      </div>
                      <span
                        style={{ font: '11px/1 var(--font-mono)', color: 'var(--fg-3)', flexShrink: 0 }}
                      >
                        {((e.w ?? 0) * 100).toFixed(0)}%
                      </span>
                    </div>
                  );
                })}
                {relatedEdges.length > 5 && (
                  <div style={{ font: '11px/1 var(--font-body)', color: 'var(--fg-3)', paddingTop: 4 }}>
                    +{relatedEdges.length - 5} quan hệ khác
                  </div>
                )}
              </div>

              {/* Stock detail button */}
              {selectedNode.type === 'Stock' && (
                <button
                  className="btn primary"
                  onClick={() => onTicker(selectedNode.id)}
                  aria-label={`Xem chi tiết cổ phiếu ${selectedNode.label}`}
                  style={{ width: '100%', minHeight: 36, justifyContent: 'center' }}
                >
                  Xem chi tiết <Icon k="caretR" size={12} />
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* ── Footer: legend ── */}
      <div
        style={{
          display: 'flex',
          gap: 16,
          padding: '8px 14px',
          borderTop: '1px solid var(--border-hairline)',
          font: '11px/1 var(--font-body)',
          color: 'var(--fg-3)',
          flexWrap: 'wrap',
        }}
      >
        {[
          { color: 'var(--event, #FCAF16)', label: 'Sự kiện' },
          { color: 'var(--iris)', label: 'Ngành' },
          { color: 'var(--brand)', label: 'Cổ phiếu' },
          { color: 'var(--mint)', label: 'Lãnh đạo' },
        ].map(({ color, label }) => (
          <span key={label} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <span
              style={{ width: 8, height: 8, borderRadius: '50%', background: color, flexShrink: 0 }}
            />
            {label}
          </span>
        ))}
        <span style={{ marginLeft: 'auto' }}>Kéo để pan · Cuộn để zoom</span>
      </div>
    </div>
  );
}
