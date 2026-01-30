import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { act } from '@testing-library/react';

// Mock localStorage before importing the store
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

// Import store after mocking localStorage
import { useUserStore } from './userStore';

describe('User Store', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
  });

  describe('User management', () => {
    it('should set user', () => {
      const user = {
        id: '1',
        name: 'Test User',
        email: 'test@example.com',
      };

      act(() => {
        useUserStore.getState().setUser(user);
      });

      expect(useUserStore.getState().user).toEqual(user);
    });

    it('should logout user', () => {
      const user = {
        id: '1',
        name: 'Test User',
        email: 'test@example.com',
      };

      act(() => {
        useUserStore.getState().setUser(user);
      });

      act(() => {
        useUserStore.getState().logout();
      });

      expect(useUserStore.getState().user).toBeNull();
    });
  });

  describe('Theme management', () => {
    it('should have isDark property', () => {
      const state = useUserStore.getState();
      expect(typeof state.isDark).toBe('boolean');
    });

    it('should toggle theme', () => {
      const initialTheme = useUserStore.getState().isDark;

      act(() => {
        useUserStore.getState().toggleTheme();
      });

      expect(useUserStore.getState().isDark).toBe(!initialTheme);
    });

    it('should set theme explicitly', () => {
      act(() => {
        useUserStore.getState().setTheme(false);
      });

      expect(useUserStore.getState().isDark).toBe(false);

      act(() => {
        useUserStore.getState().setTheme(true);
      });

      expect(useUserStore.getState().isDark).toBe(true);
    });
  });

  describe('Conversation management', () => {
    it('should create a new conversation', () => {
      const initialCount = useUserStore.getState().conversations.length;

      let convId: string;
      act(() => {
        convId = useUserStore.getState().createConversation();
      });

      const state = useUserStore.getState();
      expect(state.conversations.length).toBe(initialCount + 1);
      expect(state.currentConversationId).toBe(convId!);
    });

    it('should create conversation with specific mode', () => {
      act(() => {
        useUserStore.getState().createConversation('expert');
      });

      const state = useUserStore.getState();
      const latestConv = state.conversations[0]; // Newest is first
      expect(latestConv.mode).toBe('expert');
    });

    it('should select a conversation', () => {
      let convId1: string;
      let convId2: string;

      act(() => {
        convId1 = useUserStore.getState().createConversation();
      });

      act(() => {
        convId2 = useUserStore.getState().createConversation();
      });

      act(() => {
        useUserStore.getState().selectConversation(convId1!);
      });

      expect(useUserStore.getState().currentConversationId).toBe(convId1!);
    });

    it('should add message to conversation', () => {
      let convId: string;

      act(() => {
        convId = useUserStore.getState().createConversation();
      });

      const message = {
        id: 'msg_1',
        role: 'user' as const,
        content: 'Hello!',
        timestamp: new Date().toISOString(),
      };

      act(() => {
        useUserStore.getState().addMessageToConversation(convId!, message);
      });

      const state = useUserStore.getState();
      const conv = state.conversations.find(c => c.id === convId!);
      expect(conv?.messages.length).toBe(1);
      expect(conv?.messages[0].content).toBe('Hello!');
    });

    it('should update conversation title', () => {
      let convId: string;

      act(() => {
        convId = useUserStore.getState().createConversation();
      });

      act(() => {
        useUserStore.getState().updateConversationTitle(convId!, 'Updated Title');
      });

      const state = useUserStore.getState();
      const conv = state.conversations.find(c => c.id === convId!);
      expect(conv?.title).toBe('Updated Title');
    });

    it('should delete a conversation', () => {
      let convId: string;

      act(() => {
        convId = useUserStore.getState().createConversation();
      });

      const countBefore = useUserStore.getState().conversations.length;
      
      // Verify the conversation exists
      expect(useUserStore.getState().conversations.find(c => c.id === convId)).toBeDefined();

      act(() => {
        useUserStore.getState().deleteConversation(convId!);
      });

      // Verify the conversation was deleted (no longer found by that id)
      expect(useUserStore.getState().conversations.find(c => c.id === convId)).toBeUndefined();
    });
  });

  describe('Stats management', () => {
    it('should set graph stats', () => {
      act(() => {
        useUserStore.getState().setGraphStats({ nodes: 100, relationships: 50 });
      });

      expect(useUserStore.getState().graphStats).toEqual({ nodes: 100, relationships: 50 });
    });

    it('should set query stats', () => {
      act(() => {
        useUserStore.getState().setQueryStats({ totalQueries: 500, avgResponseTime: 1.5 });
      });

      expect(useUserStore.getState().queryStats).toEqual({ totalQueries: 500, avgResponseTime: 1.5 });
    });
  });
});
