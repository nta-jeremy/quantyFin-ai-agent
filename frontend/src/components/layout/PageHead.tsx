import React from 'react';
import { Icon } from '@/components/shared';

interface PageHeadProps {
  eyebrow?: string;
  title: React.ReactNode;
  sub?: React.ReactNode;
  actions?: React.ReactNode;
}

export function PageHead({ eyebrow, title, sub, actions }: PageHeadProps) {
  return (
    <div className="qf-pagehead">
      <div>
        {eyebrow && (
          <div style={{ font: '700 10.5px/1 var(--font-mono)', color: 'var(--iris-deep)', letterSpacing: '0.2em', textTransform: 'uppercase', marginBottom: 6, display: 'inline-flex', alignItems: 'center', gap: 8 }}>
            <Icon name="sparkle" size={11} /> {eyebrow}
          </div>
        )}
        <h1>{title}</h1>
        {sub && <div className="sub">{sub}</div>}
      </div>
      {actions && <div className="actions">{actions}</div>}
    </div>
  );
}
