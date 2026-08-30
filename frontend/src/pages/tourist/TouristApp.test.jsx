import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { I18nextProvider } from 'react-i18next'
import i18n from '../../i18n'
import { ThemeProvider } from '../../theme.jsx'
import TouristApp from './TouristApp'

// A freshly registered tourist has never sent a GPS ping, so the API
// legitimately returns last_lat/last_lng as null. Leaflet's MapContainer
// throws on a null center -- with no error boundary, that used to blank
// the whole page. These stubs isolate that from jsdom's lack of real
// Leaflet/SVG support (same rationale as TrailReplay.test.jsx).
vi.mock('react-leaflet', () => ({
  MapContainer: ({ children }) => <div data-testid="map">{children}</div>,
  TileLayer: () => null,
  Marker: () => null,
  Polygon: () => null,
  Circle: () => null,
}))
vi.mock('../../components/mapIcons', () => ({
  touristIcon: () => ({}),
  policeIcon: {},
  riskColor: { low: '#000', medium: '#000', high: '#000', restricted: '#000' },
}))
vi.mock('../../auth.jsx', () => ({
  useAuth: () => ({ user: { tourist_id: 1, full_name: 'Test Tourist', role: 'tourist' }, logout: vi.fn() }),
}))
vi.mock('../../api', () => ({ default: { get: vi.fn(), post: vi.fn() } }))
import api from '../../api'

const NO_LOCATION_TOURIST = {
  id: 1, digital_id: 'STS-TEST001', full_name: 'Test Tourist',
  last_lat: null, last_lng: null, tracking_enabled: true, itinerary: [],
}
const SCORE = { tourist_id: 1, score: 80, band: 'safe', breakdown: { zone: 'none', night_penalty: false, explanation: null } }

const renderApp = () => render(
  <MemoryRouter>
    <ThemeProvider>
      <I18nextProvider i18n={i18n}>
        <TouristApp />
      </I18nextProvider>
    </ThemeProvider>
  </MemoryRouter>,
)

beforeEach(async () => {
  vi.resetAllMocks()
  await i18n.changeLanguage('en')
})

describe('TouristApp', () => {
  it('does not crash for a just-registered tourist with no location yet, and shows a waiting placeholder instead of the map', async () => {
    api.get.mockImplementation((url) => {
      if (url === '/tourists/1') return Promise.resolve({ data: NO_LOCATION_TOURIST })
      if (url === '/tourists/1/safety-score') return Promise.resolve({ data: SCORE })
      if (url === '/zones') return Promise.resolve({ data: [] })
      if (url === '/police-units') return Promise.resolve({ data: [] })
      return Promise.resolve({ data: [] })
    })

    renderApp()

    await waitFor(() => expect(screen.getByText('STS-TEST001')).toBeInTheDocument())
    expect(screen.getAllByText(/waiting for your first location update/i).length).toBeGreaterThan(0)
    expect(screen.queryByTestId('map')).not.toBeInTheDocument()
  })

  it('renders the real map once a location is known', async () => {
    const withLocation = { ...NO_LOCATION_TOURIST, last_lat: 26.14, last_lng: 91.73 }
    api.get.mockImplementation((url) => {
      if (url === '/tourists/1') return Promise.resolve({ data: withLocation })
      if (url === '/tourists/1/safety-score') return Promise.resolve({ data: SCORE })
      if (url === '/zones') return Promise.resolve({ data: [] })
      if (url === '/police-units') return Promise.resolve({ data: [] })
      return Promise.resolve({ data: [] })
    })

    renderApp()

    await waitFor(() => expect(screen.getByTestId('map')).toBeInTheDocument())
    expect(screen.queryByText(/waiting for your first location update/i)).not.toBeInTheDocument()
  })
})
