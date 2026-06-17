import React from 'react';

interface TPillProps {
  children: React.ReactNode;
  tone?: string;
  onClick?: () => void;
  className?: string;
  style?: React.CSSProperties;
}

export function TPill({ children, tone, onClick, className, style }: TPillProps) {
  return (
    <span
      className={`t-pill ${tone || ''} ${className || ''}`}
      style={style}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
    >
      {children}
    </span>
  );
}
