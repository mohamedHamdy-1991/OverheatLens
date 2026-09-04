import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { StatusPill, Figure, ResultVerdict, MarginBar, StandardBadge } from '../src/components'
import { BrandMark, AppShell } from '../src/AppShell'
import { MemoryRouter } from 'react-router-dom'

describe('StatusPill', () => {
  it('pairs a label with an icon for pass statuses (never colour alone)', () => {
    render(<StatusPill status="PASS" />)
    const pill = screen.getByText('PASS').closest('.pill')
    expect(pill).toHaveClass('pill-pass')
    expect(pill?.querySelector('svg')).not.toBeNull()
  })

  it('maps synonyms to a readable label', () => {
    render(<StatusPill status="PASS_WITH_WARNINGS" />)
    expect(screen.getByText('PASS · WARNINGS')).toBeInTheDocument()
  })

  it('renders failures in the fail style', () => {
    render(<StatusPill status="FAIL" />)
    expect(screen.getByText('FAIL').closest('.pill')).toHaveClass('pill-fail')
  })
})

describe('Figure', () => {
  it('renders the figure number and caption', () => {
    render(
      <Figure figNo="FIG 1" caption="hourly dry-bulb temperature">
        <div>chart</div>
      </Figure>,
    )
    expect(screen.getByText('FIG 1')).toBeInTheDocument()
    expect(screen.getByText('hourly dry-bulb temperature')).toBeInTheDocument()
  })
})

describe('BrandMark', () => {
  it('is an svg with the dwelling outline', () => {
    const { container } = render(<BrandMark />)
    expect(container.querySelector('svg path')).not.toBeNull()
  })
})

describe('AppShell navigation (RULE 13 primary nav)', () => {
  it('renders all primary destinations including archive and batch', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <AppShell>
          <p>content</p>
        </AppShell>
      </MemoryRouter>,
    )
    for (const label of ['Analyze', 'Compare', 'Archetype Atlas', 'Run Archive',
      'Scenario & Batch', 'Weather Lab',
      'Comfort Lab', 'Mitigation Lab', 'Validation', 'Methods', 'Docs', 'About']) {
      expect(screen.getAllByRole('link', { name: new RegExp(label) }).length).toBeGreaterThan(0)
    }
  })

  it('carries the non-certification notice in the rail', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <AppShell>
          <p>content</p>
        </AppShell>
      </MemoryRouter>,
    )
    expect(screen.getByText(/not a compliance certificate/i)).toBeInTheDocument()
  })
})

describe('ResultVerdict', () => {
  it('announces PASS as a status with label and icon', () => {
    render(<ResultVerdict verdict="PASS" detail="all criteria pass" />)
    expect(screen.getByRole('status', { name: /PASS/ })).toBeInTheDocument()
  })

  it('renders INCOMPLETE distinctly from failure', () => {
    const { container } = render(<ResultVerdict verdict="INCOMPLETE" />)
    expect(container.querySelector('.verdict.incomplete')).not.toBeNull()
    expect(screen.getByText(/INCOMPLETE/)).toBeInTheDocument()
  })
})

describe('MarginBar', () => {
  it('shows value, limit and margin with an accessible label', () => {
    render(<MarginBar label="Living A" value={2.1} limit={3.0} unit="%" higherIsWorse />)
    expect(screen.getByRole('img', { name: /Living A/ })).toBeInTheDocument()
    expect(screen.getByText(/2.1 \/ 3.0/)).toBeInTheDocument()
  })
})

describe('StandardBadge', () => {
  it('always shows the exact rule-pack edition', () => {
    render(<StandardBadge packId="uk_tm59_2017" version="1.0.0" />)
    expect(screen.getByText(/uk_tm59_2017 · v1.0.0/)).toBeInTheDocument()
  })

  it('tags the 2026 pack as research-only', () => {
    render(<StandardBadge packId="uk_tm59_2026" version="1.0.0" />)
    expect(screen.getByText('RESEARCH ONLY')).toBeInTheDocument()
  })
})
