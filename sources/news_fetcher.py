import feedparser
import requests
from datetime import datetime, timedelta
from typing import List, Dict
import yaml
import re
import time
import os
import hashlib


def _get_config_path(config_path: str = "config.yaml") -> str:
    if os.path.isabs(config_path):
        return config_path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, config_path)


class NewsFetcher:
    def __init__(self, config_path: str = "config.yaml"):
        with open(_get_config_path(config_path), "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        news_config = config["news"]
        self.rss_sources = news_config.get("rss_sources", [])
        self.use_hackernews = news_config.get("hackernews", False)
        self.search_keywords = [
            kw.lower() for kw in news_config.get("search_keywords", [])
        ]
        self.max_news = news_config.get("max_news", 8)

        quality_filter = news_config.get("quality_filter", {})
        self.high_value_keywords = [
            kw.lower() for kw in quality_filter.get("high_value_keywords", [])
        ]
        self.low_value_keywords = [
            kw.lower() for kw in quality_filter.get("low_value_keywords", [])
        ]

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/rss+xml,application/xml;q=0.9,*/*;q=0.8",
        }

    def _is_ai_related(self, title: str, summary: str = "") -> bool:
        text = (title + " " + summary).lower()
        for keyword in self.search_keywords:
            if keyword in text:
                return True
        return False

    def _calculate_quality_score(self, title: str, summary: str = "") -> int:
        text = (title + " " + summary).lower()
        score = 0

        for kw in self.low_value_keywords:
            if kw in text:
                score -= 50

        for kw in self.high_value_keywords:
            if kw in text:
                score += 10

        tech_patterns = [r"\d+b", r"\d+x", r"sota", r"新架构", r"新算法", r"突破"]
        for pattern in tech_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                score += 15

        return score

    def _clean_html(self, text: str) -> str:
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _get_content_hash(self, title: str) -> str:
        return hashlib.md5(title.encode()).hexdigest()[:8]

    def _fetch_from_rss(self, source: Dict) -> List[Dict]:
        news_list = []

        try:
            response = requests.get(source["rss_url"], headers=self.headers, timeout=15)
            feed = feedparser.parse(response.content)

            cutoff_date = datetime.now() - timedelta(days=2)

            for entry in feed.entries[:30]:
                try:
                    published = None
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        published = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                        published = datetime(*entry.updated_parsed[:6])

                    if published and published < cutoff_date:
                        continue

                    title = str(entry.get("title", "") or "")
                    summary = str(
                        entry.get("summary", entry.get("description", "")) or ""
                    )
                    summary = self._clean_html(summary)

                    if not self._is_ai_related(title, summary):
                        continue

                    quality_score = self._calculate_quality_score(title, summary)
                    if quality_score < -30:
                        continue

                    link = entry.get("link", "")
                    if not link:
                        continue

                    news_item = {
                        "title": title,
                        "summary": summary[:400] if len(summary) > 400 else summary,
                        "url": link,
                        "source": source["name"],
                        "source_type": source.get("type", "unknown"),
                        "published": published.strftime("%Y-%m-%d %H:%M")
                        if published
                        else datetime.now().strftime("%Y-%m-%d"),
                        "content_hash": self._get_content_hash(title),
                        "quality_score": quality_score,
                    }
                    news_list.append(news_item)

                except Exception:
                    continue

            print(f"  [{source['name']}] 获取到 {len(news_list)} 条")

        except Exception as e:
            print(f"  [{source['name']}] 抓取失败: {e}")

        return news_list

    def _fetch_from_hackernews(self) -> List[Dict]:
        news_list = []

        try:
            top_stories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            response = requests.get(top_stories_url, timeout=10)

            if response.status_code != 200:
                print(f"  [Hacker News] 请求失败: {response.status_code}")
                return news_list

            story_ids = response.json()[:30]

            cutoff_date = datetime.now() - timedelta(days=2)

            for story_id in story_ids:
                try:
                    story_url = (
                        f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                    )
                    story_response = requests.get(story_url, timeout=5)

                    if story_response.status_code != 200:
                        continue

                    story = story_response.json()

                    if not story:
                        continue

                    title = story.get("title", "")
                    story_time = datetime.fromtimestamp(story.get("time", 0))

                    if story_time < cutoff_date:
                        continue

                    if not self._is_ai_related(title, ""):
                        continue

                    score = story.get("score", 0)
                    if score < 100:
                        continue

                    url = story.get("url", "")
                    if not url:
                        url = f"https://news.ycombinator.com/item?id={story_id}"

                    news_item = {
                        "title": title,
                        "summary": f"Hacker News | 得分: {score}",
                        "url": url,
                        "source": "Hacker News",
                        "source_type": "hn",
                        "published": story_time.strftime("%Y-%m-%d"),
                        "content_hash": self._get_content_hash(title),
                        "quality_score": self._calculate_quality_score(title, "")
                        + min(score // 50, 20),
                    }
                    news_list.append(news_item)

                except Exception:
                    continue

            print(f"  [Hacker News] 获取到 {len(news_list)} 条")

        except Exception as e:
            print(f"  [Hacker News] 抓取失败: {e}")

        return news_list

    def fetch_news(self) -> List[Dict]:
        print("\n开始抓取新闻...")
        all_news = []

        for source in self.rss_sources:
            news = self._fetch_from_rss(source)
            all_news.extend(news)
            time.sleep(0.3)

        if self.use_hackernews:
            news = self._fetch_from_hackernews()
            all_news.extend(news)

        seen = set()
        unique_news = []
        for news in all_news:
            key = news.get("content_hash", "") + news["title"].lower()[:20]
            if key not in seen:
                seen.add(key)
                unique_news.append(news)

        unique_news.sort(key=lambda x: x.get("quality_score", 0), reverse=True)

        return unique_news[: self.max_news]


def fetch_ai_news(config_path: str = "config.yaml") -> List[Dict]:
    fetcher = NewsFetcher(config_path)
    return fetcher.fetch_news()


if __name__ == "__main__":
    news = fetch_ai_news()
    print(f"\n最终: {len(news)} 条")
    for i, item in enumerate(news, 1):
        print(f"{i}. [{item['source']}] {item['title'][:40]}...")
