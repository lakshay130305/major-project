import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Register from './Register'
import { AuthProvider } from '../auth.jsx'

vi.mock('../api', () => ({ default: { post: vi.fn() } }))
import api from '../api'

const renderPage = () => render(
  <MemoryRouter><AuthProvider><Register /></AuthProvider></MemoryRouter>,
)

const fillRequiredExceptLogin = () => {
  fireEvent.change(screen.getByLabelText(/full name/i), { target: { value: 'Test Tourist' } })
  fireEvent.change(screen.getByLabelText(/document number/i), { target: { value: 'ABCD1234' } })
  fireEvent.change(screen.getByLabelText(/^phone$/i), { target: { value: '+91-90000-00001' } })
  fireEvent.change(screen.getByLabelText(/trip start/i), { target: { value: '2026-09-01T10:00' } })
  fireEvent.change(screen.getByLabelText(/trip end/i), { target: { value: '2026-09-05T10:00' } })
}

const submitButton = () => screen.getByText(/register & issue digital id/i)

beforeEach(() => vi.resetAllMocks())

describe('Register', () => {
  // jsdom runs the same interactive constraint-validation step a real
  // browser does on a submit-button click: with `required` (and
  // type="email") set, an invalid form never dispatches the submit event
  // at all, so our onSubmit handler -- and the API call -- never run. This
  // is the primary defense; it's what stops a person from silently getting
  // through registration with blank fields.
  it('the required/email attributes block a native submit-button click when fields are empty', () => {
    renderPage()
    fireEvent.click(submitButton())
    expect(api.post).not.toHaveBeenCalled()
  })

  it('email and password are marked required so the browser blocks a login-less registration', () => {
    renderPage()
    expect(screen.getByLabelText(/^email$/i)).toBeRequired()
    expect(screen.getByLabelText(/password/i)).toBeRequired()
    expect(screen.getByLabelText(/^email$/i)).toHaveAttribute('type', 'email')
  })

  // Defense in depth: dispatch the submit event directly (bypassing the
  // browser-level gate above, the same way a bug in the native check or an
  // unusual input method could) to prove the component's own validate()
  // still rejects things HTML attributes alone can't express.
  const submitDirectly = (container) => fireEvent.submit(container.querySelector('form'))

  it('rejects a password that fails the strength policy even once every field is "filled"', () => {
    const { container } = renderPage()
    fillRequiredExceptLogin()
    fireEvent.change(screen.getByLabelText(/^email$/i), { target: { value: 'a@b.com' } })
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'onlyletters' } })
    submitDirectly(container)

    expect(screen.getByText(/letters and numbers/i)).toBeInTheDocument()
    expect(api.post).not.toHaveBeenCalled()
  })

  it('rejects a trip end that is not after trip start', () => {
    const { container } = renderPage()
    fillRequiredExceptLogin()
    fireEvent.change(screen.getByLabelText(/trip end/i), { target: { value: '2026-08-01T10:00' } })
    fireEvent.change(screen.getByLabelText(/^email$/i), { target: { value: 'a@b.com' } })
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'password1' } })
    submitDirectly(container)

    expect(screen.getByText(/trip end must be after trip start/i)).toBeInTheDocument()
    expect(api.post).not.toHaveBeenCalled()
  })

  it('submits with email and password once every required field is valid', async () => {
    // The registration response feeds a delayed auto-login call the
    // component fires via setTimeout -- route both endpoints through one
    // mock and fake the clock so that second call never leaks into later
    // tests as a real 1.5s pending timer.
    vi.useFakeTimers({ shouldAdvanceTime: true })
    api.post.mockImplementation((url) => {
      if (url === '/tourists') {
        return Promise.resolve({ data: { digital_id: 'STS-TEST001', trip_end: '2026-09-05T10:00:00' } })
      }
      return Promise.resolve({ data: { access_token: 't', refresh_token: 'r', role: 'tourist' } })
    })
    renderPage()
    fillRequiredExceptLogin()
    fireEvent.change(screen.getByLabelText(/^email$/i), { target: { value: 'a@b.com' } })
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'password1' } })
    fireEvent.click(submitButton())

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/tourists', expect.objectContaining({
      email: 'a@b.com',
      password: 'password1',
    })))
    expect(screen.getByText('STS-TEST001')).toBeInTheDocument()

    await act(async () => { await vi.advanceTimersByTimeAsync(1500) })
    vi.useRealTimers()
  })
})
