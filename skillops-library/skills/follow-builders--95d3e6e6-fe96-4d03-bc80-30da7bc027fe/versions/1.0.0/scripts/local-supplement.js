#!/usr/bin/env node

// ============================================================================
// Follow Builders — Local Supplement
// ============================================================================
// 抓取「本地补充源」（config/local-sources.json），输出与上游 feed 同构的 JSON。
// 目的：在不修改上游、不依赖 X API 的前提下，增加播客与博客转载源。
//
// 背景：
//   - 上游 prepare-digest.js 从 GitHub 取预生成 feed，本地名单改了不起作用（C 方案）
//   - pod2txt 转写服务从本机不可达，故本文用 RSS <description>（1700-3000字）替代 transcript
//   - 输出结构对齐上游 feed-podcasts.json / feed-blogs.json，供 digest 直接消费
//
// 用法：
//   node local-supplement.js            # 输出 JSON 到 stdout
//   node local-supplement.js --write    # 同时写入 _local-feeds/ 便于检查
//
// 输出：
//   {
//     generatedAt, lookbackHours,
//     podcasts: [{name, title, url, publishedAt, description, source}],
//     blogs:    [{name, title, url, publishedAt, content, source}],
//     stats: {...}
//   }
// ============================================================================

import { readFile, writeFile, mkdir } from 'fs/promises';
import { existsSync } from 'fs';
import { join } from 'path';

const SCRIPT_DIR = decodeURIComponent(new URL('.', import.meta.url).pathname);
const CONFIG_PATH = join(SCRIPT_DIR, '..', 'config', 'local-sources.json');
const OUT_DIR = join(SCRIPT_DIR, '..', '_local-feeds');
const STATE_PATH = join(OUT_DIR, 'state.json');

const UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36';
const MAX_PER_SOURCE = 2;

// -- helpers -----------------------------------------------------------------

function stripHtml(s) {
  return String(s || '')
    .replace(/<script[\s\S]*?<\/script>/gi, '')
    .replace(/<style[\s\S]*?<\/style>/gi, '')
    .replace(/<!\[CDATA\[|\]\]>/g, '')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
    .replace(/&#39;|&apos;/g, "'").replace(/&quot;/g, '"')
    .replace(/\s+/g, ' ')
    .trim();
}

function unescapeXml(s) {
  return String(s || '').replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, '$1')
    .replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"').replace(/&#39;|&apos;/g, "'");
}

async function fetchText(url) {
  const res = await fetch(url, { headers: { 'User-Agent': UA } });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.text();
}

// -- RSS 解析（播客）-----------------------------------------------------------

function parseRssItems(xml) {
  const items = [];
  const re = /<item>([\s\S]*?)<\/item>/gi;
  let m;
  while ((m = re.exec(xml)) !== null) {
    const b = m[1];
    const pick = (tag) => {
      const t = b.match(new RegExp(`<${tag}[^>]*>([\\s\\S]*?)</${tag}>`, 'i'));
      return t ? unescapeXml(t[1]).trim() : null;
    };
    const encl = (b.match(/<enclosure[^>]*url="([^"]+)"/i) || [])[1] || null;
    const title = stripHtml(pick('title') || 'Untitled');
    const desc = stripHtml(pick('description') || pick('summary') || '');
    const link = pick('link') || encl;
    const pub = pick('pubDate') || pick('published') || null;
    const guid = pick('guid') || link || title;
    if (title) items.push({ title, description: desc, url: link, publishedAt: pub ? new Date(pub).toISOString() : null, guid });
  }
  return items;
}

// -- 播客抓取 ------------------------------------------------------------------

async function fetchPodcasts(sources, lookbackHours, state, errors) {
  const cutoff = Date.now() - lookbackHours * 3600 * 1000;
  const out = [];
  for (const p of sources.podcasts || []) {
    try {
      const xml = await fetchText(p.rssUrl);
      const items = parseRssItems(xml).filter(it => {
        if (!it.publishedAt) return true;
        return new Date(it.publishedAt).getTime() >= cutoff;
      });
      let picked = 0;
      for (const it of items) {
        if (picked >= MAX_PER_SOURCE) break;
        if (state.seenPodcasts?.includes(it.guid)) continue;
        out.push({
          name: p.name,
          title: it.title,
          url: it.url || p.url,
          publishedAt: it.publishedAt,
          description: it.description,   // RSS 描述替代 transcript
          source: 'podcast-local',
          guid: it.guid
        });
        picked++;
      }
      console.error(`  ${p.name}: ${items.length} 集在窗口内，取 ${picked}`);
    } catch (e) {
      errors.push(`Local podcast ${p.name}: ${e.message}`);
      console.error(`  ${p.name}: ERR ${e.message}`);
    }
  }
  return out;
}

// -- 博客抓取（通用：从 index 页提取文章链接）-----------------------------------

