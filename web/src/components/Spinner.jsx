import React from 'react'

export default function Spinner({ size = 'md', className = '' }) {
  const sizes = {
    sm: 'w-4 h-4 border-[1.5px]',
    md: 'w-6 h-6 border-2',
    lg: 'w-8 h-8 border-2',
  }
  return (
    <span
      className={`inline-block rounded-full border-accent/30 border-t-accent animate-spin ${sizes[size]} ${className}`}
    />
  )
}

export function PageSpinner({ text = 'Loading...' }) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-3">
      <Spinner size="lg" />
      <span className="text-xs text-text-muted">{text}</span>
    </div>
  )
}

export function InlineSpinner({ text }) {
  return (
    <span className="inline-flex items-center gap-2 text-text-muted text-xs">
      <Spinner size="sm" />
      {text}
    </span>
  )
}
