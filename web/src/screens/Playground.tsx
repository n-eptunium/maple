import { useState } from 'react'
import '../theme.css'
import './Playground.css'
import {
  AccentButton,
  Card,
  CaptionBox,
  EmptyState,
  PillButton,
  SafeZoneGuides,
  SceneScreen,
  Tag,
  Toast,
  type Box,
} from '../components'
import { PLATFORM_LABELS, snapLines, type Platform } from '../components/safeZones'
import { useToasts } from '../store/toast'
import { useUi } from '../store/ui'

const CLIPS = ['Entry', 'Ace', 'Clutch']

export function Playground() {
  const show = useToasts((s) => s.show)
  const { safeZones, toggleSafeZone } = useUi()
  const [box, setBox] = useState<Box>({ x: 0.5, y: 0.72, w: 0.8, h: 0.12 })
  const [clip, setClip] = useState('Ace')
  const [tool, setTool] = useState('Trim')
  const [toastKey, setToastKey] = useState(0)
  const [scene, setScene] = useState<'welcome' | 'posted'>('welcome')

  return (
    <div className="pg">
      <header className="pg-header">
        <h1>🧪 Playground</h1>
        <AccentButton onClick={() => show('Rendered', { kind: 'done', emoji: '🎬' })}>Render</AccentButton>
      </header>

      <div className="pg-grid">
        <Card className="pg-section">
          <h2>PillButton</h2>
          <div className="pg-row">
            {(
              [
                ['Idle', {}],
                ['Hover', { demo: 'hover' }],
                ['Pressed', { demo: 'pressed' }],
                ['Selected', { selected: true }],
                ['Disabled', { disabled: true }],
              ] as const
            ).map(([label, props]) => (
              <div className="pg-item" key={label}>
                <PillButton {...props}>Trim</PillButton>
                <Tag>{label}</Tag>
              </div>
            ))}
          </div>
          <div className="pg-row">
            {['Trim', 'Captions', 'Add phonk'].map((t) => (
              <PillButton key={t} selected={tool === t} onClick={() => setTool(t)}>
                {t}
              </PillButton>
            ))}
          </div>
        </Card>

        <Card className="pg-section">
          <h2>AccentButton</h2>
          <div className="pg-row">
            {(
              [
                ['Idle', {}],
                ['Hover', { demo: 'hover' }],
                ['Pressed', { demo: 'pressed' }],
                ['Disabled', { disabled: true }],
              ] as const
            ).map(([label, props]) => (
              <div className="pg-item" key={label}>
                <AccentButton {...props}>Post</AccentButton>
                <Tag>{label}</Tag>
              </div>
            ))}
          </div>
        </Card>

        <Card className="pg-section">
          <h2>Card</h2>
          <Card>Card</Card>
          <Card selected>Selected card</Card>
        </Card>

        <Card className="pg-section">
          <h2>Tag</h2>
          <div className="pg-row">
            <Tag>Mirage</Tag>
            <Tag>Round 12</Tag>
            <Tag>🎯 ZywOo</Tag>
            <Tag selected>Selected</Tag>
            <Tag gold>⭐ Highlight</Tag>
          </div>
        </Card>

        <Card className="pg-section">
          <h2>Toast</h2>
          <div className="pg-row" key={toastKey}>
            <Toast message="Saved" emoji="💾" />
            <Toast message="Rendered" emoji="🎬" kind="done" />
          </div>
          <div className="pg-row">
            <PillButton onClick={() => setToastKey((k) => k + 1)}>Replay</PillButton>
            <PillButton onClick={() => show('Copied link', { emoji: '🔗' })}>Show toast</PillButton>
            <PillButton onClick={() => show('Posted', { kind: 'done', emoji: '🚀' })}>Show done</PillButton>
          </div>
        </Card>
      </div>

      <Card className="pg-section">
        <h2>EmptyState</h2>
        <div className="pg-grid">
          <div className="pg-empty">
            <EmptyState emoji="🎞️" title="Drop a video here" actionLabel="Browse" />
          </div>
          <div className="pg-empty">
            <EmptyState emoji="🔗" title="Paste an HLTV link" actionLabel="Paste" />
          </div>
        </div>
      </Card>

      <Card className="pg-section">
        <h2>SceneScreen</h2>
        <div className="pg-row">
          <PillButton selected={scene === 'welcome'} onClick={() => setScene('welcome')}>
            Welcome
          </PillButton>
          <PillButton selected={scene === 'posted'} onClick={() => setScene('posted')}>
            Posted!
          </PillButton>
        </div>
        <div className="pg-scene">
          {scene === 'welcome' ? (
            <SceneScreen key="welcome" contained emoji="🎮" title="CS2 Shorts">
              <PillButton surface="scene">New edit</PillButton>
              <PillButton surface="scene">Open</PillButton>
            </SceneScreen>
          ) : (
            <SceneScreen key="posted" contained emoji="🚀" title="Posted!">
              <PillButton surface="scene">Open on YouTube</PillButton>
              <PillButton surface="scene">Next clip</PillButton>
            </SceneScreen>
          )}
        </div>
      </Card>

      <section className="stage">
        <div className="preview-frame">
          <SafeZoneGuides platforms={safeZones} />
          <CaptionBox value={box} onChange={setBox} lines={snapLines(safeZones)}>
            <span className="caption-text preview-caption">what a shot</span>
          </CaptionBox>
        </div>
        <div className="stage-side">
          <Card surface="stage" className="pg-section">
            <h2>Stage</h2>
            <div className="pg-row">
              {(Object.keys(PLATFORM_LABELS) as Platform[]).map((p) => (
                <PillButton key={p} selected={safeZones[p]} onClick={() => toggleSafeZone(p)}>
                  {PLATFORM_LABELS[p]}
                </PillButton>
              ))}
            </div>
            <div className="pg-row">
              <Tag>x {box.x.toFixed(2)}</Tag>
              <Tag>y {box.y.toFixed(2)}</Tag>
              <Tag>w {box.w.toFixed(2)}</Tag>
            </div>
          </Card>
          <div className="timeline">
            {CLIPS.map((c) => (
              <Card key={c} surface="stage" selected={clip === c} className={clip === c ? 'is-selected' : ''} onClick={() => setClip(c)}>
                {c}
              </Card>
            ))}
          </div>
          <div className="pg-row">
            <PillButton surface="stage">Captions</PillButton>
            <PillButton surface="stage">Add phonk</PillButton>
          </div>
        </div>
      </section>
    </div>
  )
}
