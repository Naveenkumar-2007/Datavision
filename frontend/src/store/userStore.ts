import { create } from 'zustand';

interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
}

interface UserState {
  user: User | null;
  setUser: (user: User) => void;
  logout: () => void;
}

export const useUserStore = create<UserState>((set) => ({
  user: {
    id: 'user_001',
    name: 'Demo User',
    email: 'demo@enterprise.ai',
  },
  setUser: (user) => set({ user }),
  logout: () => set({ user: null }),
}));
