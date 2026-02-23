import { db } from './database';

export class AnalyticsService {
  async trackPageView(pageId: string, userId: string): Promise<void> {
    // Simple page view tracking
    await db.query(
      'INSERT INTO page_views (page_id, user_id, timestamp) VALUES ($1, $2, $3)',
      [pageId, userId, new Date()]
    );
  }

  async getPageViewCount(pageId: string): Promise<number> {
    const result = await db.query(
      'SELECT COUNT(*) as count FROM page_views WHERE page_id = $1',
      [pageId]
    );
    return result.rows[0].count;
  }
}