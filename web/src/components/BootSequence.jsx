import React, { useState, useEffect, useRef } from 'react'

const bootMessages = [
  { text: '> P.I.N.G.S Core v2.0 initializing...', delay: 200,  type: 'normal' },
  { text: '> Loading neural mesh interface...',     delay: 600,  type: 'normal' },
  { text: '> Connecting to core systems...',        delay: 1000, type: 'normal' },
  { text: '> Initializing memory graph...',         delay: 1400, type: 'normal' },
  { text: '> Calibrating agent protocols...',       delay: 1800, type: 'normal' },
  { text: '> Loading skill modules...',             delay: 2200, type: 'normal' },
  { text: '> Establishing secure channels...',      delay: 2600, type: 'normal' },
  { text: '> Proactive intelligence: ONLINE',       delay: 3000, type: 'success' },
  { text: '> All systems operational.',             delay: 3400, type: 'normal' },
  { text: '> Welcome, Operator.',                   delay: 3800, type: 'accent'  },
]

const TOTAL_DURATION = 4600   // ms before auto-complete fires
const RING_DELAYS    = [0, 180, 360, 540]  // staggered ring reveal

// Inline styles so we don't depend on Tailwind classes that may not exist yet
const styles = {
  overlay: {
    position: 'fixed',
    inset: 0,
    zIndex: 100,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
  },
  scanline: {
    position: 'absolute',
    inset: 0,
    pointerEvents: 'none',
    background: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 4px)',
    zIndex: 1,
  },
  scanlineBeam: {
    position: 'absolute',
    left: 0,
    right: 0,
    height: '120px',
            background: 'linear-gradient(to bottom, transparent, rgba(var(--accent-rgb),0.03), transparent)',
    animation: 'scanlineBeam 3.5s linear infinite',
    zIndex: 2,
    pointerEvents: 'none',
  },
}

