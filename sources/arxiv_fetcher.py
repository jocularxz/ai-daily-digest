import arxiv
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import yaml
import re


def _get_config_path(config_path: str = "config.yaml") -> str:
    if os.path.isabs(config_path):
        return config_path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, config_path)


class ArxivFetcher:
    def __init__(self, config_path: str = "config.yaml"):
        with open(_get_config_path(config_path), "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        self.config = config["arxiv"]
        self.categories = self.config["categories"]
        self.keywords = [kw.lower() for kw in self.config["keywords"]]
        self.max_papers = self.config["max_papers"]
        self.days_back = self.config["days_back"]

    def _build_query(self) -> str:
        cat_query = " OR ".join([f"cat:{cat}" for cat in self.categories])
        return f"({cat_query})"

    def _matches_keywords(self, title: str, abstract: str) -> tuple[bool, List[str]]:
        text = (title + " " + abstract).lower()
        matched_keywords = []
        for keyword in self.keywords:
            if keyword.lower() in text:
                matched_keywords.append(keyword)
        return len(matched_keywords) > 0, matched_keywords

    def _calculate_relevance_score(
        self, paper: arxiv.Result, matched_keywords: List[str]
    ) -> int:
        score = len(matched_keywords) * 10
        title_lower = paper.title.lower()

        priority_keywords = [
            ("fine-tuning", 15),
            ("finetuning", 15),
            ("lora", 15),
            ("peft", 15),
            ("llm", 12),
            ("large language model", 12),
            ("gpt", 10),
            ("bert", 8),
            ("continual learning", 12),
            ("instruction tuning", 12),
            ("rlhf", 12),
            ("dpo", 12),
            ("moe", 10),
            ("mixture of experts", 10),
            ("multimodal", 10),
            ("vision language", 10),
            ("reasoning", 8),
            ("chain of thought", 10),
            ("quantization", 8),
            ("distillation", 8),
            ("transformer", 6),
            ("attention", 6),
        ]

        for kw, bonus in priority_keywords:
            if kw in title_lower:
                score += bonus

        return score

    def fetch_papers(self) -> List[Dict]:
        papers_with_scores = []

        query = self._build_query()

        try:
            search = arxiv.Search(
                query=query,
                max_results=self.max_papers * 3,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending,
            )

            cutoff_date = datetime.now() - timedelta(days=self.days_back)

            for result in search.results():
                if result.published.replace(tzinfo=None) < cutoff_date:
                    continue

                matches, matched_keywords = self._matches_keywords(
                    result.title, result.summary
                )

                if matches:
                    score = self._calculate_relevance_score(result, matched_keywords)

                    paper_data = {
                        "title": result.title,
                        "arxiv_id": result.entry_id.split("/")[-1],
                        "url": result.entry_id,
                        "pdf_url": result.pdf_url,
                        "authors": [author.name for author in result.authors[:3]],
                        "summary": result.summary.replace("\n", " ").strip(),
                        "published": result.published.strftime("%Y-%m-%d"),
                        "categories": result.categories,
                        "matched_keywords": matched_keywords,
                        "relevance_score": score,
                    }
                    papers_with_scores.append((paper_data, score))

        except Exception as e:
            print(f"Error fetching from arXiv: {e}")
            return []

        papers_with_scores.sort(key=lambda x: x[1], reverse=True)

        return [paper for paper, score in papers_with_scores[: self.max_papers]]


def fetch_arxiv_papers(config_path: str = "config.yaml") -> List[Dict]:
    fetcher = ArxivFetcher(config_path)
    return fetcher.fetch_papers()


if __name__ == "__main__":
    papers = fetch_arxiv_papers()
    print(f"Found {len(papers)} papers:")
    for i, paper in enumerate(papers, 1):
        print(f"\n{i}. {paper['title']}")
        print(f"   Keywords: {paper['matched_keywords']}")
        print(f"   Score: {paper['relevance_score']}")