function extractArticleLinks(html, base) {
  const links = new Set();
  const re = /href="([^"]+)"/gi;
  let m;
  while ((m = re.exec(html)) !== null) {
    let href = m[1];
    if (href.startsWith('/')) href = new URL(href, base).href;
    if (!href.startsWith('http')) continue;
    // 排除 RSS/json/api 等非文章链接
    if (/\.(xml|json|css|js|png|jpg|svg|webp)$/i.test(href)) continue;
    if (/(\/feed\/?$|wp-json|\/rss|\?|#)/i.test(href)) continue;
    links.add(href.split('#')[0]);
  }
  return [...links];
}

// 博客：RSS 优先；无 RSS 的走 HTML 抓取
async function fetchBlogs(sources, lookbackHours, state, errors) {
  const cutoff = Date.now() - lookbackHours * 3600 * 1000;
  const out = [];
  for (const b of sources.blogs || []) {
    try {
      // 路线 A：RSS
      if (b.rssUrl && b.kind !== 'scrape') {
        const xml = await fetchText(b.rssUrl);
        const items = parseRssItems(xml).filter(it => {
          if (!it.publishedAt) return true;
          return new Date(it.publishedAt).getTime() >= cutoff;
        });
        let picked = 0;
        for (const it of items) {
          if (picked >= MAX_PER_SOURCE) break;
          if (state.seenBlogs?.includes(it.url)) continue;
          out.push({
            name: b.name, title: it.title, url: it.url,
            publishedAt: it.publishedAt, content: it.description,
            source: 'blog-local', guid: it.guid
          });
          picked++;
        }
        console.error(`  ${b.name}(RSS): ${items.length} 篇在窗口内，取 ${picked}`);
        continue;
      }

      // 路线 B：HTML 抓取（无 RSS 的站）
      const html = await fetchText(b.indexUrl);
      const base = new URL(b.indexUrl).origin;
      const links = extractArticleLinks(html, b.indexUrl)
        .filter(u => {
          if (u === b.indexUrl || u === b.indexUrl + '/' || u === base + '/' || u === base) return false;
          const tail = u.replace(base, '');
          return /\/(news|blog|research|discover)\/.+/.test(tail) && tail.split('/').filter(Boolean).length >= 2;
        });
      let picked = 0;
      for (const url of links.slice(0, 8)) {
        if (picked >= MAX_PER_SOURCE) break;
        if (state.seenBlogs?.includes(url)) continue;
        try {
          const art = await fetchText(url);
          const titleM = art.match(/<title[^>]*>([\s\S]*?)<\/title>/i);
          const title = stripHtml(titleM ? titleM[1] : url).split(/[|\\]/)[0].trim();
          const descM = art.match(/<meta[^>]+(?:name|property)="(?:description|og:description)"[^>]+content="([^"]*)"/i);
          const content = descM ? stripHtml(descM[1]) : '';
          if (!title) continue;
          out.push({ name: b.name, title, url, publishedAt: null, content, source: 'blog-local' });
          picked++;
        } catch { /* 单篇失败不阻断 */ }
      }
      console.error(`  ${b.name}(HTML): ${links.length} 链接，取 ${picked}`);
    } catch (e) {
      errors.push(`Local blog ${b.name}: ${e.message}`);
      console.error(`  ${b.name}: ERR ${e.message}`);
    }
  }
  return out;
}

// -- main ---------------------------------------------------------------------

async function main() {
  const errors = [];
  let cfg;
  try {
    cfg = JSON.parse(await readFile(CONFIG_PATH, 'utf-8'));
  } catch (e) {
    console.log(JSON.stringify({ status: 'error', message: `读不到 local-sources.json: ${e.message}` }));
    process.exit(1);
  }

  await mkdir(OUT_DIR, { recursive: true }).catch(() => {});
  let state = { seenPodcasts: [], seenBlogs: [] };
  if (existsSync(STATE_PATH)) {
    try { state = JSON.parse(await readFile(STATE_PATH, 'utf-8')); } catch {}
  }

  const lb = cfg.lookbackHours || {};
  const podcasts = await fetchPodcasts(cfg, lb.podcasts || 336, state, errors);
  const blogs = await fetchBlogs(cfg, lb.blogs || 168, state, errors);

  const out = {
    generatedAt: new Date().toISOString(),
    source: 'local-supplement',
    podcasts,
    blogs,
    stats: { localPodcasts: podcasts.length, localBlogs: blogs.length },
    errors: errors.length ? errors : undefined
  };

  // 更新 state（防重复）
  for (const p of podcasts) if (p.guid && !state.seenPodcasts.includes(p.guid)) state.seenPodcasts.push(p.guid);
  for (const b of blogs) if (!state.seenBlogs.includes(b.url)) state.seenBlogs.push(b.url);
  state.seenPodcasts = state.seenPodcasts.slice(-500);
  state.seenBlogs = state.seenBlogs.slice(-500);
  await writeFile(STATE_PATH, JSON.stringify(state, null, 2)).catch(() => {});

  if (process.argv.includes('--write')) {
    await writeFile(join(OUT_DIR, 'local-feed.json'), JSON.stringify(out, null, 2));
    console.error(`已写入 ${join(OUT_DIR, 'local-feed.json')}`);
  }

  console.log(JSON.stringify(out, null, 2));
}

main().catch(e => {
  console.error(JSON.stringify({ status: 'error', message: e.message }));
  process.exit(1);
});
