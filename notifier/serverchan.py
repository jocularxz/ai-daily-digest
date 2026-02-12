import requests
import yaml
import os
from typing import Optional


def _get_config_path(config_path: str = "config.yaml") -> str:
    if os.path.isabs(config_path):
        return config_path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, config_path)


class ServerChanNotifier:
    def __init__(self, config_path: str = "config.yaml"):
        with open(_get_config_path(config_path), "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        self.sendkey = (
            os.environ.get("SERVERCHAN_SENDKEY")
            or config["notifier"]["serverchan"]["sendkey"]
        )
        self.api_url = f"https://sctapi.ftqq.com/{self.sendkey}.send"

    def send(self, title: str, content: str) -> bool:
        if not self.sendkey or self.sendkey == "YOUR_SENDKEY":
            print("错误: 请先在config.yaml中配置Server酱的sendkey")
            return False

        try:
            response = requests.post(
                self.api_url, data={"title": title, "desp": content}, timeout=10
            )

            result = response.json()

            if response.status_code == 200 and result.get("code") == 0:
                print("推送成功!")
                return True
            else:
                print(f"推送失败: {result.get('message', '未知错误')}")
                return False

        except Exception as e:
            print(f"推送异常: {e}")
            return False

    def send_daily_digest(
        self,
        date_str: str,
        news_summary: str,
        papers: list,
        knowledge: str,
        topic: str,
        images: list = None,
    ) -> bool:
        title = f"AI每日速递 | {date_str}"

        content = self._format_markdown(
            date_str, news_summary, papers, knowledge, topic, images or []
        )

        return self.send(title, content)

    def _format_markdown(
        self,
        date_str: str,
        news_summary: str,
        papers: list,
        knowledge: str,
        topic: str,
        images: list = None,
    ) -> str:
        md = f"# AI每日速递 | {date_str}\n\n"

        md += "## 📰 今日要闻\n"
        md += "---\n"
        md += f"{news_summary}\n\n"

        md += "## 📚 论文精选\n"
        md += "---\n"

        if papers:
            for i, paper_data in enumerate(papers, 1):
                paper = paper_data.get("paper_info", {})
                analysis = paper_data.get("analysis", "")

                md += f"### 论文 {i}: {paper.get('title', '未知标题')}\n\n"
                md += f"- **arXiv**: [{paper.get('arxiv_id', '')}]({paper.get('url', '')})\n"
                md += f"- **作者**: {', '.join(paper.get('authors', []))}\n"
                md += f"- **发布日期**: {paper.get('published', '')}\n\n"
                md += f"{analysis}\n\n"
                md += "---\n\n"
        else:
            md += "暂无今日论文精选\n\n"

        md += f"## 💡 今日知识点: {topic}\n"
        md += "---\n"

        if images:
            md += "### 📷 可能的参考图片\n\n"
            for i, img_url in enumerate(images[:2], 1):
                md += f"![示意图{i}]({img_url})\n\n"
            md += "---\n\n"

        md += f"{knowledge}\n\n"

        md += "---\n"
        md += "*由 AI每日速递 自动生成*\n"

        return md


def create_notifier(config_path: str = "config.yaml") -> ServerChanNotifier:
    return ServerChanNotifier(config_path)


if __name__ == "__main__":
    notifier = ServerChanNotifier()
    notifier.send("测试推送", "这是一条测试消息")
