# Crawling Design - Ulixee Hero

## 1. Overview

### 1.1 Tool Selection

| Item | Value |
|------|-------|
| **Tool** | Ulixee Hero |
| **Documentation** | https://ulixee.org/docs/hero |
| **Type** | Headless Browser (Chromium-based) |
| **Language** | TypeScript / JavaScript |
| **Use Case** | Web scraping, data extraction, automation |

### 1.2 Why Ulixee Hero?

- **Anti-detection**: Built-in bot detection bypass
- **Human-like behavior**: Realistic mouse movements, typing patterns
- **Session management**: Cookie/session persistence
- **Modern web support**: SPA, dynamic content, JavaScript rendering
- **TypeScript native**: Type-safe development

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Crawling Architecture                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [Next.js API / Worker]                                        │
│         │                                                       │
│         ▼                                                       │
│  [Ulixee Hero Client]                                          │
│         │                                                       │
│         ├─── YouTube Crawler ──→ Recipe videos                 │
│         │                                                       │
│         ├─── Naver Crawler ───→ Shopping products              │
│         │                                                       │
│         └─── Coupang Crawler ─→ Shopping products              │
│         │                                                       │
│         ▼                                                       │
│  [Cache Layer]                                                  │
│         ├─── Redis (short-term: 1-6h)                          │
│         └─── PostgreSQL (long-term: youtube_cache, commerce_cache)
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Installation

### 3.1 Dependencies

```bash
# Core packages
npm install @ulixee/hero-playground
npm install @ulixee/hero

# For production (separate cloud process)
npm install @ulixee/cloud
```

### 3.2 Project Structure

```
src/
├── lib/
│   └── crawler/
│       ├── index.ts           # Crawler exports
│       ├── hero-client.ts     # Hero client singleton
│       ├── youtube.ts         # YouTube crawler
│       ├── naver.ts           # Naver Shopping crawler
│       └── coupang.ts         # Coupang crawler
└── workers/
    └── crawl-worker.ts        # Background crawl jobs
```

---

## 4. Implementation

### 4.1 Hero Client Singleton

```typescript
// src/lib/crawler/hero-client.ts
import Hero from '@ulixee/hero';

let heroInstance: Hero | null = null;

export async function getHero(): Promise<Hero> {
  if (!heroInstance) {
    heroInstance = new Hero({
      showChrome: false,  // headless
      userAgent: '~chrome-latest',
    });
  }
  return heroInstance;
}

export async function closeHero(): Promise<void> {
  if (heroInstance) {
    await heroInstance.close();
    heroInstance = null;
  }
}
```

### 4.2 YouTube Crawler

```typescript
// src/lib/crawler/youtube.ts
import Hero from '@ulixee/hero';

interface YouTubeVideo {
  videoId: string;
  title: string;
  thumbnail: string;
  channelName: string;
  viewCount: string;
  duration: string;
  publishedAt: string;
}

export async function crawlYouTubeRecipes(
  query: string,
  maxResults: number = 5
): Promise<YouTubeVideo[]> {
  const hero = new Hero({
    showChrome: false,
    userAgent: '~chrome-latest',
  });

  try {
    const searchUrl = `https://www.youtube.com/results?search_query=${encodeURIComponent(query + ' 레시피 만들기')}`;
    
    await hero.goto(searchUrl);
    await hero.waitForPaintingStable();

    // Wait for video results to load
    await hero.waitForElement('ytd-video-renderer');

    const videos: YouTubeVideo[] = [];
    const videoElements = await hero.querySelectorAll('ytd-video-renderer');

    for (let i = 0; i < Math.min(videoElements.length, maxResults); i++) {
      const el = videoElements[i];
      
      const videoId = await el.$eval('a#thumbnail', (a) => {
        const href = a.getAttribute('href');
        return href?.split('v=')[1]?.split('&')[0] || '';
      });

      const title = await el.$eval('#video-title', (t) => t.textContent?.trim() || '');
      const thumbnail = `https://i.ytimg.com/vi/${videoId}/hqdefault.jpg`;
      const channelName = await el.$eval('#channel-name', (c) => c.textContent?.trim() || '');
      const viewCount = await el.$eval('#metadata-line span:first-child', (s) => s.textContent?.trim() || '');
      const publishedAt = await el.$eval('#metadata-line span:last-child', (s) => s.textContent?.trim() || '');

      if (videoId) {
        videos.push({
          videoId,
          title,
          thumbnail,
          channelName,
          viewCount,
          duration: '',
          publishedAt,
        });
      }
    }

    return videos;
  } finally {
    await hero.close();
  }
}
```

### 4.3 Naver Shopping Crawler

```typescript
// src/lib/crawler/naver.ts
import Hero from '@ulixee/hero';

