import { EventEmitter } from 'events';

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

export class DataCache<T> extends EventEmitter {
  private cache: Map<string, CacheEntry<T>> = new Map();
  private cleanupInterval: NodeJS.Timeout;

  constructor(private defaultTTL: number = 3600000) {  // 1 hour default
    super();

    // Cleanup expired entries every minute
    this.cleanupInterval = setInterval(() => {
      this.cleanupExpired();
    }, 60000);
  }

  set(key: string, value: T, ttl?: number): void {
    const entry: CacheEntry<T> = {
      data: value,
      timestamp: Date.now(),
      ttl: ttl || this.defaultTTL
    };
    this.cache.set(key, entry);
    this.emit('set', key, value);
  }

  get(key: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) return null;

    const now = Date.now();
    if (now - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      return null;
    }

    return entry.data;
  }

  delete(key: string): boolean {
    const result = this.cache.delete(key);
    if (result) {
      this.emit('delete', key);
    }
    return result;
  }

  clear(): void {
    this.cache.clear();
    this.emit('clear');
  }

  private cleanupExpired(): void {
    const now = Date.now();
    for (const [key, entry] of this.cache.entries()) {
      if (now - entry.timestamp > entry.ttl) {
        this.cache.delete(key);
      }
    }
  }

  destroy(): void {
    clearInterval(this.cleanupInterval);
    this.clear();
    this.removeAllListeners();
  }
}