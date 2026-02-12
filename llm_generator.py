import os
import time
import yaml
import requests
from typing import List, Dict, Optional, Tuple
import dashscope
from dashscope import Generation

from knowledge_manager import KnowledgeManager
from sources.image_searcher import search_images_for_topic


class LLMGenerator:
    def __init__(self, config_path: str = "config.yaml"):
        if os.path.isabs(config_path):
            config_file = config_path
            self.project_dir = os.path.dirname(config_path)
        else:
            self.project_dir = os.path.dirname(os.path.abspath(__file__))
            config_file = os.path.join(self.project_dir, config_path)

        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        llm_config = config.get("llm", {})

        self.api_key = os.environ.get("DASHSCOPE_API_KEY") or llm_config.get(
            "api_key", ""
        )
        self.timeout = llm_config.get("timeout", 60)

        self.models = llm_config.get("models", [])
        self.models.sort(key=lambda x: x.get("priority", 999))

        dashscope.api_key = self.api_key

        self.prompts_dir = os.path.join(self.project_dir, "prompts")
        self.knowledge_manager = KnowledgeManager(config_file)

        content_config = config.get("content", {})
        self.image_search_enabled = content_config.get("image_search", {}).get(
            "enabled", False
        )

    def _load_prompt(self, prompt_name: str) -> str:
        prompt_path = os.path.join(self.prompts_dir, prompt_name)
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    def _call_with_format(
        self, model_name: str, prompt: str, use_message_format: bool
    ) -> tuple:
        try:
            if use_message_format:
                response = Generation.call(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2000,
                    temperature=0.7,
                    top_p=0.8,
                    result_format="message",
                )
                if response.status_code == 200:
                    return True, response.output.choices[0].message.content
            else:
                response = Generation.call(
                    model=model_name,
                    prompt=prompt,
                    max_tokens=2000,
                    temperature=0.7,
                    top_p=0.8,
                    result_format="text",
                )
                if response.status_code == 200:
                    return True, response.output.text

            error_code = getattr(response, "code", "unknown")
            error_msg = getattr(response, "message", str(response))
            return False, f"{error_code} - {error_msg}"
        except requests.exceptions.Timeout:
            return False, "请求超时"
        except requests.exceptions.ConnectionError:
            return False, "网络连接失败"
        except Exception as e:
            return False, str(e)[:100]

    def _call_qwen(self, prompt: str) -> str:
        if not self.api_key or self.api_key.startswith("YOUR_"):
            print("      错误: 请在config.yaml中配置api_key")
            return ""

        for i, model_config in enumerate(self.models):
            model_name = model_config.get("name", "qwen-plus")
            print(f"      尝试模型 [{i + 1}/{len(self.models)}]: {model_name}")

            success, result = self._call_with_format(
                model_name, prompt, use_message_format=True
            )
            if success:
                print(f"      成功: {model_name}")
                return result

            print(f"        message格式失败: {result[:60]}")

            success, result = self._call_with_format(
                model_name, prompt, use_message_format=False
            )
            if success:
                print(f"      成功: {model_name}")
                return result

            print(f"        text格式失败: {result[:60]}")

            time.sleep(1)

        print("      所有模型均调用失败!")
        return ""

    def summarize_news(self, news_items: List[Dict]) -> str:
        if not news_items:
            return "暂无今日AI要闻"

        prompt_template = self._load_prompt("news_summary.txt")

        news_text = ""
        for i, item in enumerate(news_items, 1):
            news_text += f"\n{i}. [{item.get('source', '未知来源')}]\n"
            news_text += f"   标题: {item.get('title', '')}\n"
            news_text += f"   摘要: {item.get('summary', '')[:200]}\n"

        prompt = prompt_template.format(news_items=news_text)
        return self._call_qwen(prompt)

    def analyze_paper(self, paper: Dict) -> str:
        prompt_template = self._load_prompt("paper_analysis.txt")

        prompt = prompt_template.format(
            title=paper.get("title", ""),
            authors=", ".join(paper.get("authors", [])),
            summary=paper.get("summary", ""),
            keywords=", ".join(paper.get("matched_keywords", [])),
        )

        return self._call_qwen(prompt)

    def analyze_papers(self, papers: List[Dict], max_papers: int = 2) -> List[Dict]:
        results = []

        for paper in papers[:max_papers]:
            analysis = self.analyze_paper(paper)
            results.append({"paper_info": paper, "analysis": analysis})

        return results

    def get_random_topic(self) -> str:
        result = self.knowledge_manager.get_topic_with_category()
        return result["topic"]

    def get_topic_with_category(self) -> Dict:
        return self.knowledge_manager.get_topic_with_category()

    def explain_knowledge(self, topic: Optional[str] = None) -> str:
        if topic is None:
            topic = self.get_random_topic()

        prompt_template = self._load_prompt("knowledge_explain.txt")
        prompt = prompt_template.format(topic=topic)

        return self._call_qwen(prompt)

    def explain_knowledge_with_images(
        self, topic: Optional[str] = None
    ) -> Tuple[str, List[str]]:
        if topic is None:
            topic = self.get_random_topic()

        prompt_template = self._load_prompt("knowledge_explain.txt")
        prompt = prompt_template.format(topic=topic)

        explanation = self._call_qwen(prompt)

        images = []
        if self.image_search_enabled:
            print("      - 搜索相关图片...")
            images = search_images_for_topic(topic)
            print(f"        找到 {len(images)} 张图片")

        return explanation, images

    def get_knowledge_stats(self) -> Dict:
        return self.knowledge_manager.get_history_stats()


def create_generator(config_path: str = "config.yaml") -> LLMGenerator:
    return LLMGenerator(config_path)


if __name__ == "__main__":
    generator = LLMGenerator()

    stats = generator.get_knowledge_stats()
    print(f"知识点库: 剩余 {stats['remaining_topics']}/{stats['total_topics']}")
    print(f"可用模型: {[m.get('name') for m in generator.models]}")
