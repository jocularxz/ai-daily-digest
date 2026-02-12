import requests
import urllib.parse
import re
from typing import List


class ImageSearcher:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

    def search_baidu_images(self, keyword: str, max_images: int = 2) -> List[str]:
        images = []
        try:
            encoded_keyword = urllib.parse.quote(keyword)
            search_url = f"https://image.baidu.com/search/acjson?tn=resultjson_com&word={encoded_keyword}&rn={max_images * 3}"
            response = requests.get(search_url, headers=self.headers, timeout=20)

            print(f"          百度HTTP状态: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                items = data.get("data", [])
                print(f"          百度返回 {len(items)} 条数据")

                dict_count = 0
                url_found = 0

                for i, item in enumerate(items):
                    if not isinstance(item, dict):
                        print(f"          百度item[{i}]类型: {type(item)}")
                        continue
                    dict_count += 1
                    for key in ["thumbURL", "objURL", "middleURL", "hoverURL"]:
                        url = item.get(key)
                        if url:
                            print(f"          百度item[{i}].{key} = {str(url)[:50]}...")
                            if url.startswith("http"):
                                images.append(url)
                                url_found += 1
                                break

                    if len(images) >= max_images:
                        break

                print(f"          百度: {dict_count}个dict, {url_found}个有效URL")

                if images:
                    print(f"          百度成功: {len(images)}张")
                else:
                    print(f"          百度: 无匹配图片")
            else:
                print(f"          百度失败: HTTP {response.status_code}")
        except Exception as e:
            print(f"          百度失败: {type(e).__name__}: {str(e)[:80]}")
        return images

    def search_google_images(self, keyword: str, max_images: int = 2) -> List[str]:
        images = []
        try:
            encoded_keyword = urllib.parse.quote(keyword)
            search_url = (
                f"https://www.google.com/search?q={encoded_keyword}&tbm=isch&hl=en"
            )

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html",
            }

            response = requests.get(search_url, headers=headers, timeout=30)
            print(
                f"          Google HTTP状态: {response.status_code}, 响应长度: {len(response.text)}"
            )

            if response.status_code == 200:
                html = response.text

                patterns = [
                    r'"ou"\s*:\s*"([^"]+)"',
                    r'"imageUrl"\s*:\s*"([^"]+)"',
                    r'data-src\s*=\s*"([^"]+)"',
                ]

                all_urls = []
                for pattern in patterns:
                    matches = re.findall(pattern, html, re.IGNORECASE)
                    if matches:
                        all_urls.extend(matches)

                print(f"          Google找到 {len(all_urls)} 个URL")

                for url in all_urls[:20]:
                    url = (
                        url.replace("\\u003d", "=")
                        .replace("\\u0026", "&")
                        .replace("\\/", "/")
                    )
                    if url.startswith("http"):
                        skip_words = [
                            "favicon",
                            "logo",
                            "icon",
                            "gstatic",
                            "google.com/images",
                        ]
                        if not any(word in url.lower() for word in skip_words):
                            images.append(url)
                            print(f"          Google图片URL: {url[:80]}...")
                            if len(images) >= max_images:
                                break

                if images:
                    print(f"          Google成功: {len(images)}张")
                else:
                    print(f"          Google: 无匹配图片")
            else:
                print(f"          Google失败: HTTP {response.status_code}")
        except Exception as e:
            print(f"          Google失败: {type(e).__name__}: {str(e)[:80]}")
        return images

    def search_wikipedia_images(self, topic: str, max_images: int = 2) -> List[str]:
        images = []

        try:
            encoded_term = urllib.parse.quote(f"{topic} diagram")
            search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={encoded_term}&srnamespace=6&srlimit=15&format=json&origin=*"

            response = requests.get(search_url, headers=self.headers, timeout=30)
            print(f"          Wikipedia HTTP状态: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                search_results = data.get("query", {}).get("search", [])
                print(f"          Wikipedia返回 {len(search_results)} 条结果")

                keywords = [
                    "diagram",
                    "architecture",
                    "structure",
                    "flowchart",
                    "figure",
                    "scheme",
                ]

                for result in search_results:
                    title = result.get("title", "")
                    title_lower = title.lower()

                    if not any(kw in title_lower for kw in keywords):
                        continue

                    if "File:" in title:
                        file_title = title.replace("File:", "")
                        image_url = self._get_image_url("en.wikipedia.org", file_title)
                        if image_url:
                            images.append(image_url)
                            print(f"          Wikipedia图片URL: {image_url[:80]}...")
                        if len(images) >= max_images:
                            break

            if images:
                print(f"          Wikipedia成功: {len(images)}张")
        except Exception as e:
            print(f"          Wikipedia失败: {type(e).__name__}: {str(e)[:80]}")
        return images

    def search_wikimedia_commons(self, topic: str, max_images: int = 2) -> List[str]:
        images = []

        try:
            encoded_term = urllib.parse.quote(f"{topic} diagram")
            search_url = f"https://commons.wikimedia.org/w/api.php?action=query&list=search&srsearch={encoded_term}&srnamespace=6&srlimit=15&format=json&origin=*"

            response = requests.get(search_url, headers=self.headers, timeout=30)
            print(f"          Wikimedia HTTP状态: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                search_results = data.get("query", {}).get("search", [])
                print(f"          Wikimedia返回 {len(search_results)} 条结果")

                for result in search_results[:10]:
                    title = result.get("title", "")
                    if "File:" in title:
                        file_title = title.replace("File:", "")
                        image_url = self._get_image_url(
                            "commons.wikimedia.org", file_title
                        )
                        if image_url:
                            images.append(image_url)
                            print(f"          Wikimedia图片URL: {image_url[:80]}...")
                        if len(images) >= max_images:
                            break

            if images:
                print(f"          Wikimedia成功: {len(images)}张")
        except Exception as e:
            print(f"          Wikimedia失败: {type(e).__name__}: {str(e)[:80]}")
        return images

    def _get_image_url(self, domain: str, filename: str) -> str:
        try:
            encoded_filename = urllib.parse.quote(filename)
            url = f"https://{domain}/w/api.php?action=query&titles=File:{encoded_filename}&prop=imageinfo&iiprop=url&format=json&origin=*"
            response = requests.get(url, headers=self.headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                pages = data.get("query", {}).get("pages", {})
                for page_id, page_info in pages.items():
                    image_info = page_info.get("imageinfo", [])
                    if image_info:
                        return image_info[0].get("url", "")
        except Exception:
            pass
        return ""

    def search_concept_images(self, topic: str) -> List[str]:
        print(f"        搜索图片: {topic}")

        print("        [1/4] 尝试百度图片...")
        images = self.search_baidu_images(f"{topic} 架构图", max_images=2)
        if images:
            return images

        print("        [2/4] 尝试Google图片...")
        images = self.search_google_images(
            f"{topic} architecture diagram", max_images=2
        )
        if images:
            return images

        print("        [3/4] 尝试Wikipedia...")
        images = self.search_wikipedia_images(topic, max_images=2)
        if images:
            return images

        print("        [4/4] 尝试Wikimedia Commons...")
        images = self.search_wikimedia_commons(topic, max_images=2)
        if images:
            return images

        print("        未找到图片")
        return []


def search_images_for_topic(topic: str) -> List[str]:
    searcher = ImageSearcher()
    return searcher.search_concept_images(topic)
