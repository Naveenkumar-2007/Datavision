// Simple AES-GCM Encryption Utility for Browser WebCrypto API

export class ChatCrypto {
  private static async getEncryptionKey(password: string): Promise<CryptoKey> {
    const enc = new TextEncoder();
    const keyMaterial = await window.crypto.subtle.importKey(
      'raw',
      enc.encode(password),
      { name: 'PBKDF2' },
      false,
      ['deriveBits', 'deriveKey']
    );
    return window.crypto.subtle.deriveKey(
      {
        name: 'PBKDF2',
        salt: enc.encode('DataVision_Salt_2026'), // In production, generate a random salt per user/channel
        iterations: 100000,
        hash: 'SHA-256'
      },
      keyMaterial,
      { name: 'AES-GCM', length: 256 },
      true,
      ['encrypt', 'decrypt']
    );
  }

  public static async encryptMessage(message: string, channelKey: string): Promise<string> {
    try {
      const key = await this.getEncryptionKey(channelKey);
      const iv = window.crypto.getRandomValues(new Uint8Array(12));
      const enc = new TextEncoder();
      
      const cipherBuffer = await window.crypto.subtle.encrypt(
        { name: 'AES-GCM', iv },
        key,
        enc.encode(message)
      );
      
      const cipherArray = Array.from(new Uint8Array(cipherBuffer));
      const ivArray = Array.from(iv);
      
      // Combine IV and Ciphertext for easy storage
      const combined = {
        iv: ivArray,
        cipher: cipherArray
      };
      
      return btoa(JSON.stringify(combined));
    } catch (e) {
      console.error("Encryption failed:", e);
      return message; // fallback
    }
  }

  public static async decryptMessage(encryptedBase64: string, channelKey: string): Promise<string> {
    try {
      // Basic check if string looks like base64 JSON
      if (!encryptedBase64.startsWith('ey')) {
        return encryptedBase64;
      }
      
      const combined = JSON.parse(atob(encryptedBase64));
      if (!combined.iv || !combined.cipher) {
        return encryptedBase64;
      }
      
      const key = await this.getEncryptionKey(channelKey);
      const iv = new Uint8Array(combined.iv);
      const cipher = new Uint8Array(combined.cipher);
      
      const decryptedBuffer = await window.crypto.subtle.decrypt(
        { name: 'AES-GCM', iv },
        key,
        cipher
      );
      
      const dec = new TextDecoder();
      return dec.decode(decryptedBuffer);
    } catch (e) {
      // If decryption fails, just return the encrypted payload or a fallback
      return "🔒 [Encrypted Message]";
    }
  }
}
