import json
import os
import random
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import yaml


class KnowledgeManager:
    def __init__(self, config_path: str = "config.yaml"):
        if os.path.isabs(config_path):
            self.config_path = config_path
            self.config_dir = os.path.dirname(config_path)
        else:
            self.config_dir = os.path.dirname(os.path.abspath(__file__))
            self.config_path = os.path.join(self.config_dir, config_path)

        with open(self.config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        self.knowledge_config = config.get("knowledge", {})
        self.categories = self.knowledge_config.get("categories", {})
        self.max_history_days = self.knowledge_config.get("max_history_days", 60)

        self.data_dir = os.path.join(self.config_dir, "data")
        os.makedirs(self.data_dir, exist_ok=True)

        self.history_file = os.path.join(self.data_dir, "knowledge_history.json")
        self.history = self._load_history()

    def _load_history(self) -> Dict:
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_history(self):
        self._cleanup_old_history()
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)

    def _cleanup_old_history(self):
        cutoff_date = (datetime.now() - timedelta(days=self.max_history_days)).strftime(
            "%Y-%m-%d"
        )

        topics_to_remove = []
        for topic, date in self.history.items():
            if date < cutoff_date:
                topics_to_remove.append(topic)

        for topic in topics_to_remove:
            del self.history[topic]

    def _get_all_topics(self) -> List[tuple]:
        all_topics = []
        for category, topics in self.categories.items():
            for topic in topics:
                all_topics.append((category, topic))
        return all_topics

    def _get_available_topics(self) -> List[tuple]:
        all_topics = self._get_all_topics()
        available = []

        for category, topic in all_topics:
            if topic not in self.history:
                available.append((category, topic))

        return available

    def select_topic(self) -> tuple:
        available = self._get_available_topics()

        if not available:
            self.history.clear()
            self._save_history()
            available = self._get_all_topics()

        today_str = datetime.now().strftime("%Y-%m-%d")

        category_weights = {}
        for category, topic in available:
            category_topics = [t for c, t in available if c == category]
            category_weights[category] = len(category_topics)

        categories = list(category_weights.keys())
        weights = [category_weights[c] for c in categories]
        selected_category = random.choices(categories, weights=weights, k=1)[0]

        category_topics = [t for c, t in available if c == selected_category]
        selected_topic = random.choice(category_topics)

        self.history[selected_topic] = today_str
        self._save_history()

        return selected_category, selected_topic

    def get_random_topic(self) -> str:
        category, topic = self.select_topic()
        return topic

    def get_topic_with_category(self) -> Dict:
        category, topic = self.select_topic()
        return {"category": category, "topic": topic}

    def get_history_stats(self) -> Dict:
        all_topics = self._get_all_topics()
        total = len(all_topics)
        used = len(self.history)

        return {
            "total_topics": total,
            "used_topics": used,
            "remaining_topics": total - used,
            "categories": {cat: len(topics) for cat, topics in self.categories.items()},
        }


def create_knowledge_manager(config_path: str = "config.yaml") -> KnowledgeManager:
    return KnowledgeManager(config_path)


if __name__ == "__main__":
    manager = KnowledgeManager()

    print("知识点统计:")
    stats = manager.get_history_stats()
    print(f"  总主题数: {stats['total_topics']}")
    print(f"  已使用: {stats['used_topics']}")
    print(f"  剩余: {stats['remaining_topics']}")
    print(f"\n各分类主题数:")
    for cat, count in stats["categories"].items():
        print(f"  {cat}: {count}")

    print("\n\n今日选题:")
    result = manager.get_topic_with_category()
    print(f"  分类: {result['category']}")
    print(f"  主题: {result['topic']}")
