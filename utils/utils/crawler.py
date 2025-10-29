# utils/crawler.py

import logging, random, time
from typing import List, Dict, Optional
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

from utils.config import DEFAULT_TIMEOUT, DEFAULT_UA

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

# -------- 通用抓取 --------
def _session(base_headers: Optional[Dict] = None) -> requests.Session:
    s = requests.Session()
    headers = {"User-Agent": DEFAULT_UA, "Accept": "text/html,application/json"}
    if base_headers:
        headers.update(base_headers)
    s.headers.update(headers)
    return s

def fetch_page(url: str, timeout: int = DEFAULT_TIMEOUT) -> Optional[str]:
    try:
        sess = _session()
        resp = sess.get(url, timeout=timeout)
        logging.info(f"GET {url} -> {resp.status_code}")
        if resp.status_code == 200:
            return resp.text
    except Exception as e:
        logging.warning(f"fetch_page error: {url} - {e}")
    return None

def extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator=" ", strip=True)

def crawl_keyword_from_sources(
    sources: List[str], keyword: str, max_pages: int
) -> List[Dict]:
    """
    对每个源尝试分页 (?page=N) 获取页面主文本文本，做关键词粗检。
    （不同站点分页规则不一，后续可为每站写专属 parser）
    """
    out: List[Dict] = []
    kw = keyword.lower()

    for base in sources:
        for page in range(1, max_pages + 1):
            url = base if page == 1 else f"{base}?page={page}"
            html = fetch_page(url)
            if not html:
                break
            text = extract_text(html)
            if kw in text.lower():
                out.append({"source": url, "text": text})
            # 随机延时，降低封禁概率
            time.sleep(0.8 + random.random() * 1.2)
    return out

# -------- Reddit 抓取（JSON 端点 & 可选 OAuth）--------
class RedditCrawler:
    """
    轻量：使用 /search.json 与 /comments/{id}.json
    如需更高配额/稳定性，可接入 OAuth（client_id/secret/user_agent）。
    """

    def __init__(
        self,
        user_agent: str,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        rate_sleep: float = 2.0,
    ):
        self.rate_sleep = rate_sleep
        self.s = _session({"User-Agent": user_agent})
        self.client_id = client_id
        self.client_secret = client_secret  # 这里保留字段，后续可扩展 OAuth

    def _pause(self):
        t = self.rate_sleep + random.random()
        time.sleep(t)

    def search(self, keyword: str, limit: int = 50) -> List[Dict]:
        """
        通过 /search.json 搜索帖子（匿名 JSON 端点）
        """
        base = "https://www.reddit.com/search.json"
        params = {"q": keyword, "limit": min(limit, 100), "sort": "relevance", "t": "all"}
        url = f"{base}?{urlencode(params)}"
        try:
            self._pause()
            r = self.s.get(url, timeout=DEFAULT_TIMEOUT)
            if r.status_code == 200:
                data = r.json().get("data", {}).get("children", [])
                return [it.get("data", {}) for it in data]
            logging.warning(f"Reddit search {r.status_code}")
        except Exception as e:
            logging.warning(f"Reddit search err: {e}")
        return []

    def comments(self, post_fullname: str, limit: int = 50) -> List[Dict]:
        """
        获取帖子评论；post_fullname 形如 t3_xxxxx
        """
        post_id = post_fullname[3:]
        url = f"https://www.reddit.com/comments/{post_id}.json?{urlencode({'limit':limit})}"
        try:
            self._pause()
            r = self.s.get(url, timeout=DEFAULT_TIMEOUT)
            if r.status_code == 200 and isinstance(r.json(), list) and len(r.json()) > 1:
                children = r.json()[1].get("data", {}).get("children", [])
                return [c.get("data", {}) for c in children]
        except Exception as e:
            logging.warning(f"Reddit comments err: {e}")
        return []