interface NaverProduct {
  productId: string;
  title: string;
  price: number;
  image: string;
  mallName: string;
  link: string;
  category: string;
}

export async function crawlNaverShopping(
  query: string,
  maxResults: number = 5
): Promise<NaverProduct[]> {
  const hero = new Hero({
    showChrome: false,
    userAgent: '~chrome-latest',
  });

  try {
    const searchUrl = `https://search.shopping.naver.com/search/all?query=${encodeURIComponent(query)}`;
    
    await hero.goto(searchUrl);
    await hero.waitForPaintingStable();

    // Wait for product list
    await hero.waitForElement('.product_list');

    const products: NaverProduct[] = [];
    const productElements = await hero.querySelectorAll('.product_item');

    for (let i = 0; i < Math.min(productElements.length, maxResults); i++) {
      const el = productElements[i];
      
      const title = await el.$eval('.product_title', (t) => t.textContent?.trim() || '');
      const priceText = await el.$eval('.price_num', (p) => p.textContent?.trim() || '0');
      const price = parseInt(priceText.replace(/[^0-9]/g, ''), 10);
      const image = await el.$eval('img', (img) => img.getAttribute('src') || '');
      const mallName = await el.$eval('.product_mall', (m) => m.textContent?.trim() || '');
      const link = await el.$eval('a', (a) => a.getAttribute('href') || '');

      if (title && price > 0) {
        products.push({
          productId: `naver_${i}`,
          title,
          price,
          image,
          mallName,
          link,
          category: query,
        });
      }
    }

    return products;
  } finally {
    await hero.close();
  }
}
```

### 4.4 Coupang Crawler

```typescript
// src/lib/crawler/coupang.ts
import Hero from '@ulixee/hero';

interface CoupangProduct {
  productId: string;
  title: string;
  price: number;
  originalPrice?: number;
  image: string;
  rating?: number;
  reviewCount?: number;
  link: string;
  isRocketDelivery: boolean;
}

export async function crawlCoupang(
  query: string,
  maxResults: number = 5
): Promise<CoupangProduct[]> {
  const hero = new Hero({
    showChrome: false,
    userAgent: '~chrome-latest',
  });

  try {
    const searchUrl = `https://www.coupang.com/np/search?component=&q=${encodeURIComponent(query)}`;
    
    await hero.goto(searchUrl);
    await hero.waitForPaintingStable();

    // Wait for product list
    await hero.waitForElement('.search-product-list');

    const products: CoupangProduct[] = [];
    const productElements = await hero.querySelectorAll('.search-product');

    for (let i = 0; i < Math.min(productElements.length, maxResults); i++) {
      const el = productElements[i];
      
      const title = await el.$eval('.name', (t) => t.textContent?.trim() || '');
      const priceText = await el.$eval('.price-value', (p) => p.textContent?.trim() || '0');
      const price = parseInt(priceText.replace(/[^0-9]/g, ''), 10);
      const image = await el.$eval('img', (img) => img.getAttribute('src') || '');
      const link = await el.$eval('a', (a) => a.getAttribute('href') || '');
      const isRocketDelivery = await el.$eval('.rocket-icon', () => true).catch(() => false);

      if (title && price > 0) {
        products.push({
          productId: `coupang_${i}`,
          title,
          price,
          image,
          link: `https://www.coupang.com${link}`,
          isRocketDelivery,
        });
      }
    }

    return products;
  } finally {
    await hero.close();
  }
}
```

---

## 5. Caching Strategy

### 5.1 Cache Flow

```
[Crawl Request]
      │
      ▼
[1. Redis Cache Check] ─── Hit ──→ Return cached data
      │ Miss
      ▼
[2. PostgreSQL Cache Check] ─── Hit (not expired) ──→ Return + Update Redis
      │ Miss/Expired
      ▼
[3. Execute Hero Crawler]
      │
      ▼
[4. Save to PostgreSQL + Redis]
      │
      ▼
[Return data]
```

### 5.2 Cache TTL

| Source | Redis TTL | PostgreSQL expires_at |
|--------|-----------|----------------------|
| YouTube | 6 hours | 6 hours |
| Naver Shopping | 1 hour | 1 hour |
| Coupang | 1 hour | 1 hour |

### 5.3 Cache Implementation

```typescript
// src/lib/crawler/cache.ts
import { createClient } from 'redis';
import { createClient as createSupabase } from '@supabase/supabase-js';
import crypto from 'crypto';

