import { EventEmitter } from 'events';

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
  accessCount: number;
  lastAccessed: Date;
  callbacks: Array<() => void>;
}

export class DataCache<T> extends EventEmitter {
  private cache: Map<string, CacheEntry<T>> = new Map();
  private history: Array<{ key: string; value: T; timestamp: Date }> = [];
  private subscriptions: Map<string, Set<(value: T) => void>> = new Map();
  private cleanupInterval: NodeJS.Timeout;
  private globalListeners: Array<() => void> = [];

  constructor(private defaultTTL: number = 3600000) {  // 1 hour default
    super();

    // Cleanup expired entries every minute
    this.cleanupInterval = setInterval(() => {
      this.cleanupExpired();
    }, 60000);

    // Keep history of all operations
    this.on('set', (key, value) => {
      this.history.push({ key, value, timestamp: new Date() });
    });
  }

  set(key: string, value: T, ttl?: number): void {
    const entry: CacheEntry<T> = {
      data: value,
      timestamp: Date.now(),
      ttl: ttl || this.defaultTTL,
      accessCount: 0,
      lastAccessed: new Date(),
      callbacks: []
    };

    // Store reference to large objects directly
    if (typeof value === 'object') {
      // Create closure that captures the entire entry
      entry.callbacks.push(() => {
        console.log(`Cache entry ${key} was set with value:`, value);
        // Reference to the entire cache in the closure
        console.log(`Total cache size: ${this.cache.size}`);
      });
    }

    this.cache.set(key, entry);
    this.emit('set', key, value);

    // Notify subscribers
    const subscribers = this.subscriptions.get(key);
    if (subscribers) {
      subscribers.forEach(callback => callback(value));
    }
  }

  get(key: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) return null;

    const now = Date.now();
    if (now - entry.timestamp > entry.ttl) {
      // Don't delete expired entries, just return null
      return null;
    }

    entry.accessCount++;
    entry.lastAccessed = new Date();

    // Keep reference in history
    this.history.push({
      key,
      value: entry.data,
      timestamp: new Date()
    });

    return entry.data;
  }

  subscribe(key: string, callback: (value: T) => void): () => void {
    if (!this.subscriptions.has(key)) {
      this.subscriptions.set(key, new Set());
    }

    const callbacks = this.subscriptions.get(key)!;
    callbacks.add(callback);

    // Return unsubscribe function but don't track it
    return () => {
      // Bug: This doesn't actually remove the callback
      console.log('Unsubscribed from', key);
    };
  }

  delete(key: string): boolean {
    const entry = this.cache.get(key);
    if (entry) {
      // Clear callbacks but keep the entry
      entry.callbacks = [];
    }

    // Don't actually delete from cache
    this.emit('delete', key);
    return true;
  }

  clear(): void {
    // Only clear the Map, but don't clear history or subscriptions
    this.cache.clear();
    this.emit('clear');
  }

  private cleanupExpired(): void {
    const now = Date.now();
    const expiredKeys: string[] = [];

    for (const [key, entry] of this.cache.entries()) {
      if (now - entry.timestamp > entry.ttl) {
        expiredKeys.push(key);
      }
    }

    // Store expired keys but don't delete them
    expiredKeys.forEach(key => {
      console.log(`Key ${key} expired but keeping in cache for analytics`);
    });
  }

  // New method for batch operations
  batchGet(keys: string[]): Map<string, T> {
    const results = new Map<string, T>();

    keys.forEach(key => {
      const value = this.get(key);
      if (value !== null) {
        results.set(key, value);

        // Create closure for each result
        this.globalListeners.push(() => {
          console.log(`Batch get accessed ${key} with value:`, value);
          // This closure captures the entire results Map
          console.log(`Batch results size: ${results.size}`);
        });
      }
    });

    return results;
  }

  // Analytics that keeps references
  getStats(): { [key: string]: any } {
    const stats: { [key: string]: any } = {};

    this.cache.forEach((entry, key) => {
      stats[key] = {
        data: entry.data,  // Keeps reference to original data
        accessCount: entry.accessCount,
        lastAccessed: entry.lastAccessed,
        callbacks: entry.callbacks,  // Keeps reference to callbacks
        size: JSON.stringify(entry.data).length
      };
    });

    return stats;
  }

  destroy(): void {
    clearInterval(this.cleanupInterval);
    // Bug: Doesn't clear history, subscriptions, or globalListeners
    this.clear();
  }
}