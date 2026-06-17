import React from 'react';
import { Icon } from '@/components/shared';

interface SectionProps {
  title?: string;
  meta?: string;
  actions?: React.ReactNode;
  flush?: boolean;
  children: React.ReactNode;
  ai?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

export function Section({ title, meta, actions, flush, children, ai, className, style }: SectionProps) {
  return (
    <div className={`qf-card ${flush ? 'flush' : ''} ${className || ''}`} style={style}>
      {(title || meta || actions) && (
        <div className="qf-card-head">
          <div>
            {title && (
              <h3 className="qf-card-title">
                {ai && <span className="ai-spark"><Icon name="sparkle" size={12} /></span>}
                {title}
              </h3>
            )}
            {meta && <div className="qf-card-meta" style={{ marginTop: 4 }}>{meta}</div>}
          </div>
          {actions && <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>{actions}</div>}
        </div>
      )}
      {children}
    </div>
  );
}