const redis = createClient({ url: process.env.REDIS_URL });
const supabase = createSupabase(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

function hashQuery(query: string): string {
  return crypto.createHash('sha256').update(query).digest('hex');
}

export async function getCachedYouTube(query: string) {
  const hash = hashQuery(query);
  const cacheKey = `youtube:${hash}`;

  // 1. Check Redis
  const redisData = await redis.get(cacheKey);
  if (redisData) {
    return JSON.parse(redisData);
  }

  // 2. Check PostgreSQL
  const { data } = await supabase
    .from('youtube_cache')
    .select('results')
    .eq('query_hash', hash)
    .gt('expires_at', new Date().toISOString())
    .single();

  if (data) {
    // Update Redis
    await redis.setEx(cacheKey, 6 * 60 * 60, JSON.stringify(data.results));
    return data.results;
  }

  return null;
}

export async function setCachedYouTube(query: string, results: any) {
  const hash = hashQuery(query);
  const cacheKey = `youtube:${hash}`;
  const expiresAt = new Date(Date.now() + 6 * 60 * 60 * 1000);

  // Save to Redis
  await redis.setEx(cacheKey, 6 * 60 * 60, JSON.stringify(results));

  // Save to PostgreSQL
  await supabase.from('youtube_cache').upsert({
    query_hash: hash,
    query,
    results,
    result_count: results.length,
    expires_at: expiresAt.toISOString(),
  });
}
```

---

## 6. Worker Integration

### 6.1 Crawl Worker

```typescript
// src/workers/crawl-worker.ts
import { Worker, Job } from 'bullmq';
import { crawlYouTubeRecipes } from '../lib/crawler/youtube';
import { crawlNaverShopping } from '../lib/crawler/naver';
import { crawlCoupang } from '../lib/crawler/coupang';
import { getCachedYouTube, setCachedYouTube } from '../lib/crawler/cache';

interface CrawlJob {
  type: 'youtube' | 'naver' | 'coupang';
  query: string;
  maxResults?: number;
}

const worker = new Worker<CrawlJob>('crawl-queue', async (job: Job<CrawlJob>) => {
  const { type, query, maxResults = 5 } = job.data;

  switch (type) {
    case 'youtube': {
      const cached = await getCachedYouTube(query);
      if (cached) return cached;

      const results = await crawlYouTubeRecipes(query, maxResults);
      await setCachedYouTube(query, results);
      return results;
    }

    case 'naver': {
      const results = await crawlNaverShopping(query, maxResults);
      // Cache similar to YouTube
      return results;
    }

    case 'coupang': {
      const results = await crawlCoupang(query, maxResults);
      // Cache similar to YouTube
      return results;
    }

    default:
      throw new Error(`Unknown crawl type: ${type}`);
  }
}, {
  connection: {
    host: process.env.REDIS_HOST,
    port: parseInt(process.env.REDIS_PORT || '6379'),
  },
  concurrency: 3,  // Max 3 concurrent crawl jobs
});

export default worker;
```

---

## 7. API Endpoints

### 7.1 YouTube Content API

```
GET /api/youtube?query={query}&limit={limit}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| query | string | Yes | Search keyword (e.g., prescription name) |
| limit | number | No | Max results (default: 5, max: 10) |

### 7.2 Commerce API

```
GET /api/commerce?query={query}&provider={provider}&limit={limit}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| query | string | Yes | Product keyword (ingredient name) |
| provider | string | No | `naver`, `coupang`, or `all` (default: all) |
| limit | number | No | Max results per provider (default: 5) |

---

## 8. Error Handling

### 8.1 Retry Strategy

```typescript
const MAX_RETRIES = 3;
const RETRY_DELAY = 2000;  // 2 seconds

async function crawlWithRetry<T>(
  crawlFn: () => Promise<T>,
  retries = MAX_RETRIES
): Promise<T> {
  try {
    return await crawlFn();
  } catch (error) {
    if (retries > 0) {
      await new Promise(r => setTimeout(r, RETRY_DELAY));
      return crawlWithRetry(crawlFn, retries - 1);
    }
    throw error;
  }
}
```

### 8.2 Fallback Strategy

| Condition | Fallback |
|-----------|----------|
| Crawler timeout | Return cached data (even if expired) |
| Site blocking | Return empty + log alert |
| Parse error | Return partial data + log error |

---

## 9. Monitoring

### 9.1 Metrics to Track

| Metric | Description |
|--------|-------------|
| Crawl success rate | % of successful crawls |
| Average crawl time | Time per crawl request |
| Cache hit rate | Redis/PostgreSQL cache effectiveness |
| Error rate by source | Errors per YouTube/Naver/Coupang |
| Blocked rate | Detection/blocking frequency |

### 9.2 Alerts

- Crawl success rate < 90%
- Average crawl time > 10s
- Blocked rate > 5%

---

## 10. Change History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-24 | Initial design |
