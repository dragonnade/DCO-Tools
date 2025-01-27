// lib/services/cacheService.ts

import type { Project, Document, DocumentStage, DocumentCategory } from '../types/database.types';

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  expiresAt: number;
}

interface CacheOptions {
  ttl: number;           // Time to live in milliseconds
  maxSize: number;       // Maximum number of items to store
  refreshThreshold?: number; // Time before expiry to trigger refresh
}

export class CacheService<T> {
  private cache: Map<string, CacheEntry<T>>;
  private options: CacheOptions;
  private refreshHandler?: () => Promise<T>;

  constructor(options: CacheOptions) {
    this.cache = new Map();
    this.options = {
      ...options,
      // Default refresh threshold is 10% of TTL if not specified
      refreshThreshold: options.refreshThreshold || options.ttl * 0.1
    };
  }

  async set(key: string, data: T): Promise<void> {
    const timestamp = Date.now();
    const expiresAt = timestamp + this.options.ttl;

    if (this.cache.size >= this.options.maxSize) {
      const oldestKey = Array.from(this.cache.entries())
        .sort(([, a], [, b]) => a.timestamp - b.timestamp)[0][0];
      this.cache.delete(oldestKey);
    }

    this.cache.set(key, { data, timestamp, expiresAt });
  }

  async get(key: string): Promise<T | null> {
    const entry = this.cache.get(key);
    
    if (!entry) {
      return null;
    }

    // If we're past expiry, clear and return null
    if (Date.now() > entry.expiresAt) {
      this.cache.delete(key);
      return null;
    }

    // If we're approaching expiry and have a refresh handler, trigger background refresh
    const timeUntilExpiry = entry.expiresAt - Date.now();
    if (this.refreshHandler && timeUntilExpiry < this.options.refreshThreshold!) {
      this.triggerBackgroundRefresh(key).catch(console.error);
    }

    return entry.data;
  }

  private async triggerBackgroundRefresh(key: string): Promise<void> {
    if (!this.refreshHandler) return;

    try {
      const newData = await this.refreshHandler();
      await this.set(key, newData);
    } catch (error) {
      console.error('Background refresh failed:', error);
    }
  }

  setRefreshHandler(handler: () => Promise<T>): void {
    this.refreshHandler = handler;
  }

  clear(key?: string): void {
    if (key) {
      this.cache.delete(key);
    } else {
      this.cache.clear();
    }
  }
}

// Create optimized cache instances based on actual update frequencies

// Projects update once per day at most
export const projectCache = new CacheService<Project[]>({
  ttl: 24 * 60 * 60 * 1000,  // 24 hours
  maxSize: 100,              // Reasonable number of projects
  refreshThreshold: 2 * 60 * 60 * 1000  // Refresh if within 2 hours of expiry
});

// Documents update hourly at most
export const documentCache = new CacheService<Document[]>({
  ttl: 60 * 60 * 1000,      // 1 hour
  maxSize: 500,             // Store document lists for multiple projects
  refreshThreshold: 5 * 60 * 1000  // Refresh if within 5 minutes of expiry
});

// Stages and categories are static
export const stageCache = new CacheService<DocumentStage[]>({
  ttl: Number.POSITIVE_INFINITY,  // Never expires
  maxSize: 50  // Stages are static and few in number
});

export const categoryCache = new CacheService<DocumentCategory[]>({
  ttl: Number.POSITIVE_INFINITY,  // Never expires
  maxSize: 100  // Categories are static
});

// Initialize static data caches on application start
export async function initializeStaticCaches(): Promise<void> {
  try {
    const { data: stages } = await supabase
      .from('document_stages')
      .select('*')
      .order('display_order');
    
    if (stages) {
      await stageCache.set('all-stages', stages);
    }

    const { data: categories } = await supabase
      .from('document_categories')
      .select('*')
      .order('name');
    
    if (categories) {
      await categoryCache.set('all-categories', categories);
    }
  } catch (error) {
    console.error('Failed to initialize static caches:', error);
  }
}