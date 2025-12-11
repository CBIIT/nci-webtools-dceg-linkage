import React from 'react';

interface HoverUnderlineLinkProps {
  href: string;
  children: React.ReactNode;
  className?: string;
  target?: string;
  rel?: string;
  style?: React.CSSProperties;
}

export default function HoverUnderlineLink({ 
  href, 
  children, 
  className = "text-primary", 
  target = "_blank", 
  rel = "noopener noreferrer",
  style = {}
}: HoverUnderlineLinkProps) {
  const defaultStyle = {
    textDecoration: 'none',
    transition: 'text-decoration 0.2s ease',
    ...style
  };

  return (
    <a
      href={href}
      className={className}
      target={target}
      rel={rel}
      style={defaultStyle}
      onMouseEnter={(e) => (e.target as HTMLAnchorElement).style.textDecoration = 'underline'}
      onMouseLeave={(e) => (e.target as HTMLAnchorElement).style.textDecoration = 'none'}
    >
      {children}
    </a>
  );
}
