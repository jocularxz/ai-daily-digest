import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from sources.arxiv_fetcher import fetch_arxiv_papers
from sources.news_fetcher import fetch_ai_news
from llm_generator import LLMGenerator
from notifier.serverchan import ServerChanNotifier
import yaml


def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    print("=" * 60)
    print(f"  AI每日速递 - 开始运行 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    config = load_config()
    date_str = datetime.now().strftime("%Y-%m-%d")

    print("\n[1/5] 抓取AI新闻...")
    try:
        news = fetch_ai_news()
        print(f"      获取到 {len(news)} 条新闻")
    except Exception as e:
        print(f"      新闻抓取失败: {e}")
        news = []

    print("\n[2/5] 抓取arXiv论文...")
    try:
        papers = fetch_arxiv_papers()
        print(f"      获取到 {len(papers)} 篇论文")
    except Exception as e:
        print(f"      论文抓取失败: {e}")
        papers = []

    print("\n[3/5] 生成内容摘要...")
    generator = LLMGenerator()

    stats = generator.get_knowledge_stats()
    print(
        f"      知识点库: 剩余 {stats['remaining_topics']}/{stats['total_topics']} 个主题未使用"
    )

    print("      - 生成新闻摘要...")
    news_summary = generator.summarize_news(news) if news else "暂无今日AI要闻"

    print("      - 分析论文...")
    paper_count = config.get("content", {}).get("paper_count", 2)
    analyzed_papers = generator.analyze_papers(papers, max_papers=paper_count)

    print("      - 选择今日知识点...")
    topic_info = generator.get_topic_with_category()
    topic = topic_info["topic"]
    category = topic_info["category"]
    print(f"        分类: {category}")
    print(f"        主题: {topic}")

    print("      - 生成知识点解释...")
    knowledge, images = generator.explain_knowledge_with_images(topic)

    print("\n[4/5] 推送到微信...")
    notifier = ServerChanNotifier()
    success = notifier.send_daily_digest(
        date_str=date_str,
        news_summary=news_summary,
        papers=analyzed_papers,
        knowledge=knowledge,
        topic=f"[{category}] {topic}",
        images=images,
    )

    print("\n[5/5] 完成!")
    if success:
        print("      推送成功,请查收微信消息")
    else:
        print("      推送失败,请检查config.yaml中的sendkey配置")

    print("=" * 60)
    return success


if __name__ == "__main__":
    main()
