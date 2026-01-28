import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from '../contexts/AuthContext';
import ProtectedRoute from './ProtectedRoute';

// Mock Supabase
vi.mock('../lib/supabase', () => ({
  supabase: {
    auth: {
      getSession: vi.fn().mockResolvedValue({ data: { session: null } }),
      onAuthStateChange: vi.fn().mockReturnValue({ data: { subscription: { unsubscribe: vi.fn() } } }),
    },
  },
  auth: {
    signIn: vi.fn(),
    signOut: vi.fn(),
  },
}));

const renderWithRouter = (ui: React.ReactElement, { route = '/' } = {}) => {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <AuthProvider>
        {ui}
      </AuthProvider>
    </MemoryRouter>
  );
};

describe('ProtectedRoute Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should show loading spinner initially', async () => {
    // Mock loading state
    const { supabase } = await import('../lib/supabase');
    vi.mocked(supabase.auth.getSession).mockReturnValue(
      new Promise(() => {}) // Never resolves to keep loading
    );

    renderWithRouter(
      <Routes>
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <div>Protected Content</div>
            </ProtectedRoute>
          }
        />
      </Routes>
    );

    // Loading spinner should be visible
    const spinner = document.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  it('should redirect to login when not authenticated', async () => {
    const { supabase } = await import('../lib/supabase');
    vi.mocked(supabase.auth.getSession).mockResolvedValue({
      data: { session: null },
      error: null,
    });

    renderWithRouter(
      <Routes>
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <div>Protected Content</div>
            </ProtectedRoute>
          }
        />
        <Route path="/login" element={<div>Login Page</div>} />
      </Routes>
    );

    // Wait for the redirect
    await vi.waitFor(() => {
      expect(screen.getByText('Login Page')).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('should render children when authenticated', async () => {
    const mockSession = {
      user: {
        id: 'test-user-id',
        email: 'test@example.com',
        user_metadata: {},
      },
      access_token: 'mock-token',
    };

    const { supabase } = await import('../lib/supabase');
    vi.mocked(supabase.auth.getSession).mockResolvedValue({
      data: { session: mockSession as any },
      error: null,
    });

    renderWithRouter(
      <Routes>
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <div>Protected Content</div>
            </ProtectedRoute>
          }
        />
      </Routes>
    );

    // Wait for authenticated content
    await vi.waitFor(() => {
      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    }, { timeout: 3000 });
  });
});
