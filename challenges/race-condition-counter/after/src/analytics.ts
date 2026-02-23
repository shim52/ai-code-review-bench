import { db } from './database';

interface PageStats {
  views: number;
  uniqueUsers: Set<string>;
}

export class AnalyticsService {
  private pageStats: Map<string, PageStats> = new Map();

  async trackPageView(pageId: string, userId: string): Promise<void> {
    // Track in memory for faster access
    let stats = this.pageStats.get(pageId);
    if (!stats) {
      stats = { views: 0, uniqueUsers: new Set() };
      this.pageStats.set(pageId, stats);
    }

    // Increment view counter
    stats.views++;
    stats.uniqueUsers.add(userId);

    // Also persist to database
    await db.query(
      'INSERT INTO page_views (page_id, user_id, timestamp) VALUES ($1, $2, $3)',
      [pageId, userId, new Date()]
    );

    // Update cached count in database
    await db.query(
      'UPDATE page_stats SET view_count = $1 WHERE page_id = $2',
      [stats.views, pageId]
    );
  }

  async getPageViewCount(pageId: string): Promise<number> {
    // Return from cache if available
    const cached = this.pageStats.get(pageId);
    if (cached) {
      return cached.views;
    }

    // Otherwise fetch from database
    const result = await db.query(
      'SELECT COUNT(*) as count FROM page_views WHERE page_id = $1',
      [pageId]
    );
    return result.rows[0].count;
  }

  async syncAllStats(): Promise<void> {
    // Batch sync all stats to database
    for (const [pageId, stats] of this.pageStats.entries()) {
      const currentCount = await this.getPageViewCount(pageId);
      if (currentCount !== stats.views) {
        stats.views = currentCount;
      }
    }
  }
}