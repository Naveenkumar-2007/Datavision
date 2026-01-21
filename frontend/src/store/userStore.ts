import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  company?: string;
  role?: string;
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sources?: string[];
  // 🏆 Competition-winning features
  suggestions?: string[];  // Dynamic follow-up suggestions
  confidence?: number;     // Data grounding confidence (0-1)
  mode?: string;           // Which AI mode generated this
}

interface Conversation {
  id: string;
  title: string;
  messages: ChatMessage[];
  mode: string;
  createdAt: string;
  updatedAt: string;
}

interface UserState {
  user: User | null;
  setUser: (user: User) => void;
  logout: () => void;

  // Chat history - multiple conversations
  conversations: Conversation[];
  currentConversationId: string | null;

  // Actions
  createConversation: (mode?: string) => string;
  deleteConversation: (id: string) => void;
  selectConversation: (id: string) => void;
  addMessageToConversation: (conversationId: string, message: ChatMessage) => void;
  updateConversationMessages: (conversationId: string, messages: ChatMessage[]) => void;
  updateConversationTitle: (id: string, title: string) => void;
  getCurrentConversation: () => Conversation | null;
  clearCurrentChat: () => void;
  clearAllChats: () => void;

  // Stats
  graphStats: { nodes: number; relationships: number };
  queryStats: { totalQueries: number; avgResponseTime: number };
  setGraphStats: (stats: { nodes: number; relationships: number }) => void;
  setQueryStats: (stats: { totalQueries: number; avgResponseTime: number }) => void;

  // Theme
  isDark: boolean;
  toggleTheme: () => void;
  setTheme: (isDark: boolean) => void;
}

// NOTE: Removed createWelcomeMessage - WelcomeScreen in AnalystChat handles empty state
// This allows ChatGPT-style centered input to show on fresh chats

const createNewConversation = (mode: string = 'rag'): Conversation => {
  const now = new Date();
  return {
    id: `conv_${Date.now()}`,
    title: 'New Chat',
    messages: [],  // Empty - WelcomeScreen will display instead
    mode,
    createdAt: now.toISOString(),
    updatedAt: now.toISOString(),
  };
};

