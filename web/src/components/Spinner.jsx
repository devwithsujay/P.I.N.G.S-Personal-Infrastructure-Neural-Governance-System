import React from 'react'
import { Spinner as HeroSpinner } from '@heroui/react'

export default function Spinner({ size = 'md', className = '' }) {
  return <HeroSpinner size={size} color="current" className={className} />
}

export function PageSpinner({ text = 'Loading...' }) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-3">
      <HeroSpinner size="lg" color="accent" />
      <span className="text-xs text-text-muted">{text}</span>
    </div>
  )
}

export function InlineSpinner({ text }) {
  return (
    <span className="inline-flex items-center gap-2 text-text-muted text-xs">
      <HeroSpinner size="sm" color="current" />
      {text}
    </span>
  )
}
