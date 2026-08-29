import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import { useState } from 'react'

// api.js is a configured axios instance; stub it so no network is touched.
vi.mock('./api', () => ({ default: { post: vi.fn() } }))

import api from './api'
import { AuthProvider, useAuth } from './auth.jsx'

function Probe() {
  const { user, login, logout } = useAuth()
  const [error, setError] = useState(null)
  // Swallow the rejection here the way a real login form would, so a failed
  // login is asserted on rather than surfacing as an unhandled rejection.
  const doLogin = () => login('admin@test.gov', 'pw').catch((e) => setError(e.message))
  return (
    <div>
      <span data-testid="who">{user ? `${user.role}:${user.full_name}` : 'anonymous'}</span>
      <span data-testid="error">{error || ''}</span>
      <button onClick={doLogin}>login</button>
      <button onClick={logout}>logout</button>
    </div>
  )
}

const renderProbe = () => render(<AuthProvider><Probe /></AuthProvider>)

beforeEach(() => {
  localStorage.clear()
  vi.clearAllMocks()
})

describe('AuthProvider', () => {
  it('starts anonymous with empty storage', () => {
    renderProbe()
    expect(screen.getByTestId('who')).toHaveTextContent('anonymous')
  })

  it('rehydrates a session from localStorage', () => {
    localStorage.setItem('user', JSON.stringify({ role: 'admin', full_name: 'Officer' }))
    renderProbe()
    expect(screen.getByTestId('who')).toHaveTextContent('admin:Officer')
  })

  it('stores the token and user on login', async () => {
    api.post.mockResolvedValue({
      data: { access_token: 'tok123', role: 'admin', tourist_id: null, full_name: 'Officer' },
    })
    renderProbe()
    await act(async () => { screen.getByText('login').click() })

    expect(localStorage.getItem('token')).toBe('tok123')
    expect(JSON.parse(localStorage.getItem('user')).role).toBe('admin')
    expect(screen.getByTestId('who')).toHaveTextContent('admin:Officer')
  })

  it('sends credentials as form-encoded fields (OAuth2 password flow)', async () => {
    api.post.mockResolvedValue({
      data: { access_token: 't', role: 'tourist', tourist_id: 3, full_name: 'Aarav' },
    })
    renderProbe()
    await act(async () => { screen.getByText('login').click() })

    const [path, body] = api.post.mock.calls[0]
    expect(path).toBe('/auth/login')
    // The backend expects the email in the OAuth2 `username` field.
    expect(body.get('username')).toBe('admin@test.gov')
    expect(body.get('password')).toBe('pw')
  })

  it('keeps the tourist_id so the app can scope requests', async () => {
    api.post.mockResolvedValue({
      data: { access_token: 't', role: 'tourist', tourist_id: 3, full_name: 'Aarav' },
    })
    renderProbe()
    await act(async () => { screen.getByText('login').click() })
    expect(JSON.parse(localStorage.getItem('user')).tourist_id).toBe(3)
  })

  it('clears credentials on logout', async () => {
    api.post.mockResolvedValue({
      data: { access_token: 't', role: 'admin', tourist_id: null, full_name: 'Officer' },
    })
    renderProbe()
    await act(async () => { screen.getByText('login').click() })
    await act(async () => { screen.getByText('logout').click() })

    expect(localStorage.getItem('token')).toBeNull()
    expect(localStorage.getItem('user')).toBeNull()
    expect(screen.getByTestId('who')).toHaveTextContent('anonymous')
  })

  it('leaves no session behind when login fails', async () => {
    api.post.mockRejectedValue(new Error('401'))
    renderProbe()
    await act(async () => { screen.getByText('login').click() })

    expect(localStorage.getItem('token')).toBeNull()
    expect(screen.getByTestId('who')).toHaveTextContent('anonymous')
    expect(screen.getByTestId('error')).toHaveTextContent('401')
  })
})
