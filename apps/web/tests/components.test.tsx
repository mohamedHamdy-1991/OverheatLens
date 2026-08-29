import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { StatusPill, Figure } from '../src/components'
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
  it('renders all eleven primary destinations', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <AppShell>
          <p>content</p>
        </AppShell>
      </MemoryRouter>,
    )
    for (const label of ['Analyze', 'Compare', 'Archetype Atlas', 'Weather Lab',
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
