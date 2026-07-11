/**
 * User ID Utility - Ensures proper user isolation
 * 
 * CRITICAL: Each user (authenticated or guest) gets a unique ID.
 * This ID is used to isolate all user data (files, models, chats, etc.)
 */

import { supabase } from '../lib/auth-client';

const GUEST_ID_KEY = 'guestUserId';
const USER_ID_KEY = 'userId';

/**
 * Generate a unique guest ID
 */
function generateGuestId(): string {
  const timestamp = Date.now().toString(36);
  const randomPart = Math.random().toString(36).substring(2, 10);
  return `guest_${timestamp}_${randomPart}`;
}

/**
 * Get or create a guest user ID
 * This ensures guests have persistent, unique IDs
 */
function getOrCreateGuestId(): string {
  let guestId = localStorage.getItem(GUEST_ID_KEY);
  
  if (!guestId) {
    guestId = generateGuestId();
    localStorage.setItem(GUEST_ID_KEY, guestId);
    console.log('🆔 Created new guest ID:', guestId);
  }
  
  return guestId;
}

/**
 * Get the current user ID (authenticated or guest)
 * ALWAYS use this function to get user ID for API calls
 */
export async function getUserId(): Promise<string> {
  try {
    // First check auth session
    const { data: { session } } = await supabase.auth.getSession();
    
    if (session?.user?.id) {
      // Authenticated user - use their user ID
      localStorage.setItem(USER_ID_KEY, session.user.id);
      return session.user.id;
    }
  } catch (error) {
    console.warn('Could not check auth session:', error);
  }
  
  // Check for stored authenticated user ID
  const storedUserId = localStorage.getItem(USER_ID_KEY);
  if (storedUserId && !storedUserId.startsWith('guest_')) {
    return storedUserId;
  }
  
  // Fallback to guest ID
  return getOrCreateGuestId();
}

/**
 * Synchronous version - uses cached value
 * Prefer getUserId() when possible
 */
export function getUserIdSync(): string {
  // Check for authenticated user ID first
  const storedUserId = localStorage.getItem(USER_ID_KEY);
  if (storedUserId && !storedUserId.startsWith('guest_')) {
    return storedUserId;
  }
  
  // Fallback to guest ID
  return getOrCreateGuestId();
}

/**
 * Clear user data on logout
 */
export function clearUserData(): void {
  const userId = getUserIdSync();
  
  // Clear user-specific localStorage items
  const keysToRemove = [
    `mlResults_${userId}`,
    `hasMLResults_${userId}`,
    `userPreferences_${userId}`,
    `userProfile_${userId}`,
  ];
  
  keysToRemove.forEach(key => localStorage.removeItem(key));
  
  // Clear user-specific sessionStorage
  sessionStorage.removeItem(`mlCharts_${userId}`);
  
  // Remove authenticated user ID but keep guest ID
  localStorage.removeItem(USER_ID_KEY);
  
  console.log('🧹 Cleared user data for:', userId);
}

/**
 * Check if current user is authenticated
 */
export async function isAuthenticated(): Promise<boolean> {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    return !!session?.user;
  } catch {
    return false;
  }
}

/**
 * 🔐 Get authorization headers for fetch calls
 * Use this for all direct fetch() calls to ensure proper auth
 */
export async function getAuthHeaders(): Promise<Record<string, string>> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  
  try {
    const { data: { session } } = await supabase.auth.getSession();
    
    if (session?.access_token) {
      headers['Authorization'] = `Bearer ${session.access_token}`;
      headers['X-User-ID'] = session.user.id;
    } else {
      const guestId = getOrCreateGuestId();
      headers['X-User-ID'] = guestId;
    }
  } catch (error) {
    console.warn('Failed to get auth headers:', error);
    const guestId = getOrCreateGuestId();
    headers['X-User-ID'] = guestId;
  }
  
  return headers;
}

/**
 * Sync version - uses cached token if available
 */
export function getAuthHeadersSync(): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  
  const userId = localStorage.getItem(USER_ID_KEY);
  if (userId && !userId.startsWith('guest_')) {
    headers['X-User-ID'] = userId;
    // Note: For sync, we can't get the JWT token without async call
    // The interceptor in api.ts handles adding the token
  } else {
    const guestId = getOrCreateGuestId();
    headers['X-User-ID'] = guestId;
  }
  
  return headers;
}

export default {
  getUserId,
  getUserIdSync,
  clearUserData,
  isAuthenticated,
  getAuthHeaders,
  getAuthHeadersSync,
};