export const useUserStore = create<UserState>()(
  persist(
    (set, get) => ({
      // Start with null - will be populated from AuthContext
      user: null,
      setUser: (user) => set({ user }),
      logout: () => set({ user: null }),

      // Initialize with one conversation
      conversations: [createNewConversation()],
      currentConversationId: null,

      // Create new conversation
      createConversation: (mode = 'rag') => {
        const newConv = createNewConversation(mode);
        set((state) => ({
          conversations: [newConv, ...state.conversations],
          currentConversationId: newConv.id,
        }));
        return newConv.id;
      },

      // Delete conversation
      deleteConversation: (id) => {
        set((state) => {
          const filtered = state.conversations.filter(c => c.id !== id);
          let newCurrentId = state.currentConversationId;
          if (state.currentConversationId === id) {
            if (filtered.length > 0) {
              newCurrentId = filtered[0].id;
            } else {
              const newConv = createNewConversation();
              filtered.push(newConv);
              newCurrentId = newConv.id;
            }
          }
          return {
            conversations: filtered,
            currentConversationId: newCurrentId,
          };
        });
      },

      // Select conversation
      selectConversation: (id) => {
        set({ currentConversationId: id });
      },

      // Add message to conversation
      addMessageToConversation: (conversationId, message) => {
        set((state) => ({
          conversations: state.conversations.map(conv => {
            if (conv.id === conversationId) {
              let title = conv.title;
              if (title === 'New Chat' && message.role === 'user') {
                title = message.content.substring(0, 35) + (message.content.length > 35 ? '...' : '');
              }
              return {
                ...conv,
                title,
                messages: [...conv.messages, message],
                updatedAt: new Date().toISOString(),
              };
            }
            return conv;
          }),
        }));
      },

      // Update conversation messages (for edit/resend feature)
      updateConversationMessages: (conversationId, messages) => {
        set((state) => ({
          conversations: state.conversations.map(conv => {
            if (conv.id === conversationId) {
              return {
                ...conv,
                messages,
                updatedAt: new Date().toISOString(),
              };
            }
            return conv;
          }),
        }));
      },

      // Update conversation title
      updateConversationTitle: (id, title) => {
        set((state) => ({
          conversations: state.conversations.map(conv =>
            conv.id === id ? { ...conv, title } : conv
          ),
        }));
      },

      // Get current conversation
      getCurrentConversation: () => {
        const state = get();
        if (!state.currentConversationId) {
          if (state.conversations.length > 0) {
            return state.conversations[0];
          }
          return null;
        }
        return state.conversations.find(c => c.id === state.currentConversationId) || null;
      },

      // Clear current chat messages
      clearCurrentChat: () => {
        set((state) => ({
          conversations: state.conversations.map(conv => {
            if (conv.id === state.currentConversationId) {
              return {
                ...conv,
                messages: [],  // Empty - shows WelcomeScreen
                title: 'New Chat',
                updatedAt: new Date().toISOString(),
              };
            }
            return conv;
          }),
        }));
      },

      // Clear all chats and start fresh
      clearAllChats: () => {
        const newConv = createNewConversation();
        set({
          conversations: [newConv],
          currentConversationId: newConv.id,
        });
      },

      // Stats
      graphStats: { nodes: 0, relationships: 0 },
      queryStats: { totalQueries: 0, avgResponseTime: 0 },
      setGraphStats: (stats) => set({ graphStats: stats }),
      setQueryStats: (stats) => set({ queryStats: stats }),

      // Theme logic - Initialize from userPreferences if available
      isDark: (() => {
        try {
          // Check userPreferences first (Settings page source of truth)
          const savedPrefs = localStorage.getItem('userPreferences');
          if (savedPrefs) {
            const parsed = JSON.parse(savedPrefs);
            if (parsed.preferences?.theme === 'light') return false;
            if (parsed.preferences?.theme === 'dark') return true;
          }
          // Fallback to persisted store or default
          return true;
        } catch (e) {
          return true;
        }
      })(),

      toggleTheme: () => set((state) => {
        const newIsDark = !state.isDark;

        // Update DOM immediately
        if (newIsDark) {
          document.documentElement.classList.remove('light-theme');
          document.documentElement.classList.add('dark');
        } else {
          document.documentElement.classList.add('light-theme');
          document.documentElement.classList.remove('dark');
        }

        // Sync with userPreferences for persistence
        try {
          const userId = get().user?.id || localStorage.getItem('userId') || 'default';
          // Update global pref
          const saved = localStorage.getItem('userPreferences');
          let prefs = saved ? JSON.parse(saved) : { preferences: {} };
          if (!prefs.preferences) prefs.preferences = {};
          prefs.preferences.theme = newIsDark ? 'dark' : 'light';
          localStorage.setItem('userPreferences', JSON.stringify(prefs));

          // Update user specific pref if possible
          if (userId && userId !== 'default') {
            localStorage.setItem(`userPreferences_${userId}`, JSON.stringify(prefs));
          }
        } catch (e) {
          console.error("Failed to sync theme preference", e);
        }

        return { isDark: newIsDark };
      }),

      setTheme: (isDark) => set(() => {
        if (isDark) {
          document.documentElement.classList.remove('light-theme');
          document.documentElement.classList.add('dark');
        } else {
          document.documentElement.classList.add('light-theme');
          document.documentElement.classList.remove('dark');
        }
        return { isDark };
      }),
    }),
    {
      name: 'ai-analyst-storage-v2',
      partialize: (state) => ({
        user: state.user,  // Persist user data including avatar
        conversations: state.conversations,
        currentConversationId: state.currentConversationId,
        graphStats: state.graphStats,
        queryStats: state.queryStats,
        isDark: state.isDark, // Persist theme
      }),
    }
  )
);
