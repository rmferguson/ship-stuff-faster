/**
 * Tests for AuthProvider / useAuth.
 *
 * The auth API module is fully mocked — these tests verify that AuthProvider
 * correctly calls the API functions and wires the results into context state.
 * No actual HTTP requests are made.
 */
import { describe, it, expect, vi, beforeEach, type Mock } from 'vitest';
import { render, screen, act, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from '../AuthContext';
import * as authApi from '@/lib/auth-api';

// Mock the auth API module so no real fetch calls are made
vi.mock('@/lib/auth-api', () => ({
  getMe: vi.fn(),
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
}));

const mockGetMe = authApi.getMe as Mock;
const mockLogin = authApi.login as Mock;
const mockLogout = authApi.logout as Mock;
const mockRegister = authApi.register as Mock;

const TEST_USER = { id: 1, email: 'test@example.com' };

/** Helper: renders AuthProvider + a child component that exposes context state */
function TestConsumer() {
  const { user, isLoading, login, logout, register } = useAuth();
  return (
    <div>
      <span data-testid="loading">{isLoading ? 'loading' : 'ready'}</span>
      <span data-testid="user">{user ? user.email : 'no-user'}</span>
      <button
        onClick={() => login({ email: 'a@b.com', password: 'pw' })}
        data-testid="login-btn"
      >
        Login
      </button>
      <button onClick={() => logout()} data-testid="logout-btn">
        Logout
      </button>
      <button
        onClick={() => register({ email: 'a@b.com', password: 'pw' })}
        data-testid="register-btn"
      >
        Register
      </button>
    </div>
  );
}

function renderWithProvider() {
  return render(
    <AuthProvider>
      <TestConsumer />
    </AuthProvider>,
  );
}

describe('AuthProvider', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('session restore on mount', () => {
    it('sets user state when getMe resolves', async () => {
      mockGetMe.mockResolvedValueOnce(TEST_USER);

      renderWithProvider();

      // Initially loading
      expect(screen.getByTestId('loading').textContent).toBe('loading');

      await waitFor(() => {
        expect(screen.getByTestId('loading').textContent).toBe('ready');
      });

      expect(screen.getByTestId('user').textContent).toBe(TEST_USER.email);
    });

    it('leaves user null when getMe rejects', async () => {
      mockGetMe.mockRejectedValueOnce(new Error('not authenticated'));

      renderWithProvider();

      await waitFor(() => {
        expect(screen.getByTestId('loading').textContent).toBe('ready');
      });

      expect(screen.getByTestId('user').textContent).toBe('no-user');
    });

    it('isLoading is true during getMe and false after', async () => {
      let resolveGetMe!: (user: typeof TEST_USER) => void;
      mockGetMe.mockImplementationOnce(
        () => new Promise<typeof TEST_USER>((res) => { resolveGetMe = res; }),
      );

      renderWithProvider();

      expect(screen.getByTestId('loading').textContent).toBe('loading');

      await act(async () => {
        resolveGetMe(TEST_USER);
      });

      expect(screen.getByTestId('loading').textContent).toBe('ready');
    });
  });

  describe('login', () => {
    it('sets user state after successful login', async () => {
      mockGetMe.mockRejectedValueOnce(new Error('not authenticated'));
      mockLogin.mockResolvedValueOnce({ user: TEST_USER });

      renderWithProvider();

      await waitFor(() => {
        expect(screen.getByTestId('loading').textContent).toBe('ready');
      });

      await act(async () => {
        screen.getByTestId('login-btn').click();
      });

      expect(screen.getByTestId('user').textContent).toBe(TEST_USER.email);
    });

    it('calls login with provided credentials', async () => {
      mockGetMe.mockRejectedValueOnce(new Error('not authenticated'));
      mockLogin.mockResolvedValueOnce({ user: TEST_USER });

      renderWithProvider();

      await waitFor(() => screen.getByTestId('loading').textContent === 'ready');

      await act(async () => {
        screen.getByTestId('login-btn').click();
      });

      expect(mockLogin).toHaveBeenCalledWith({ email: 'a@b.com', password: 'pw' });
    });
  });

  describe('logout', () => {
    it('clears user state after logout', async () => {
      mockGetMe.mockResolvedValueOnce(TEST_USER);
      mockLogout.mockResolvedValueOnce(undefined);

      renderWithProvider();

      await waitFor(() => {
        expect(screen.getByTestId('user').textContent).toBe(TEST_USER.email);
      });

      await act(async () => {
        screen.getByTestId('logout-btn').click();
      });

      expect(screen.getByTestId('user').textContent).toBe('no-user');
    });

    it('clears user state even when logout API call fails', async () => {
      mockGetMe.mockResolvedValueOnce(TEST_USER);
      mockLogout.mockRejectedValueOnce(new Error('network error'));

      renderWithProvider();

      await waitFor(() => {
        expect(screen.getByTestId('user').textContent).toBe(TEST_USER.email);
      });

      await act(async () => {
        screen.getByTestId('logout-btn').click();
      });

      expect(screen.getByTestId('user').textContent).toBe('no-user');
    });
  });

  describe('register', () => {
    it('sets user state after successful registration', async () => {
      mockGetMe.mockRejectedValueOnce(new Error('not authenticated'));
      mockRegister.mockResolvedValueOnce({ user: TEST_USER });

      renderWithProvider();

      await waitFor(() => {
        expect(screen.getByTestId('loading').textContent).toBe('ready');
      });

      await act(async () => {
        screen.getByTestId('register-btn').click();
      });

      expect(screen.getByTestId('user').textContent).toBe(TEST_USER.email);
    });
  });

  describe('useAuth hook', () => {
    it('throws when used outside AuthProvider', () => {
      // Suppress console.error for this expected error
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      expect(() => render(<TestConsumer />)).toThrow(
        'useAuth must be used within AuthProvider',
      );
      consoleSpy.mockRestore();
    });
  });
});