export default function BootSequence({ onComplete }) {
  const [visibleLines, setVisibleLines]   = useState([])
  const [ringVisible, setRingVisible]     = useState([false, false, false, false])
  const [logoVisible, setLogoVisible]     = useState(false)
  const [titleVisible, setTitleVisible]   = useState(false)
  const [termVisible, setTermVisible]     = useState(false)
  const [progress, setProgress]           = useState(0)
  const [done, setDone]                   = useState(false)
  const [fadeOut, setFadeOut]             = useState(false)
  const termRef                           = useRef(null)
  const progressRef                       = useRef(null)

  // Scroll terminal to bottom when new lines appear
  useEffect(() => {
    if (termRef.current) {
      termRef.current.scrollTop = termRef.current.scrollHeight
    }
  }, [visibleLines])

  useEffect(() => {
    const timers = []

    // Staggered ring reveal
    RING_DELAYS.forEach((delay, i) => {
      timers.push(setTimeout(() => {
        setRingVisible(prev => { const n = [...prev]; n[i] = true; return n })
      }, delay))
    })

    // Logo pulse + title appear
    timers.push(setTimeout(() => setLogoVisible(true),  600))
    timers.push(setTimeout(() => setTitleVisible(true), 900))
    timers.push(setTimeout(() => setTermVisible(true),  1100))

    // Boot messages
    bootMessages.forEach(msg => {
      timers.push(setTimeout(() => {
        setVisibleLines(prev => [...prev, msg])
      }, msg.delay))
    })

    // Progress bar — tick every 46ms to reach 100 over TOTAL_DURATION
    let tick = 0
    const totalTicks = 100
    const interval = TOTAL_DURATION / totalTicks
    progressRef.current = setInterval(() => {
      tick++
      setProgress(tick)
      if (tick >= totalTicks) clearInterval(progressRef.current)
    }, interval)

    // Completion
    const doneTimer = setTimeout(() => {
      setDone(true)
      setTimeout(() => {
        setFadeOut(true)
        setTimeout(onComplete, 500)
      }, 400)
    }, TOTAL_DURATION)

    return () => {
      timers.forEach(clearTimeout)
      clearInterval(progressRef.current)
      clearTimeout(doneTimer)
    }
  }, [onComplete])

  const handleSkip = () => {
    clearInterval(progressRef.current)
    setFadeOut(true)
    setTimeout(onComplete, 300)
  }

  return (
    <>
      {/* Inject keyframe for scanline beam + ring reveals + fade-out */}
      <style>{`
        @keyframes scanlineBeam {
          from { top: -120px; }
          to   { top: 100vh;  }
        }
        @keyframes bootRingPulse {
          0%,100% { opacity: var(--ring-opacity); }
          50%     { opacity: calc(var(--ring-opacity) * 1.6); }
        }
        @keyframes bootFadeSlideUp {
          from { opacity: 0; transform: translateY(8px); }
          to   { opacity: 1; transform: translateY(0);   }
        }
        @keyframes bootFadeOut {
          from { opacity: 1; }
          to   { opacity: 0; }
        }
        @keyframes bootLogoFloat {
          0%,100% { transform: translateY(0px);  }
          50%     { transform: translateY(-5px); }
        }
        @keyframes bootCursorBlink {
          0%,100% { opacity: 1; }
          50%     { opacity: 0; }
        }
        .boot-line-enter {
          animation: bootFadeSlideUp 0.35s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards;
        }
        .boot-container {
          animation: ${fadeOut ? 'bootFadeOut 0.5s ease-out forwards' : 'none'};
        }
      `}</style>

      <div
        className="boot-container"
        style={{
          ...styles.overlay,
          background: '#07070a',
          backgroundImage: `
            radial-gradient(ellipse 90% 60% at 15% 15%, rgba(var(--accent-rgb),0.08) 0%, transparent 65%),
            radial-gradient(ellipse 50% 50% at 85% 5%,  rgba(var(--accent-rgb),0.05) 0%, transparent 55%),
            radial-gradient(ellipse 70% 80% at 55% 95%, rgba(var(--accent-rgb),0.04) 0%, transparent 60%)
          `,
        }}
      >
        {/* Scanline texture */}
        <div style={styles.scanline} />
        <div style={styles.scanlineBeam} />

        {/* Main content card */}
        <div style={{ position: 'relative', zIndex: 10, width: '100%', maxWidth: '520px', padding: '0 24px' }}>
          <div style={{
            background: 'var(--bg-surface)',
            backdropFilter: 'blur(24px) saturate(1.4)',
            WebkitBackdropFilter: 'blur(24px) saturate(1.4)',
            border: '1px solid rgba(255,255,255,0.07)',
            borderRadius: '20px',
            padding: '40px 36px 32px',
                  boxShadow: '0 25px 60px rgba(0,0,0,0.6), 0 0 0 1px rgba(var(--accent-rgb),0.08)',
            position: 'relative',
            overflow: 'hidden',
          }}>
            {/* Top gradient border accent */}
            <div style={{
              position: 'absolute', top: 0, left: 0, right: 0, height: '1px',
              background: 'linear-gradient(to right, transparent, rgba(var(--accent-rgb),0.5), transparent)',
            }} />

            {/* Logo section */}
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              marginBottom: '32px',
            }}>
              {/* Concentric rings logo — staggered reveal */}
              <div style={{
                position: 'relative',
                width: '96px',
                height: '96px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '16px',
                animation: logoVisible ? 'bootLogoFloat 3s ease-in-out infinite' : 'none',
              }}>
                <svg viewBox="0 0 96 96" fill="none" style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}>
                  {/* Outermost ring */}
                  <circle
                    cx="48" cy="48" r="44"
                    stroke="rgba(var(--accent-rgb),0.15)"
                    strokeWidth="1"
                    style={{
                      '--ring-opacity': '0.15',
                      opacity: ringVisible[3] ? 0.15 : 0,
                      transition: 'opacity 0.6s ease',
                      animation: ringVisible[3] ? 'bootRingPulse 3s ease-in-out infinite 1.2s' : 'none',
                    }}
                  />
                  {/* Third ring */}
                  <circle
                    cx="48" cy="48" r="34"
                    stroke="rgba(var(--accent-rgb),0.25)"
                    strokeWidth="1"
                    style={{
                      '--ring-opacity': '0.25',
                      opacity: ringVisible[2] ? 0.25 : 0,
                      transition: 'opacity 0.5s ease',
                      animation: ringVisible[2] ? 'bootRingPulse 3s ease-in-out infinite 0.8s' : 'none',
                    }}
                  />
                  {/* Second ring */}
                  <circle
                    cx="48" cy="48" r="23"
                    stroke="rgba(var(--accent-rgb),0.5)"
                    strokeWidth="1.5"
                    style={{
                      '--ring-opacity': '0.5',
                      opacity: ringVisible[1] ? 0.5 : 0,
                      transition: 'opacity 0.4s ease',
                      animation: ringVisible[1] ? 'bootRingPulse 2.5s ease-in-out infinite 0.4s' : 'none',
                    }}
                  />
                  {/* Inner glow ring */}
                  <circle cx="48" cy="48" r="23"
                    stroke="rgba(var(--accent-rgb),0.15)"
                    strokeWidth="10"
                    style={{ opacity: ringVisible[1] ? 1 : 0, transition: 'opacity 0.4s ease', filter: 'blur(4px)' }}
                  />
                  {/* Core dot */}
                  <circle
                    cx="48" cy="48" r="6"
                    fill="var(--accent)"
                    style={{
                      opacity: ringVisible[0] ? 1 : 0,
                      transition: 'opacity 0.3s ease',
                      filter: 'drop-shadow(0 0 8px rgba(var(--accent-rgb),0.9))',
                    }}
                  />
                  {/* Core dot inner bright */}
                  <circle
                    cx="48" cy="48" r="3"
                    fill="var(--accent-light)"
                    style={{ opacity: ringVisible[0] ? 1 : 0, transition: 'opacity 0.3s ease 0.1s' }}
                  />
                </svg>
              </div>

              {/* Brand name */}
              <div style={{
                opacity: titleVisible ? 1 : 0,
                transform: titleVisible ? 'translateY(0)' : 'translateY(10px)',
                transition: 'opacity 0.5s ease, transform 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275)',
                textAlign: 'center',
              }}>
                <div style={{
                  fontFamily: "'Oxanium', sans-serif",
                  fontSize: '28px',
                  fontWeight: '700',
                  letterSpacing: '0.08em',
                  color: 'var(--text-primary, #ededf5)',
                    textShadow: '0 0 30px rgba(var(--accent-rgb),0.4)',
                  lineHeight: 1,
                }}>
                  P.I.N.G.S
                </div>
                <div style={{
                  fontFamily: "'Inter', sans-serif",
                  fontSize: '11px',
                  color: 'var(--text-muted, #5c5c78)',
                  letterSpacing: '0.2em',
                  textTransform: 'uppercase',
                  marginTop: '6px',
                }}>
                  Core v2.0 · Neural Governance Console
                </div>
              </div>
            </div>

            {/* Terminal block */}
            <div style={{
              opacity: termVisible ? 1 : 0,
              transform: termVisible ? 'translateY(0)' : 'translateY(8px)',
              transition: 'opacity 0.4s ease, transform 0.4s ease',
            }}>
              <div style={{
                background: 'var(--bg-code)',
                border: '1px solid rgba(255,255,255,0.06)',
                borderRadius: '12px',
                padding: '16px 20px',
                marginBottom: '20px',
                position: 'relative',
                overflow: 'hidden',
              }}>
                {/* Terminal header dots */}
                <div style={{ display: 'flex', gap: '6px', marginBottom: '14px', opacity: 0.5 }}>
                  <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ff5f57' }} />
                  <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#febc2e' }} />
                  <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#28c840' }} />
                  <span style={{ fontFamily: 'monospace', fontSize: '10px', color: 'rgba(255,255,255,0.2)', marginLeft: '6px', lineHeight: '8px' }}>
                    system.boot
                  </span>
                </div>

                {/* Log lines */}
                <div
                  ref={termRef}
                  style={{
                    fontFamily: "'Courier New', Courier, monospace",
                    fontSize: '12px',
                    lineHeight: '1.7',
                    height: '200px',
                    overflowY: 'auto',
                    scrollbarWidth: 'none',
                  }}
                >
                  {visibleLines.map((line, i) => (
                    <div
                      key={i}
                      className="boot-line-enter"
                      style={{
                        color: line.type === 'success' ? 'var(--status-success)'
                          : line.type === 'accent'  ? 'var(--accent)'
                          : 'var(--text-secondary)',
                        display: 'flex',
                        alignItems: 'baseline',
                        gap: '6px',
                      }}
                    >
                      {/* Prompt symbol */}
                      <span style={{ color: 'rgba(var(--accent-rgb),0.6)', flexShrink: 0 }}>›</span>
                      <span>{line.text.replace(/^>\s*/, '')}</span>
                      {/* Success checkmark */}
                      {line.type === 'success' && (
                        <span style={{ marginLeft: 'auto', color: 'var(--status-success)', fontSize: '10px' }}>✓</span>
                      )}
                    </div>
                  ))}

                  {/* Blinking cursor */}
                  {!done && (
                    <span style={{
                      display: 'inline-block',
                      width: '8px',
                      height: '14px',
                      background: 'var(--accent)',
                      marginTop: '2px',
                      animation: 'bootCursorBlink 1s step-end infinite',
                      borderRadius: '1px',
                      verticalAlign: 'text-bottom',
                    }} />
                  )}
                </div>
              </div>

              {/* Progress bar */}
              <div style={{
                height: '2px',
                background: 'var(--border-subtle)',
                borderRadius: '2px',
                marginBottom: '20px',
                overflow: 'hidden',
              }}>
                <div style={{
                  height: '100%',
                  width: `${progress}%`,
                  background: 'linear-gradient(to right, var(--accent, #6c5ce7), var(--accent-light, #a29bfe))',
                  borderRadius: '2px',
                  boxShadow: '0 0 8px rgba(var(--accent-rgb),0.5)',
                  transition: 'width 0.1s linear',
                }} />
              </div>

              {/* Skip button */}
              <button
                onClick={handleSkip}
                style={{
                  width: '100%',
                  padding: '10px',
                  background: 'var(--bg-elevated)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '10px',
                  color: 'var(--text-muted)',
                  fontSize: '12px',
                  fontFamily: "'Inter', sans-serif",
                  letterSpacing: '0.08em',
                  textTransform: 'uppercase',
                  cursor: 'pointer',
                  transition: 'background 0.2s ease, color 0.2s ease',
                }}
                onMouseEnter={e => {
                  e.target.style.background = 'rgba(var(--accent-rgb),0.1)'
                  e.target.style.color = 'var(--text-secondary, #9b9bb8)'
                }}
                onMouseLeave={e => {
                  e.target.style.background = 'var(--bg-elevated)'
                  e.target.style.color = 'var(--text-muted)'
                }}
              >
                Skip Initialization
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
