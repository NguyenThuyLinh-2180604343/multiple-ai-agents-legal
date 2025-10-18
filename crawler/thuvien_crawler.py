# ================================
# File: crawler/thuvien_crawler.py
# ================================
import requests
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime
import sys
import os
from urllib.parse import quote_plus

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from ai_agents import BaseAgent

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Warning: Playwright not installed. Install with: pip install playwright")



class ThuvienCrawlerAgent(BaseAgent):
    def __init__(self):
        super().__init__("Crawler Agent")
        self.session = requests.Session()
        self.session.headers.update(Config.HEADERS)
        self.crawled_documents = []
        self.request_count = 0
        self.last_restart_time = time.time()

    def process(self, search_params=None):
        """Crawl văn bản từ thuvienphapluat.vn - YÊU CẦU 1

        search_params (dict, optional):
            - keyword: từ khóa tìm kiếm (mặc định "giao thông")
            - max_pages: số trang tối đa để crawl (mặc định 5)
            - docs_per_page: số văn bản mỗi trang (mặc định 20)
            - max_docs: tổng số văn bản tối đa (mặc định Config.MAX_DOCUMENTS)
            - use_simple_crawl: sử dụng simple crawl method (mặc định True)
            - headless: chạy Playwright headless (mặc định True)
        """
        self.start_timer()
        self.log("Bắt đầu crawl dữ liệu từ thuvienphapluat.vn")

        # Defaults
        keyword = (search_params or {}).get("keyword", "giao thông")
        max_pages = int((search_params or {}).get("max_pages", 5))
        docs_per_page = int((search_params or {}).get("docs_per_page", 20))
        max_docs = int((search_params or {}).get("max_docs", Config.MAX_DOCUMENTS))
        headless = bool((search_params or {}).get("headless", True))

        # Back-compat: mode ưu tiên, nếu không có thì suy ra từ use_simple_crawl (mặc định 'hybrid')
        mode = (search_params or {}).get("mode")
        if not mode:
            use_simple_crawl = (search_params or {}).get("use_simple_crawl")
            if use_simple_crawl is None:
                mode = "hybrid"
            else:
                mode = "simple" if bool(use_simple_crawl) else "advanced"

        mode = mode.lower().strip()
        assert mode in {"simple", "advanced", "hybrid"}, "mode phải là simple|advanced|hybrid"

        self.log(f"Cấu hình crawl: {max_pages} trang, {docs_per_page} văn bản/trang, tối đa {max_docs} văn bản")
        self.log(f"Phương pháp: {mode.upper()}")

        try:
            # Test kết nối trước
            if not self._test_connection():
                self.log("Không thể kết nối đến website")
                return {"documents": [], "total_crawled": 0, "pages_crawled": 0}

            if mode == "simple":
                # Simple crawl
                self.crawled_documents = self.simple_crawl_search_results(
                    keyword=keyword,
                    max_pages=max_pages,
                    docs_per_page=docs_per_page
                )

            elif mode == "advanced":
                # Playwright: tìm URL rồi crawl chi tiết
                document_urls = self._find_document_urls_paginated(
                    keyword=keyword, 
                    max_pages=max_pages,
                    docs_per_page=docs_per_page,
                    max_docs=max_docs,
                    headless=headless
                )
                self.log(f"Tìm thấy {len(document_urls)} URL văn bản từ {max_pages} trang")
                for i, url in enumerate(document_urls):
                    if len(self.crawled_documents) >= max_docs:
                        break
                    self.log(f"Crawling {i+1}/{len(document_urls)}: {url}")
                    doc_data = self._crawl_document_detail(url)
                    if doc_data:
                        self.crawled_documents.append(doc_data)
                    time.sleep(Config.DELAY_BETWEEN_REQUESTS)

            else:  # mode == "hybrid"
                self.crawled_documents = self._hybrid_crawl(
                    keyword=keyword,
                    max_pages=max_pages,
                    docs_per_page=docs_per_page,
                    max_docs=max_docs,
                    headless=headless
                )


            # Giới hạn số lượng theo max_docs
            if len(self.crawled_documents) > max_docs:
                self.crawled_documents = self.crawled_documents[:max_docs]

            # Tính metrics theo yêu cầu
            self._calculate_metrics()

            self.results = {
                "documents": self.crawled_documents,
                "total_crawled": len(self.crawled_documents),
                "pages_crawled": max_pages,
                "docs_per_page": docs_per_page,
                "crawl_method": mode
            }

        except Exception as e:
            self.log(f"Lỗi trong quá trình crawl: {e}")
            self.results = {"documents": [], "total_crawled": 0, "pages_crawled": 0}

        self.end_timer()
        return self.results

    def _test_connection(self):
        """Test kết nối đến website"""
        try:
            response = self.session.get(Config.BASE_URL, timeout=10)
            return response.status_code == 200
        except Exception:
            return False

    def _restart_session_if_needed(self):
        """Restart session để tránh bị chặn"""
        current_time = time.time()
        
        # Restart session sau mỗi 50 requests hoặc 10 phút
        if (self.request_count >= 50 or 
            current_time - self.last_restart_time > 600):
            
            self.log("Restarting session để tránh bị chặn...")
            self.session.close()
            self.session = requests.Session()
            
            # Đổi User-Agent ngẫu nhiên
            user_agents = [
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
            ]
            import random
            headers = Config.HEADERS.copy()
            headers['User-Agent'] = random.choice(user_agents)
            self.session.headers.update(headers)
            
            self.request_count = 0
            self.last_restart_time = current_time
            
            # Delay sau khi restart
            time.sleep(5)

    def _make_request(self, url, timeout=30):
        """Thực hiện request với retry và session management"""
        self._restart_session_if_needed()
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.request_count += 1
                response = self.session.get(url, timeout=timeout)
                response.raise_for_status()
                return response
                
            except requests.exceptions.Timeout:
                self.log(f"Timeout khi request {url} (lần {attempt + 1})")
                if attempt < max_retries - 1:
                    time.sleep(5 * (attempt + 1))  # Tăng delay
                    
            except requests.exceptions.RequestException as e:
                self.log(f"Lỗi request {url} (lần {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(3 * (attempt + 1))
                    
        return None

    def simple_crawl_search_results(self, keyword, max_pages=2, docs_per_page=None):
        """
        Crawl đơn giản theo cách mới:
        1. Tìm div class="content-0" và "content-1"  
        2. Tìm link trong <p class="nqTitle">
        3. Crawl nội dung HTML trong <div class='content1'>
        """
        self.log(f"BẮT ĐẦU SIMPLE CRAWL: '{keyword}' - {max_pages} trang")
        
        all_documents = []
        
        for page in range(1, max_pages + 1):
            self.log(f"Crawling trang {page}/{max_pages}")
            
            # Tạo URL tìm kiếm
            encoded_keyword = quote_plus(keyword)
            search_url = f"https://thuvienphapluat.vn/page/tim-van-ban.aspx?keyword={encoded_keyword}&match=True&area=0&page={page}"
            
            # Lấy danh sách links từ trang tìm kiếm
            links = self._get_document_links_from_search_page(search_url)
            
            if not links:
                self.log(f"Không tìm thấy link nào ở trang {page}, dừng crawl")
                break
            
            # Giới hạn số văn bản mỗi trang nếu có
            if docs_per_page:
                links = links[:docs_per_page]
            
            self.log(f"Trang {page}: Tìm thấy {len(links)} links, bắt đầu crawl nội dung")
            
            # Crawl nội dung từng link
            for i, link in enumerate(links, 1):
                self.log(f"  [{i}/{len(links)}] Crawling: {link}")
                
                doc_data = self._simple_crawl_document_content(link)
                if doc_data:
                    all_documents.append(doc_data)
                
                # Delay giữa các văn bản
                time.sleep(Config.DELAY_BETWEEN_REQUESTS)
            
            # Delay giữa các trang
            time.sleep(Config.DELAY_BETWEEN_REQUESTS * 2)
        
        self.log(f"HOÀN THÀNH SIMPLE CRAWL: {len(all_documents)} văn bản từ {max_pages} trang")
        return all_documents

    def _get_document_links_from_search_page(self, search_url):
        """
        Bước 2 & 3: Tìm div class="content-0"/"content-1" và link trong <p class="nqTitle">
        """
        response = self._make_request(search_url)
        if not response:
            return []
        
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            links = []
            
            # Tìm div class="content-0" và "content-1"
            content_divs = soup.find_all('div', class_=['content-0', 'content-1'])
            self.log(f"  Tìm thấy {len(content_divs)} div content")
            
            for div in content_divs:
                # Tìm <p class="nqTitle"> trong mỗi div
                nq_title = div.find('p', class_='nqTitle')
                if nq_title:
                    # Tìm link trong nqTitle
                    link_tag = nq_title.find('a', href=True)
                    if link_tag:
                        href = link_tag['href']
                        # Chuyển thành URL đầy đủ
                        if not href.startswith('http'):
                            href = f"https://thuvienphapluat.vn{href}"
                        links.append(href)
            
            return links
            
        except Exception as e:
            self.log(f"Lỗi khi parse trang tìm kiếm: {e}")
            return []

    def _simple_crawl_document_content(self, doc_url):
        """
        Bước 4: Crawl nội dung HTML trong <div class='content1'>
        """
        response = self._make_request(doc_url)
        if not response:
            return None
        
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Tìm div class='content1'
            content_div = soup.find('div', class_='content1')
            
            if content_div:
                # Lấy nội dung HTML và text
                content_html = str(content_div)
                content_text = content_div.get_text(separator=' ', strip=True)
                
                # Trích xuất thêm metadata cơ bản
                title = self._simple_extract_title(soup)
                number = self._simple_extract_number(soup, content_text)
                field = self._simple_extract_field(soup, content_text)
                
                doc_data = {
                    'url': doc_url,
                    'crawl_time': datetime.now().isoformat(),
                    'title': title,
                    'number': number,
                    'field': field,
                    'content_html': content_html,
                    'content_text': content_text[:3000],  # Giới hạn 3000 ký tự
                    'content_length': len(content_text)
                }
                
                return doc_data
            else:
                self.log(f"  Không tìm thấy div class='content1' trong {doc_url}")
                return None
                
        except Exception as e:
            self.log(f"  Lỗi khi crawl {doc_url}: {e}")
            return None

    def _extract_title(self, soup):
        # 1) H1 hoặc tiêu đề chính
        for sel in ["h1", ".doc-title", "h1.title", "meta[property='og:title']"]:
            el = soup.select_one(sel)
            if el:
                txt = el.get("content", "").strip() if el.name == "meta" else el.get_text(strip=True)
                if txt and txt.lower() != "đăng nhập":
                    return txt

        # 2) Fallback: tìm dòng bắt đầu QUYẾT ĐỊNH/KẾ HOẠCH/THÔNG TƯ
        txt = soup.get_text("\n", strip=True)
        for rx in [r"(QUYẾT ĐỊNH[^\.:\n]+)", r"(KẾ HOẠCH[^\.:\n]+)", r"(THÔNG TƯ[^\.:\n]+)"]:
            m = re.search(rx, txt, flags=re.IGNORECASE)
            if m:
                return m.group(1).strip().title()

        return "Không xác định"

    def _simple_extract_number(self, soup, content_text):
        """Trích xuất số hiệu đơn giản"""
        # Tìm trong content trước với patterns cải tiến
        patterns = [
            # Số hiệu đầy đủ với cơ quan
            r"Số:\s*(\d{1,4}/\d{4}/[A-ZĐ\-]+(?:-[A-ZĐ]+)*)",
            r"Số:\s*(\d{1,4}/[A-ZĐ\-]+(?:-[A-ZĐ]+)*)",
            # Tìm trong nội dung
            r"(\d{1,4}/\d{4}/(?:QĐ|NĐ|TT|CV|KH|TB|QH|L)-[A-ZĐ]+)",
            r"(\d{1,4}/\d{4}/[A-ZĐ\-]+(?:-[A-ZĐ]+)*)",
            r"(\d{1,4}/[A-ZĐ\-]+(?:-[A-ZĐ]+)*)",
            # Fallback
            r"(\d+/\d+/[A-ZĐ\-]+)",
            r"Số\s+(\d+/[A-ZĐ\-]+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content_text)
            if match:
                number = match.group(1)
                # Kiểm tra độ dài và có chữ cái
                if len(number) > 5 and re.search(r'[A-ZĐ]', number):
                    return number
                    
        return "Không xác định"

    def _simple_extract_field(self, soup, content_text):
        """Trích xuất lĩnh vực đơn giản"""
        text_lower = content_text.lower()
        fields = {
            "giao thông": "Giao thông",
            "an toàn giao thông": "Giao thông - ATGT",
            "thuế": "Thuế",
            "tài chính": "Tài chính",
            "lao động": "Lao động",
        }
        for kw, name in fields.items():
            if kw in text_lower:
                return name
        return "Không xác định"
    # -----------------
    # HYBRID helpers
    # -----------------
    def _is_bad_doc(self, d: dict) -> bool:
        """Đánh dấu doc 'xấu': tiêu đề login, nội dung quá ngắn, thiếu content_html."""
        title = (d.get("title") or "").strip().lower()
        clen = int(d.get("content_length") or 0)
        if "đăng nhập" in title:
            return True
        if clen and clen < 500:
            return True
        if "content_html" in d and not d.get("content_html"):
            return True
        # nếu là kiểu _crawl_document_detail (content không phải content_text)
        content = d.get("content") or ""
        if content and len(content) < 500:
            return True
        return False

    def _needs_fallback(self, docs: list) -> bool:
        """Quyết định có cần fallback Playwright không."""
        if not docs:
            return True
        bad = sum(1 for d in docs if self._is_bad_doc(d))
        ratio = bad / max(1, len(docs))
        # nếu tỉ lệ doc xấu >= 40% thì fallback
        return ratio >= 0.4

    def _hybrid_crawl(self, keyword: str, max_pages: int, docs_per_page: int, max_docs: int, headless: bool):
        """Chạy simple trước → nếu chất lượng thấp thì fallback Playwright để tăng recall."""
        self.log("[HYBRID] Bắt đầu SIMPLE trước...")
        simple_docs = self.simple_crawl_search_results(
            keyword=keyword,
            max_pages=max_pages,
            docs_per_page=docs_per_page
        )

        # Nếu simple đủ tốt thì dùng luôn
        if not self._needs_fallback(simple_docs):
            self.log(f"[HYBRID] Simple đủ tốt (docs={len(simple_docs)}). Không cần fallback.")
            return simple_docs[:max_docs]

        # Fallback Playwright
        self.log(f"[HYBRID] Simple chưa đạt (docs xấu nhiều). Fallback sang PLAYWRIGHT...")
        urls = self._find_document_urls_paginated(
            keyword=keyword,
            max_pages=max_pages,
            docs_per_page=docs_per_page,
            max_docs=max_docs,
            headless=headless
        )

        existing = {d.get("url") for d in simple_docs if d.get("url")}
        merged = list(simple_docs)

        for i, url in enumerate(urls):
            if len(merged) >= max_docs:
                break
            if url in existing:
                continue
            self.log(f"[HYBRID] Crawl bổ sung (Playwright) {i+1}/{len(urls)}: {url}")
            d = self._crawl_document_detail(url)
            if d:
                merged.append(d)
                existing.add(url)
            time.sleep(Config.DELAY_BETWEEN_REQUESTS)

        self.log(f"[HYBRID] Hoàn tất. Simple={len(simple_docs)}, +Playwright={len(merged)-len(simple_docs)}, tổng={len(merged)}")
        return merged[:max_docs]

    def _find_document_urls(self, keyword: str = "giao thông", headless: bool = True, limit: int = 50):
        """Tìm URL văn bản theo từ khóa (render bằng Playwright, phân trang bằng click) + chặn login/anti-bot."""
        if not PLAYWRIGHT_AVAILABLE:
            self.log("Playwright không khả dụng, fallback sang requests")
            return self._find_document_urls_fallback(keyword, limit)

        from urllib.parse import quote_plus
        q = quote_plus(keyword)
        search_url = f"https://thuvienphapluat.vn/page/tim-van-ban.aspx?keyword={q}&match=True&area=0"

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=headless)
                context = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0 Safari/537.36"
                    ),
                    locale="vi-VN",
                    java_script_enabled=True,
                )
                page_obj = context.new_page()

                # set trước để collect_links dùng được
                seen = set()

                def is_blocked_html(html: str) -> bool:
                    text = html or ""
                    return ("Đăng nhập" in text) or ("Cloudflare" in text) or ("cf-browser-verification" in text)

                def collect_links():
                    # Lấy link trực tiếp từ DOM đã render (kể cả href tương đối / data-attr)
                    hrefs = page_obj.evaluate("""
                        () => Array.from(document.querySelectorAll("a"))
                        .map(a => a.getAttribute("href") || a.href || "")
                        .filter(h => /\\/van-ban\\/.*\\.aspx$/i.test(h))
                        .map(h => h.startsWith("http") ? h : new URL(h, location.origin).href)
                    """)
                    out = []
                    for h in hrefs:
                        if h not in seen:
                            seen.add(h)
                            out.append(h)
                    return out

                self.log(f"Đang mở trang tìm kiếm: {search_url}")
                page_obj.goto(search_url, timeout=60000, wait_until="domcontentloaded")
                # Cookie/banner nếu có
                try:
                    page_obj.locator("button:has-text('Đồng ý')").first.click(timeout=1500)
                except Exception:
                    pass

                # Đợi JS/XHR + cuộn để kích hoạt lazy-load
                page_obj.wait_for_load_state("networkidle", timeout=10000)
                for _ in range(6):
                    page_obj.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page_obj.wait_for_timeout(700)

                # Kiểm tra trang bị chặn / login
                html0 = page_obj.content()
                if is_blocked_html(html0):
                    self.log("Phát hiện trang đăng nhập/anti-bot (search page). Thử fallback requests.")
                    context.close(); browser.close()
                    return self._find_document_urls_fallback(keyword, limit)

                document_urls = []
                current_page_num = 1
                MAX_PAGES = 25  # tránh lặp vô hạn

                while len(document_urls) < limit and current_page_num <= MAX_PAGES:
                    # Thu thập link ở trang hiện tại
                    new_links = collect_links()
                    for u in new_links:
                        if re.search(r"/van-ban/.*\.aspx$", u) and u not in document_urls:
                            document_urls.append(u)
                            if len(document_urls) >= limit:
                                break
                    if len(document_urls) >= limit:
                        break

                    # Tìm số trang tiếp theo hoặc nút "Sau"
                    next_num = current_page_num + 1
                    locator_num = page_obj.locator(f"a:has-text('{next_num}')").first
                    locator_next = page_obj.locator("a:has-text('Sau')").first

                    clicked = False
                    try:
                        if locator_num.count() > 0:
                            locator_num.click(timeout=2500)
                            clicked = True
                        elif locator_next.count() > 0:
                            locator_next.click(timeout=2500)
                            clicked = True
                    except Exception:
                        clicked = False

                    if not clicked:
                        self.log("Hết trang hoặc không tìm thấy nút phân trang tiếp theo.")
                        break

                    current_page_num = next_num
                    page_obj.wait_for_load_state("networkidle", timeout=10000)
                    for _ in range(4):
                        page_obj.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        page_obj.wait_for_timeout(500)

                    # Kiểm tra mỗi lần sang trang mới có bị chặn không
                    htmlp = page_obj.content()
                    if is_blocked_html(htmlp):
                        self.log("Bị chuyển sang trang đăng nhập/anti-bot khi phân trang. Dừng và dùng kết quả hiện có.")
                        break

                # Debug nếu không thu được link nào
                if not document_urls:
                    try:
                        debug_dir = os.path.join(Config.RAW_DATA_DIR, "_debug")
                        os.makedirs(debug_dir, exist_ok=True)
                        with open(os.path.join(debug_dir, "last_search.html"), "w", encoding="utf-8") as f:
                            f.write(page_obj.content())
                        self.log(f"[DEBUG] Không tìm thấy link. Đã lưu HTML tìm kiếm tại: {os.path.join(debug_dir, 'last_search.html')}")
                    except Exception:
                        pass

                context.close()
                browser.close()
                return document_urls[:limit]

        except Exception as e:
            self.log(f"Lỗi khi _find_document_urls với Playwright: {e}")
            self.log("Fallback sang phương pháp requests")
            return self._find_document_urls_fallback(keyword, limit)


    def _find_document_urls_paginated(self, keyword: str = "giao thông", max_pages = 5, 
                                    docs_per_page: int = 20, max_docs: int = 100, headless: bool = True):
        """Crawl URLs từ nhiều trang với số lượng cụ thể mỗi trang"""
        if max_pages is None:
            self.log(f"Bắt đầu crawl TẤT CẢ trang, mỗi trang {docs_per_page} văn bản")
        else:
            self.log(f"Bắt đầu crawl {max_pages} trang, mỗi trang {docs_per_page} văn bản")
        
        if PLAYWRIGHT_AVAILABLE:
            return self._find_document_urls_paginated_playwright(keyword, max_pages, docs_per_page, max_docs, headless)
        else:
            return self._find_document_urls_paginated_requests(keyword, max_pages, docs_per_page, max_docs)

    def _find_document_urls_paginated_requests(self, keyword: str, max_pages, 
                                             docs_per_page: int, max_docs: int):
        """Crawl URLs bằng requests với phân trang rõ ràng - đảm bảo đúng số lượng mỗi trang"""
        try:
            q = quote_plus(keyword)
            base_url = f"https://thuvienphapluat.vn/page/tim-van-ban.aspx?keyword={q}&match=True&area=0"
            
            all_document_urls = []
            actual_pages_crawled = 0
            
            # Xử lý max_pages = None (crawl tất cả trang)
            if max_pages is None:
                max_pages_to_crawl = Config.MAX_PAGES_PER_KEYWORD  # Giới hạn an toàn
            else:
                max_pages_to_crawl = max_pages
            
            page_num = 1
            while page_num <= max_pages_to_crawl:
                if len(all_document_urls) >= max_docs:
                    break
                    
                # URL cho trang cụ thể
                page_url = f"{base_url}&page={page_num}"
                if max_pages is None:
                    self.log(f"Crawling trang {page_num} (TẤT CẢ): {page_url}")
                else:
                    self.log(f"Crawling trang {page_num}/{max_pages}: {page_url}")
                
                try:
                    response = self.session.get(page_url, timeout=Config.TIMEOUT)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Tìm links văn bản trong trang với nhiều selector
                    page_links = self._extract_document_links_from_page(soup, all_document_urls)
                    
                    # Giới hạn chính xác số văn bản mỗi trang
                    page_links = page_links[:docs_per_page]
                    all_document_urls.extend(page_links)
                    
                    self.log(f"Trang {page_num}: {len(page_links)}/{docs_per_page} văn bản (tổng: {len(all_document_urls)})")
                    
                    # Nếu trang này có văn bản, tính là đã crawl
                    if page_links:
                        actual_pages_crawled += 1
                    
                    # Nếu không tìm thấy văn bản nào, có thể đã hết
                    if not page_links:
                        self.log(f"Trang {page_num} không có văn bản mới, dừng crawl")
                        break
                    
                    # Nếu trang này không đủ văn bản, có thể đã hết
                    if len(page_links) < docs_per_page // 2:  # Ít hơn 50% số lượng mong đợi
                        self.log(f"Trang {page_num} chỉ có {len(page_links)} văn bản, có thể đã gần hết")
                    
                    # Delay giữa các trang
                    time.sleep(Config.DELAY_BETWEEN_REQUESTS)
                    
                except requests.exceptions.RequestException as e:
                    self.log(f"Lỗi khi crawl trang {page_num}: {e}")
                    
                # Tăng page_num và kiểm tra điều kiện dừng
                page_num += 1
                
                # Nếu max_pages = None, kiểm tra điều kiện dừng khác
                if max_pages is None:
                    # Dừng nếu không có văn bản mới trong vài trang liên tiếp
                    if not page_links:
                        consecutive_empty = getattr(self, '_consecutive_empty_pages', 0) + 1
                        self._consecutive_empty_pages = consecutive_empty
                        if consecutive_empty >= Config.MAX_EMPTY_PAGES:
                            self.log(f"Dừng crawl sau {consecutive_empty} trang trống liên tiếp")
                            break
                    else:
                        self._consecutive_empty_pages = 0
            
            self.log(f"Hoàn thành crawl {len(all_document_urls)} URLs từ {actual_pages_crawled} trang thực tế")
            return all_document_urls[:max_docs]
            
        except Exception as e:
            self.log(f"Lỗi trong _find_document_urls_paginated_requests: {e}")
            return []

    def _extract_document_links_from_page(self, soup, existing_urls):
        """Trích xuất links văn bản từ một trang với nhiều selector"""
        page_links = []
        
        # Thử nhiều selector khác nhau
        selectors = [
            'a[href*="/van-ban/"]',  # Link chứa /van-ban/
            'a[href$=".aspx"]',      # Link kết thúc bằng .aspx
            '.nqTitle a',            # Link trong title
            '.content-0 a',          # Link trong content
            '.left-col a'            # Link trong left column
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href', '')
                
                # Kiểm tra pattern URL văn bản
                if '/van-ban/' in href and href.endswith('.aspx'):
                    # Chuẩn hóa URL
                    if not href.startswith('http'):
                        href = f"https://thuvienphapluat.vn{href}"
                    
                    # Tránh trùng lặp
                    if href not in existing_urls and href not in page_links:
                        page_links.append(href)
        
        return page_links

    def _find_document_urls_paginated_playwright(self, keyword: str, max_pages, 
                                               docs_per_page: int, max_docs: int, headless: bool):
        """Crawl URLs bằng Playwright với phân trang rõ ràng"""
        try:
            q = quote_plus(keyword)
            search_url = f"https://thuvienphapluat.vn/page/tim-van-ban.aspx?keyword={q}&match=True&area=0"

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=headless)
                context = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0 Safari/537.36"
                    ),
                    locale="vi-VN",
                    java_script_enabled=True,
                )
                page_obj = context.new_page()

                def collect_page_links():
                    """Thu thập links từ trang hiện tại"""
                    hrefs = page_obj.evaluate("""
                        () => Array.from(document.querySelectorAll("a"))
                        .map(a => a.getAttribute("href") || a.href || "")
                        .filter(h => /\\/van-ban\\/.*\\.aspx$/i.test(h))
                        .map(h => h.startsWith("http") ? h : new URL(h, location.origin).href)
                    """)
                    return hrefs

                self.log(f"Đang mở trang tìm kiếm: {search_url}")
                page_obj.goto(search_url, timeout=60000, wait_until="domcontentloaded")
                
                # Xử lý cookie banner nếu có
                try:
                    page_obj.locator("button:has-text('Đồng ý')").first.click(timeout=1500)
                except Exception:
                    pass

                all_document_urls = []
                
                # Xử lý max_pages = None
                if max_pages is None:
                    max_pages_to_crawl = Config.MAX_PAGES_PER_KEYWORD
                else:
                    max_pages_to_crawl = max_pages
                
                page_num = 1
                consecutive_empty = 0
                
                while page_num <= max_pages_to_crawl:
                    if len(all_document_urls) >= max_docs:
                        break
                        
                    if max_pages is None:
                        self.log(f"Đang crawl trang {page_num} (TẤT CẢ)")
                    else:
                        self.log(f"Đang crawl trang {page_num}/{max_pages}")
                    
                    # Đợi trang load và cuộn để kích hoạt lazy loading
                    page_obj.wait_for_load_state("networkidle", timeout=15000)
                    for _ in range(3):
                        page_obj.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        page_obj.wait_for_timeout(500)

                    # Thu thập links từ trang hiện tại
                    page_links = collect_page_links()
                    new_links = []
                    
                    for link in page_links:
                        if link not in all_document_urls:
                            new_links.append(link)
                            all_document_urls.append(link)
                            
                            # Giới hạn số văn bản mỗi trang
                            if len(new_links) >= docs_per_page:
                                break
                    
                    self.log(f"Trang {page_num}: tìm thấy {len(new_links)} văn bản mới (tổng: {len(all_document_urls)})")
                    
                    # Nếu không tìm thấy văn bản mới, dừng
                    if not new_links:
                        consecutive_empty += 1
                        self.log(f"Trang {page_num} không có văn bản mới ({consecutive_empty}/{Config.MAX_EMPTY_PAGES})")
                        if consecutive_empty >= Config.MAX_EMPTY_PAGES:
                            self.log(f"Dừng crawl sau {consecutive_empty} trang trống liên tiếp")
                            break
                    else:
                        consecutive_empty = 0
                    
                    # Chuyển sang trang tiếp theo
                    if max_pages is None or page_num < max_pages_to_crawl:
                        next_page_num = page_num + 1
                        
                        # Thử click vào số trang tiếp theo
                        try:
                            next_locator = page_obj.locator(f"a:has-text('{next_page_num}')").first
                            if next_locator.count() > 0:
                                next_locator.click(timeout=3000)
                            else:
                                # Thử nút "Sau"
                                next_btn = page_obj.locator("a:has-text('Sau')").first
                                if next_btn.count() > 0:
                                    next_btn.click(timeout=3000)
                                else:
                                    self.log(f"Không tìm thấy nút chuyển trang từ trang {page_num}")
                                    break
                        except Exception as e:
                            self.log(f"Lỗi khi chuyển từ trang {page_num} sang {next_page_num}: {e}")
                            break
                    
                    page_num += 1

                context.close()
                browser.close()
                
                self.log(f"Hoàn thành crawl {len(all_document_urls)} URLs từ Playwright")
                return all_document_urls[:max_docs]

        except Exception as e:
            self.log(f"Lỗi trong _find_document_urls_paginated_playwright: {e}")
            self.log("Fallback sang phương pháp requests")
            return self._find_document_urls_paginated_requests(keyword, max_pages, docs_per_page, max_docs)

    def _find_document_urls_fallback(self, keyword: str, limit: int = 50):
        """Fallback method sử dụng requests thay vì Playwright"""
        try:
            q = quote_plus(keyword)
            search_url = f"https://thuvienphapluat.vn/page/tim-van-ban.aspx?keyword={q}&match=True&area=0"
            
            document_urls = []
            page = 1
            max_pages = 10
            
            while len(document_urls) < limit and page <= max_pages:
                url = f"{search_url}&page={page}"
                self.log(f"Crawling trang {page}: {url}")
                
                response = self.session.get(url, timeout=Config.TIMEOUT)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Tìm links văn bản
                links = soup.find_all('a', href=True)
                page_links = []
                
                for link in links:
                    href = link.get('href', '')
                    if '/van-ban/' in href and href.endswith('.aspx'):
                        if not href.startswith('http'):
                            href = f"https://thuvienphapluat.vn{href}"
                        if href not in document_urls:
                            document_urls.append(href)
                            page_links.append(href)
                
                self.log(f"Trang {page}: tìm thấy {len(page_links)} links mới")
                
                if not page_links:  # Không tìm thấy link mới
                    break
                    
                page += 1
                time.sleep(Config.DELAY_BETWEEN_REQUESTS)
            
            return document_urls[:limit]
            
        except Exception as e:
            self.log(f"Lỗi trong fallback method: {e}")
            return []

    def _crawl_document_detail(self, url):
        """Crawl chi tiết một văn bản với retry strategy"""
        return self._crawl_document_with_retry(url)
    
    def _crawl_document_with_retry(self, url):
        """Crawl document với retry strategy và soft-keep"""
        retry_strategies = [
            {"name": "standard", "headless": True, "delay": 1},
            {"name": "visible", "headless": False, "delay": 2, "change_ua": True},
            {"name": "patient", "headless": False, "delay": 3, "scroll": True}
        ]
        
        last_error = None
        
        for attempt, strategy in enumerate(retry_strategies, 1):
            try:
                self.log(f"Attempt {attempt}/{len(retry_strategies)} for {url} (strategy: {strategy['name']})")
                
                # Apply strategy
                if strategy.get("change_ua"):
                    self._rotate_user_agent()
                
                # Standard requests approach
                response = self._make_request_with_strategy(url, strategy)
                if not response:
                    continue
                    
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Check if we got blocked (common indicators)
                if self._is_blocked_response(soup, response):
                    self.log(f"Detected blocked response for {url} on attempt {attempt}")
                    last_error = "blocked_response"
                    time.sleep(strategy.get("delay", 1))
                    continue

                doc_data = {
                    "url": url,
                    "crawl_time": datetime.now().isoformat(),
                    "status": "success",
                    "title": self._extract_title(soup),
                    "number": self._extract_document_number(soup),
                    "field": self._extract_field(soup),
                    "issue_date": self._extract_issue_date(soup),
                    "effective_date": self._extract_effective_date(soup),
                    "agency": self._extract_agency(soup),
                    "content": self._extract_content(soup),
                    "retry_attempt": attempt,
                    "retry_strategy": strategy['name']
                }
                
                # Validate document quality
                if self._is_valid_document(doc_data):
                    self.log(f"Successfully crawled {url} on attempt {attempt}")
                    return doc_data
                else:
                    self.log(f"Low quality document from {url} on attempt {attempt}")
                    last_error = "low_quality"
                    
            except requests.exceptions.RequestException as e:
                last_error = f"request_error: {str(e)}"
                self.log(f"Request error for {url} on attempt {attempt}: {e}")
                
            except Exception as e:
                last_error = f"parse_error: {str(e)}"
                self.log(f"Parse error for {url} on attempt {attempt}: {e}")
            
            # Wait before next retry
            if attempt < len(retry_strategies):
                time.sleep(strategy.get("delay", 1))
        
        # All retries failed - create soft-keep document
        return self._create_blocked_document(url, last_error)
    
    def _make_request_with_strategy(self, url, strategy):
        """Make request with specific strategy"""
        try:
            timeout = Config.TIMEOUT * strategy.get("delay", 1)
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response
        except Exception:
            return None
    
    def _rotate_user_agent(self):
        """Rotate user agent to avoid detection"""
        user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
        import random
        new_ua = random.choice(user_agents)
        self.session.headers.update({'User-Agent': new_ua})
        self.log(f"Rotated User-Agent to: {new_ua[:50]}...")
    
    def _is_blocked_response(self, soup, response):
        """Check if response indicates we're blocked"""
        # Common blocking indicators
        text = soup.get_text().lower()
        blocking_indicators = [
            "access denied",
            "blocked",
            "captcha",
            "robot",
            "bot detection",
            "rate limit",
            "too many requests",
            "đăng nhập" # Vietnamese login page
        ]
        
        # Check status code
        if response.status_code in [403, 429, 503]:
            return True
            
        # Check content
        for indicator in blocking_indicators:
            if indicator in text:
                return True
                
        # Check if content is suspiciously short
        if len(text.strip()) < 100:
            return True
            
        return False
    
    def _is_valid_document(self, doc_data):
        """Check if document has sufficient quality"""
        # Must have either good title or good content
        has_title = doc_data.get("title", "Không xác định") != "Không xác định"
        has_content = doc_data.get("content", "Không xác định") != "Không xác định"
        content_length = len(doc_data.get("content", ""))
        
        # Minimum quality thresholds
        if has_title and has_content and content_length > 200:
            return True
        elif has_content and content_length > 1000:  # Good content can compensate for missing title
            return True
            
        return False
    
    def _create_blocked_document(self, url, error_reason):
        """Create a soft-keep document for blocked/failed URLs"""
        return {
            "url": url,
            "crawl_time": datetime.now().isoformat(),
            "status": "blocked",
            "error_reason": error_reason,
            "title": "Blocked/Failed",
            "number": "Không xác định",
            "field": "Không xác định", 
            "issue_date": "Không xác định",
            "effective_date": "Không xác định",
            "agency": "Không xác định",
            "content": "Document could not be crawled due to blocking or errors",
            "retry_needed": True
        }

    # -----------------
    # Helpers trích xuất
    # -----------------
    def _extract_title(self, soup):
        """Trích xuất tiêu đề"""
        # Loại bỏ các title không hợp lệ
        invalid_titles = ["đăng nhập", "login", "trang chủ", "home", ""]
        
        selectors = [
            "h1#ctl00_mainContent_ctl00_lblTieuDe",
            "h1.title",
            "h1",
            ".title",
            ".doc-title",
        ]
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                if title and title.lower() not in invalid_titles:
                    return title
        
        # Fallback: tìm trong content theo pattern
        content_text = soup.get_text(" ", strip=True)
        
        # Tìm pattern tiêu đề thường gặp
        patterns = [
            r"(QUYẾT ĐỊNH[^\.]{10,200})",
            r"(KẾ HOẠCH[^\.]{10,200})", 
            r"(THÔNG BÁO[^\.]{10,200})",
            r"(LỆNH[^\.]{10,200})",
            r"(LUẬT[^\.]{10,200})",
            r"(THÔNG TƯ[^\.]{10,200})",
            r"(VĂN BẢN HỢP NHẤT[^\.]{10,200})"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content_text, re.IGNORECASE | re.DOTALL)
            if match:
                title = match.group(1).strip()
                # Làm sạch title
                title = re.sub(r'\s+', ' ', title)  # Thay nhiều space thành 1
                title = re.sub(r'\r\n', ' ', title)  # Thay xuống dòng thành space
                if 10 <= len(title) <= 200:
                    return title
                    
        return "Không xác định"

    def _extract_document_number(self, soup):
        """Trích xuất số hiệu văn bản (ưu tiên metadata 'Số:'; fallback quét đầu văn bản, hỗ trợ nhiều biến thể)."""
        import re

        def _clean(s: str) -> str:
            s = (s or "").replace("\xa0", " ").strip()
            s = re.sub(r"\s+", " ", s)
            return s

        def _is_valid(num: str) -> bool:
            if not num:
                return False
            num = num.strip()
            # Loại bỏ pattern ngày tháng dd/mm/yyyy
            if re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}", num):
                return False
            # Bắt buộc phải có ít nhất một chữ cái (tránh nhầm "123/2024/123")
            if not re.search(r"[A-ZĐ]", num, flags=re.IGNORECASE):
                return False
            # Tránh số hiệu quá ngắn kiểu "1/KH"
            return len(num) >= 5

        # Các regex số hiệu (chấp nhận nhiều biến thể)
        RX_NUMBERS = [
            # Có nhãn "Số:" (đầy đủ năm)
            re.compile(r"Số[:\s]+(?P<num>\d{1,4}/\d{4}/[A-ZĐ\-]+(?:-[A-ZĐ]+)*)", re.IGNORECASE),
            # Có nhãn "Số:" (không có năm)
            re.compile(r"Số[:\s]+(?P<num>\d{1,4}/[A-ZĐ\-]+(?:-[A-ZĐ]+)*)", re.IGNORECASE),

            # Không có nhãn "Số:" — các biến thể phổ biến trong nội dung
            # ví dụ: 01/2024/QĐ-UBND ; 2060/QĐ-TTg ; 689/KH-UBATGTQG
            re.compile(r"(?P<num>\d{1,4}/\d{4}/[A-ZĐ][A-ZĐ\-]{0,20}(?:-[A-ZĐ]{1,15})*)", re.IGNORECASE),
            re.compile(r"(?P<num>\d{1,4}/[A-ZĐ][A-ZĐ\-]{0,20}(?:-[A-ZĐ]{1,15})*)", re.IGNORECASE),

            # Biến thể gạch ngang rồi / (ví dụ: 45-KL/TW)
            re.compile(r"(?P<num>\d{1,4}-[A-ZĐ]{1,10}/[A-ZĐ\-]{1,15})", re.IGNORECASE),

            # Fallback cũ (ít gặp)
            re.compile(r"(?P<num>\d{1,4}/\d{1,4}/[A-ZĐ\-]+)", re.IGNORECASE),
            re.compile(r"Số\s+(?P<num>\d{1,4}/[A-ZĐ\-]+)", re.IGNORECASE),
        ]

        def _extract_from_text(text: str) -> str | None:
            txt = _clean(text)
            for rx in RX_NUMBERS:
                m = rx.search(txt)
                if m:
                    cand = m.group("num").upper()
                    # Chuẩn hóa nhẹ: gom nhiều dấu '-' liên tiếp
                    cand = re.sub(r"-{2,}", "-", cand)
                    cand = cand.strip(" -")
                    if _is_valid(cand):
                        return cand
            return None

        # 1) Ưu tiên metadata: các node chứa "Số:"
        for node in soup.find_all(string=re.compile(r"^\s*Số\s*:", re.IGNORECASE)):
            container = node.parent
            if container:
                got = _extract_from_text(container.get_text(" ", strip=True))
                if got:
                    return got
            # Thử lấy ô/kề-sau (trường hợp bảng metadata chia cột)
            sib = None
            try:
                sib = node.find_parent().find_next_sibling()
            except Exception:
                pass
            if sib:
                got = _extract_from_text(sib.get_text(" ", strip=True))
                if got:
                    return got

        # 2) Fall-back: quét phần đầu văn bản (hạn chế nhặt 'ngày' ở phần căn cứ)
        head = soup.get_text(" ", strip=True)[:1500]
        got = _extract_from_text(head)
        if got:
            return got

        # 3) Fall-back cuối: quét toàn văn
        full = soup.get_text(" ", strip=True)
        got = _extract_from_text(full)
        if got:
            return got

        return "Không xác định"

    def _extract_field(self, soup):
        """Trích xuất lĩnh vực"""
        # Tìm theo label
        for label in ["Lĩnh vực", "Linh vuc", "LĨNH VỰC"]:
            el = soup.find(string=re.compile(label, re.IGNORECASE))
            if el and el.parent:
                val = el.parent.get_text(" ", strip=True)
                # Lấy phần sau dấu : nếu có
                parts = re.split(r":", val, maxsplit=1)
                if len(parts) == 2 and parts[1].strip():
                    return parts[1].strip()
        # Fallback: đoán theo nội dung
        text = soup.get_text(" ", strip=True).lower()
        fields = {
            "giao thông": "Giao thông",
            "an toàn giao thông": "Giao thông - ATGT",
            "thuế": "Thuế",
            "tài chính": "Tài chính",
            "lao động": "Lao động",
            "xã hội": "Xã hội",
            "kinh tế": "Kinh tế",
        }
        for kw, name in fields.items():
            if kw in text:
                return name
        return "Không xác định"

    def _extract_issue_date(self, soup):
        """Trích xuất ngày ban hành (ưu tiên ngày ký ở phần đầu văn bản)."""
        import re

        def _fmt(d, m, y):
            try:
                return f"{int(d):02d}/{int(m):02d}/{int(y)}"
            except Exception:
                return "Không xác định"

        text = soup.get_text(" ", strip=True)
        head = text[:2000]  # chỉ ưu tiên phần đầu để tránh dính ngày trong 'Căn cứ ...'

        # 1) Mẫu header: ", ngày d tháng m năm yyyy"
        m = re.search(r"[,;]\s*ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})",
                    head, flags=re.IGNORECASE)
        if m:
            d, mth, y = m.groups()
            return _fmt(d, mth, y)

        # 2) Nhãn 'Ngày ban hành' → dd/mm/yyyy
        m = re.search(r"ngày\s+ban\s+hành\D{0,20}(\d{1,2}/\d{1,2}/\d{4})",
                    head, flags=re.IGNORECASE)
        if m:
            return m.group(1)

        # 3) dd/mm/yyyy ở gần chữ 'ngày' trong phần đầu
        m = re.search(r"ngày\D{0,10}(\d{1,2}/\d{1,2}/\d{4})",
                    head, flags=re.IGNORECASE)
        if m:
            return m.group(1)

        # 4) Fallback: lấy dd/mm/yyyy đầu tiên trong phần đầu
        m = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", head)
        if m:
            return m.group(1)

        # 5) Cùng lắm mới quét toàn văn
        m = re.search(r"[,;]\s*ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})",
                    text, flags=re.IGNORECASE)
        if m:
            d, mth, y = m.groups()
            return _fmt(d, mth, y)
        m = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", text)
        if m:
            return m.group(1)

        return "Không xác định"

    def _extract_effective_date(self, soup):
        txt = soup.get_text(" ", strip=True)
        m = re.search(r"(có\s+hiệu\s+lực|hiệu\s+lực)\D{0,30}(\d{1,2}/\d{1,2}/\d{4})", txt, re.IGNORECASE)
        if m:
            return m.group(2)
        issue = self._extract_issue_date(soup)
        return issue if issue != "Không xác định" else "Không xác định"

    def _extract_agency(self, soup):
        """Trích xuất cơ quan ban hành"""
        text = soup.get_text(" ", strip=True)
        
        # Tìm cơ quan ở đầu văn bản (thường ở header)
        header_patterns = [
            r"^([A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ\s]+)\s*-------",
            r"^([A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ\s]+)\s*CỘNG HÒA",
        ]
        
        for pattern in header_patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                agency = match.group(1).strip()
                # Làm sạch và chuẩn hóa
                agency = re.sub(r'\s+', ' ', agency)
                if 5 <= len(agency) <= 100:
                    return agency.title()
        
        # Fallback: tìm theo keywords phổ biến
        agency_keywords = {
            r"chính phủ": "Chính Phủ",
            r"bộ giao thông vận tải": "Bộ Giao Thông Vận Tải", 
            r"bộ công an": "Bộ Công An",
            r"bộ tài chính": "Bộ Tài Chính",
            r"quốc hội": "Quốc Hội",
            r"chủ tịch nước": "Chủ Tịch Nước",
            r"ủy ban nhân dân": "Ủy Ban Nhân Dân",
            r"ủy ban an toàn giao thông": "Ủy Ban An Toàn Giao Thông",
            r"tòa án nhân dân tối cao": "Tòa Án Nhân Dân Tối Cao"
        }
        
        text_lower = text.lower()
        for keyword, agency_name in agency_keywords.items():
            if re.search(keyword, text_lower):
                return agency_name
                
        return "Không xác định"

    def _extract_content(self, soup):
        """Trích xuất nội dung đầy đủ từ <div class=\"content1\"> (giới hạn 5000 ký tự)"""
        # Một số trang dùng content1, content, or article-content
        content_div = (
            soup.find("div", class_="content1")
            or soup.find("div", class_="content")
            or soup.find("article")
        )
        if content_div:
            for script in content_div(["script", "style"]):
                script.decompose()
            content = content_div.get_text(separator=" ", strip=True)
            return content[:5000] if content else "Không xác định"
        return "Không xác định"

    def _calculate_metrics(self):
        """Tính metrics với retry strategy và soft-keep tracking"""
        total_time = self.get_processing_time()
        total_docs = len(self.crawled_documents)
        
        # Phân loại documents theo status
        success_docs = [d for d in self.crawled_documents if d.get("status") == "success"]
        blocked_docs = [d for d in self.crawled_documents if d.get("status") == "blocked"]
        
        # Tính retry statistics
        retry_stats = {}
        for doc in success_docs:
            attempt = doc.get("retry_attempt", 1)
            strategy = doc.get("retry_strategy", "standard")
            retry_stats[f"attempt_{attempt}"] = retry_stats.get(f"attempt_{attempt}", 0) + 1
            retry_stats[f"strategy_{strategy}"] = retry_stats.get(f"strategy_{strategy}", 0) + 1

        self.metrics = {
            # Basic counts
            "total_documents_attempted": total_docs,
            "total_documents_success": len(success_docs),
            "total_documents_blocked": len(blocked_docs),
            
            # Rates
            "success_rate": (len(success_docs) / total_docs * 100) if total_docs > 0 else 0,
            "block_rate": (len(blocked_docs) / total_docs * 100) if total_docs > 0 else 0,
            "recall_potential": ((len(success_docs) + len(blocked_docs)) / total_docs * 100) if total_docs > 0 else 0,
            
            # Performance
            "average_time_per_document": total_time / total_docs if total_docs > 0 else 0,
            "total_processing_time": total_time,
            
            # Retry analysis
            "retry_statistics": retry_stats,
            
            # Quality metrics
            "documents_with_full_metadata": len([d for d in success_docs if self._has_full_metadata(d)]),
            "average_content_length": sum(len(d.get("content", "")) for d in success_docs) / len(success_docs) if success_docs else 0
        }
    
    def _has_full_metadata(self, doc):
        """Check if document has complete metadata"""
        required_fields = ["title", "number", "issue_date", "agency"]
        return all(doc.get(field, "Không xác định") != "Không xác định" for field in required_fields)

    def print_crawl_summary(self, results):
        """In tóm tắt kết quả crawl với metrics mới"""
        print(f"\n{'='*60}")
        print(f"TÓM TẮT KẾT QUẢ CRAWL (WITH RETRY STRATEGY)")
        print(f"{'='*60}")
        
        # Basic info
        print(f"Số trang đã crawl: {results.get('pages_crawled', 'N/A')}")
        print(f"Văn bản mỗi trang: {results.get('docs_per_page', 'N/A')}")
        
        # Success/Block breakdown
        metrics = self.metrics
        print(f"\nKẾT QUẢ CRAWL:")
        print(f"  Tổng văn bản thử crawl: {metrics.get('total_documents_attempted', 0)}")
        print(f"  Thành công: {metrics.get('total_documents_success', 0)} ({metrics.get('success_rate', 0):.1f}%)")
        print(f"  Bị chặn/lỗi: {metrics.get('total_documents_blocked', 0)} ({metrics.get('block_rate', 0):.1f}%)")
        print(f"  Recall potential: {metrics.get('recall_potential', 0):.1f}%")
        
        # Performance
        print(f"\nHIỆU SUẤT:")
        print(f"  Thời gian xử lý: {metrics.get('total_processing_time', 0):.2f}s")
        print(f"  Thời gian TB/văn bản: {metrics.get('average_time_per_document', 0):.2f}s")
        print(f"  Độ dài nội dung TB: {metrics.get('average_content_length', 0):.0f} ký tự")
        
        # Retry analysis
        retry_stats = metrics.get('retry_statistics', {})
        if retry_stats:
            print(f"\nPHÂN TÍCH RETRY:")
            for key, value in retry_stats.items():
                if key.startswith('attempt_'):
                    print(f"  Thành công lần {key.split('_')[1]}: {value} văn bản")
                elif key.startswith('strategy_'):
                    print(f"  Chiến lược {key.split('_')[1]}: {value} văn bản")
        
        # Quality metrics
        full_metadata = metrics.get('documents_with_full_metadata', 0)
        success_count = metrics.get('total_documents_success', 0)
        if success_count > 0:
            print(f"\nCHẤT LƯỢNG METADATA:")
            print(f"  Văn bản có đủ metadata: {full_metadata}/{success_count} ({full_metadata/success_count*100:.1f}%)")
        
        # Field distribution (only for successful documents)
        success_docs = [d for d in results.get('documents', []) if d.get('status') == 'success']
        if success_docs:
            fields = {}
            for doc in success_docs:
                field = doc.get('field', 'Không xác định')
                fields[field] = fields.get(field, 0) + 1
            
            print(f"\nPHÂN BỐ THEO LĨNH VỰC (chỉ văn bản thành công):")
            for field, count in sorted(fields.items(), key=lambda x: x[1], reverse=True):
                print(f"  - {field}: {count} văn bản")
        
        # Blocked documents info
        blocked_docs = [d for d in results.get('documents', []) if d.get('status') == 'blocked']
        if blocked_docs:
            print(f"\nVĂN BẢN BỊ CHẶN (có thể retry sau):")
            error_reasons = {}
            for doc in blocked_docs:
                reason = doc.get('error_reason', 'unknown')
                error_reasons[reason] = error_reasons.get(reason, 0) + 1
            
            for reason, count in error_reasons.items():
                print(f"  - {reason}: {count} văn bản")
        
        print(f"{'='*60}\n")

    def validate_results(self):
        """Kiểm tra chất lượng kết quả"""
        if not self.crawled_documents:
            return False

        valid_docs = 0
        for doc in self.crawled_documents:
            if (
                doc.get("title") != "Không xác định"
                and doc.get("content")
                and len(doc.get("content", "")) > 100
            ):
                valid_docs += 1

        validation_rate = valid_docs / len(self.crawled_documents)
        return validation_rate > 0.5  # 50% documents phải hợp lệ

    def get_crawl_statistics(self):
        """Lấy thống kê chi tiết về kết quả crawl"""
        if not self.crawled_documents:
            return {}
        
        stats = {
            "total_documents": len(self.crawled_documents),
            "fields": {},
            "agencies": {},
            "years": {},
            "valid_documents": 0
        }
        
        for doc in self.crawled_documents:
            # Thống kê lĩnh vực
            field = doc.get('field', 'Không xác định')
            stats['fields'][field] = stats['fields'].get(field, 0) + 1
            
            # Thống kê cơ quan
            agency = doc.get('agency', 'Không xác định')
            stats['agencies'][agency] = stats['agencies'].get(agency, 0) + 1
            
            # Thống kê năm
            issue_date = doc.get('issue_date', '')
            if '/' in issue_date:
                try:
                    year = issue_date.split('/')[-1]
                    stats['years'][year] = stats['years'].get(year, 0) + 1
                except:
                    pass
            
            # Đếm văn bản hợp lệ
            if (doc.get("title") != "Không xác định" and 
                doc.get("content") and len(doc.get("content", "")) > 100):
                stats['valid_documents'] += 1
        
        return stats

    def crawl_multiple_pages(self, keyword="giao thông", pages=5, docs_per_page=20):
        """
        Method tiện ích để crawl nhiều trang với cấu hình đơn giản
        
        Args:
            keyword (str): Từ khóa tìm kiếm
            pages (int): Số trang cần crawl
            docs_per_page (int): Số văn bản mỗi trang
            
        Returns:
            dict: Kết quả crawl với thông tin chi tiết
        """
        return self.process({
            "keyword": keyword,
            "max_pages": pages,
            "docs_per_page": docs_per_page,
            "max_docs": pages * docs_per_page,
            "headless": True
        })

    def crawl_giao_thong_multi_pages(self, pages=10, docs_per_page=20):
        """
        Method chuyên biệt để crawl lĩnh vực giao thông với nhiều trang
        
        Args:
            pages (int): Số trang cần crawl (mặc định 10)
            docs_per_page (int): Số văn bản mỗi trang (mặc định 20)
            
        Returns:
            dict: Kết quả crawl lĩnh vực giao thông
        """
        self.log(f"BẮT ĐẦU CRAWL LĨNH VỰC GIAO THÔNG")
        self.log(f"Cấu hình: {pages} trang × {docs_per_page} văn bản/trang = {pages * docs_per_page} văn bản tối đa")
        
        # Sử dụng từ khóa tối ưu cho giao thông
        traffic_keywords = [
            "giao thông",
            "an toàn giao thông", 
            "luật giao thông",
            "nghị định giao thông"
        ]
        
        all_documents = []
        total_pages_crawled = 0
        
        for keyword in traffic_keywords:
            self.log(f"Crawling với từ khóa: '{keyword}'")
            
            # Reset crawled_documents cho mỗi từ khóa
            self.crawled_documents = []
            
            results = self.process({
                "keyword": keyword,
                "max_pages": pages // len(traffic_keywords) + 1,  # Chia đều số trang
                "docs_per_page": docs_per_page,
                "max_docs": (pages * docs_per_page) // len(traffic_keywords),
                "headless": True
            })
            
            # Lọc chỉ lấy văn bản thực sự về giao thông
            filtered_docs = []
            for doc in results.get('documents', []):
                if self._is_traffic_related(doc):
                    filtered_docs.append(doc)
            
            all_documents.extend(filtered_docs)
            total_pages_crawled += results.get('pages_crawled', 0)
            
            self.log(f"Từ khóa '{keyword}': {len(filtered_docs)} văn bản về giao thông")
            
            # Dừng nếu đã đủ số lượng
            if len(all_documents) >= pages * docs_per_page:
                break
        
        # Cập nhật kết quả cuối cùng
        self.crawled_documents = all_documents[:pages * docs_per_page]
        self._calculate_metrics()
        
        final_results = {
            "documents": self.crawled_documents,
            "total_crawled": len(self.crawled_documents),
            "pages_crawled": total_pages_crawled,
            "docs_per_page": docs_per_page,
            "target_field": "Giao thông",
            "keywords_used": traffic_keywords
        }
        
        self.log(f"HOÀN THÀNH: {len(self.crawled_documents)} văn bản giao thông từ {total_pages_crawled} trang")
        return final_results

    def crawl_giao_thong_all_pages(self, docs_per_page=20, max_docs=None):
        """
        Method crawl TẤT CẢ các trang về giao thông có thể
        
        Args:
            docs_per_page (int): Số văn bản mỗi trang (mặc định 20)
            max_docs (int): Giới hạn tối đa văn bản (None = không giới hạn)
            
        Returns:
            dict: Kết quả crawl TẤT CẢ văn bản giao thông
        """
        self.log(f"BẮT ĐẦU CRAWL TẤT CẢ TRANG VỀ GIAO THÔNG")
        self.log(f"Cấu hình: Crawl đến hết, {docs_per_page} văn bản/trang")
        if max_docs:
            self.log(f"Giới hạn tối đa: {max_docs} văn bản")
        else:
            self.log(f"Không giới hạn số lượng - crawl đến hết!")
        
        # Sử dụng từ khóa từ config
        traffic_keywords = Config.TRAFFIC_KEYWORDS
        
        all_documents = []
        total_pages_crawled = 0
        
        for keyword in traffic_keywords:
            if max_docs and len(all_documents) >= max_docs:
                break
                
            self.log(f"Crawling TẤT CẢ trang với từ khóa: '{keyword}'")
            
            # Crawl không giới hạn trang cho từ khóa này
            keyword_docs, keyword_pages = self._crawl_all_pages_for_keyword(
                keyword, docs_per_page, max_docs - len(all_documents) if max_docs else None
            )
            
            # Lọc chỉ lấy văn bản thực sự về giao thông
            filtered_docs = []
            for doc in keyword_docs:
                if self._is_traffic_related(doc):
                    # Kiểm tra trùng lặp URL
                    if not any(existing['url'] == doc['url'] for existing in all_documents):
                        filtered_docs.append(doc)
            
            all_documents.extend(filtered_docs)
            total_pages_crawled += keyword_pages
            
            self.log(f"Từ khóa '{keyword}': {len(filtered_docs)} văn bản mới từ {keyword_pages} trang")
            self.log(f"Tổng cộng hiện tại: {len(all_documents)} văn bản")
        
        # Cập nhật kết quả cuối cùng
        self.crawled_documents = all_documents[:max_docs] if max_docs else all_documents
        self._calculate_metrics()
        
        final_results = {
            "documents": self.crawled_documents,
            "total_crawled": len(self.crawled_documents),
            "pages_crawled": total_pages_crawled,
            "docs_per_page": docs_per_page,
            "target_field": "Giao thông",
            "keywords_used": traffic_keywords,
            "crawl_type": "ALL_PAGES"
        }
        
        self.log(f"HOÀN THÀNH CRAWL TẤT CẢ: {len(self.crawled_documents)} văn bản giao thông từ {total_pages_crawled} trang")
        return final_results

    def _crawl_all_pages_for_keyword(self, keyword, docs_per_page, max_docs_for_keyword):
        """Crawl tất cả trang có thể cho một từ khóa"""
        self.log(f"Bắt đầu crawl tất cả trang cho từ khóa: {keyword}")
        
        all_docs = []
        page_num = 1
        consecutive_empty_pages = 0
        MAX_EMPTY_PAGES = Config.MAX_EMPTY_PAGES
        MAX_PAGES_PER_KEYWORD = Config.MAX_PAGES_PER_KEYWORD
        
        while page_num <= MAX_PAGES_PER_KEYWORD:
            if max_docs_for_keyword and len(all_docs) >= max_docs_for_keyword:
                break
                
            self.log(f"Crawling trang {page_num} cho từ khóa '{keyword}'")
            
            # Crawl một trang cụ thể
            page_docs = self._crawl_single_page(keyword, page_num, docs_per_page)
            
            if not page_docs:
                consecutive_empty_pages += 1
                self.log(f"Trang {page_num} trống ({consecutive_empty_pages}/{MAX_EMPTY_PAGES} trang trống liên tiếp)")
                
                if consecutive_empty_pages >= MAX_EMPTY_PAGES:
                    self.log(f"Dừng crawl từ khóa '{keyword}' sau {consecutive_empty_pages} trang trống liên tiếp")
                    break
            else:
                consecutive_empty_pages = 0  # Reset counter
                all_docs.extend(page_docs)
                self.log(f"Trang {page_num}: {len(page_docs)} văn bản (tổng: {len(all_docs)})")
            
            page_num += 1
            
            # Delay giữa các trang
            time.sleep(Config.DELAY_BETWEEN_REQUESTS)
        
        self.log(f"Hoàn thành từ khóa '{keyword}': {len(all_docs)} văn bản từ {page_num-1} trang")
        return all_docs, page_num - 1

    def _crawl_single_page(self, keyword, page_num, docs_per_page):
        """Crawl một trang cụ thể"""
        try:
            q = quote_plus(keyword)
            page_url = f"https://thuvienphapluat.vn/page/tim-van-ban.aspx?keyword={q}&match=True&area=0&page={page_num}"
            
            response = self.session.get(page_url, timeout=Config.TIMEOUT)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Tìm links văn bản trong trang
            page_links = self._extract_document_links_from_page(soup, [])
            
            # Giới hạn số văn bản mỗi trang
            page_links = page_links[:docs_per_page]
            
            # Crawl chi tiết từng văn bản
            page_docs = []
            for url in page_links:
                doc_data = self._crawl_document_detail(url)
                if doc_data:
                    page_docs.append(doc_data)
                    
                # Delay giữa các văn bản
                time.sleep(Config.DELAY_BETWEEN_REQUESTS)
            
            return page_docs
            
        except Exception as e:
            self.log(f"Lỗi khi crawl trang {page_num}: {e}")
            return []

    def _is_traffic_related(self, doc):
        """Kiểm tra văn bản có liên quan đến giao thông không"""
        traffic_terms = [
            "giao thông", "an toàn giao thông", "atgt", 
            "phương tiện giao thông", "đường bộ", "ô tô", "xe máy",
            "biển báo", "tín hiệu giao thông", "vi phạm giao thông",
            "bằng lái xe", "giấy phép lái xe", "đăng ký xe",
            "kiểm định xe", "bảo hiểm xe", "phí đường bộ",
            "tốc độ", "nồng độ cồn", "ma túy lái xe",
            "đường cao tốc", "quốc lộ", "tỉnh lộ"
        ]
        
        # Kiểm tra title và content
        title = doc.get('title', '').lower()
        content = doc.get('content', '').lower()
        field = doc.get('field', '').lower()
        
        # Ưu tiên field trước
        if 'giao thông' in field:
            return True
            
        # Kiểm tra title
        for term in traffic_terms:
            if term in title:
                return True
                
        # Kiểm tra content (ít nhất 2 từ khóa)
        content_matches = sum(1 for term in traffic_terms if term in content)
        return content_matches >= 2

    def crawl_groundtruth_links(self, num_pages=50):
        """Crawl groundtruth data cho evaluation"""
        base_url = "https://thuvienphapluat.vn/page/tim-van-ban.aspx?keyword={key}&area=0&type=0&status=0&lan=1&org=0&signer=0&match=True&sort=1&bdate=01/01/2025&edate=11/10/2025&page={page}"
        session = requests.Session()
        session.headers.update(Config.HEADERS)
        all_links = []
        results = []
        
        keywords = ["giao thông", "an toàn giao thông", "thuế", "tài chính", "lao động", "xã hội", "kinh tế"]
        
        for key in keywords:
            self.log(f"Crawling groundtruth cho từ khóa: {key}")
            key_encoded = quote_plus(key)
            
            for page_num in range(1, num_pages + 1):
                url = base_url.format(key=key_encoded, page=page_num)
                try:
                    resp = session.get(url, timeout=20)
                    resp.raise_for_status()
                    soup = BeautifulSoup(resp.text, "html.parser")
                    
                    # Tìm links trong các div kết quả
                    for div in soup.find_all("div", class_="content-0"):
                        left_col = div.find("div", class_="left-col")
                        if not left_col:
                            continue
                        nq = left_col.find("div", class_="nq")
                        if not nq:
                            continue
                        p_title = nq.find("p", class_="nqTitle")
                        if not p_title:
                            continue
                        a_tag = p_title.find("a", href=True)
                        if a_tag:
                            link = a_tag["href"]
                            if not link.startswith('http'):
                                link = f"https://thuvienphapluat.vn{link}"
                            if link not in all_links:
                                all_links.append(link)
                    
                    self.log(f"Trang {page_num}: Tìm thấy {len(all_links)} link tổng cộng.")
                    time.sleep(1)
                    
                except Exception as e:
                    self.log(f"Lỗi khi tải trang {page_num}: {e}")

                if len(all_links) >= 500:
                    break

        # Crawl nội dung từng link
        for i, link in enumerate(all_links[:500]):
            try:
                self.log(f"Crawling groundtruth {i+1}/{min(len(all_links), 500)}: {link}")
                doc_resp = session.get(link, timeout=20)
                doc_resp.raise_for_status()
                doc_soup = BeautifulSoup(doc_resp.text, "html.parser")
                
                content_div = doc_soup.find("div", class_="content1")
                if content_div:
                    for script in content_div(["script", "style"]):
                        script.decompose()
                    content = content_div.get_text(separator=" ", strip=True)
                else:
                    content = "Không xác định"
                    
                results.append({
                    "url": link,
                    "content": content
                })
                
            except Exception as e:
                self.log(f"Lỗi khi crawl {link}: {e}")

        self.log(f"Đã crawl {len(results)} groundtruth documents.")
        return results


    def retry_blocked_documents(self, input_file=None, max_retry=None):
        """Retry các documents bị blocked từ lần crawl trước"""
        if input_file is None:
            input_file = os.path.join(Config.RAW_DATA_DIR, "crawled_documents.json")
        
        self.log("Bắt đầu retry blocked documents...")
        
        # Load previous results
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            self.log(f"Lỗi đọc file {input_file}: {e}")
            return {"retried": 0, "success": 0, "still_blocked": 0}
        
        # Find blocked documents
        blocked_docs = [d for d in data.get('documents', []) if d.get('status') == 'blocked']
        if not blocked_docs:
            self.log("Không tìm thấy documents bị blocked để retry")
            return {"retried": 0, "success": 0, "still_blocked": 0}
        
        if max_retry:
            blocked_docs = blocked_docs[:max_retry]
        
        self.log(f"Tìm thấy {len(blocked_docs)} documents bị blocked, bắt đầu retry...")
        
        # Retry each blocked document
        retry_results = {"retried": 0, "success": 0, "still_blocked": 0}
        
        for i, doc in enumerate(blocked_docs, 1):
            url = doc.get('url')
            self.log(f"Retry {i}/{len(blocked_docs)}: {url}")
            
            # Try to crawl again
            new_doc = self._crawl_document_with_retry(url)
            retry_results["retried"] += 1
            
            if new_doc and new_doc.get('status') == 'success':
                # Update the document in original data
                for j, orig_doc in enumerate(data['documents']):
                    if orig_doc.get('url') == url:
                        data['documents'][j] = new_doc
                        break
                retry_results["success"] += 1
                self.log(f"  ✓ Success: {url}")
            else:
                retry_results["still_blocked"] += 1
                self.log(f"  ✗ Still blocked: {url}")
            
            # Delay between retries
            time.sleep(Config.DELAY_BETWEEN_REQUESTS * 2)
        
        # Save updated results
        output_file = input_file.replace('.json', '_retried.json')
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.log(f"Đã lưu kết quả retry tại: {output_file}")
        except Exception as e:
            self.log(f"Lỗi lưu file: {e}")
        
        # Print summary
        self.log(f"\nKẾT QUẢ RETRY:")
        self.log(f"  Đã retry: {retry_results['retried']}")
        self.log(f"  Thành công: {retry_results['success']}")
        self.log(f"  Vẫn bị chặn: {retry_results['still_blocked']}")
        self.log(f"  Tỷ lệ thành công retry: {retry_results['success']/retry_results['retried']*100:.1f}%")
        
        return retry_results


def crawl_groundtruth_links_standalone(num_pages=50):
    """Standalone function để crawl groundtruth"""
    crawler = ThuvienCrawlerAgent()
    return crawler.crawl_groundtruth_links(num_pages)


if __name__ == "__main__":
    print("TEST SIMPLE CRAWLER - TÍCH HỢP VÀO FILE CHÍNH")
    print("=" * 60)
    
    crawler = ThuvienCrawlerAgent()
    
    # Test 1: Simple crawl method
    print("\nTEST 1: Simple Crawl Method (2 trang, 10 văn bản/trang)")
    try:
        results1 = crawler.process({
            "keyword": "giao thông",
            "max_pages": 2,
            "docs_per_page": 10,
            "max_docs": 20,
            "use_simple_crawl": True  # ← Sử dụng simple crawl
        })
        
        print(f" Simple crawl hoạt động OK!")
        print(f"   Crawl được: {results1['total_crawled']} văn bản")
        print(f"   Phương pháp: {results1.get('crawl_method', 'N/A')}")
        
        if results1['documents']:
            doc = results1['documents'][0]
            print(f"   Văn bản đầu: {doc.get('title', 'N/A')[:50]}...")
            print(f"   Có content_html: {'Có' if doc.get('content_html') else 'Không'}")
            print(f"   Độ dài content: {doc.get('content_length', 0)} ký tự")
        
    except Exception as e:
        print(f" Simple crawl gây lỗi: {e}")
    
    # Test 2: So sánh với advanced crawl
    print("\nTEST 2: Advanced Crawl Method (so sánh)")
    try:
        crawler2 = ThuvienCrawlerAgent()
        results2 = crawler2.process({
            "keyword": "giao thông",
            "max_pages": 1,
            "docs_per_page": 5,
            "max_docs": 5,
            "use_simple_crawl": False  # ← Sử dụng advanced crawl
        })
        
        print(f" Advanced crawl hoạt động OK!")
        print(f"   Crawl được: {results2['total_crawled']} văn bản")
        print(f"   Phương pháp: {results2.get('crawl_method', 'N/A')}")
        
    except Exception as e:
        print(f" Advanced crawl gây lỗi: {e}")
    
    # Test 3: Test session restart
    print(f"\nTEST 3: Test Session Management")
    try:
        crawler3 = ThuvienCrawlerAgent()
        # Giả lập nhiều request
        crawler3.request_count = 55  # Trigger restart
        
        results3 = crawler3.simple_crawl_search_results("thuế", max_pages=1, docs_per_page=3)
        
        print(f" Session management hoạt động OK!")
        print(f"   Crawl được: {len(results3)} văn bản")
        print(f"   Request count sau restart: {crawler3.request_count}")
        
    except Exception as e:
        print(f" Session management gây lỗi: {e}")
    
    print(f"\n" + "=" * 60)
    print(f"KẾT LUẬN: Simple Crawl đã được tích hợp thành công!")
    print(f"Sử dụng: use_simple_crawl=True trong search_params")
    print(f"Chạy main.py để sử dụng đầy đủ:")
    print(f"   python main.py")

    # -----------------
    # HYBRID helpers
    # -----------------
    def _is_bad_doc(self, d: dict) -> bool:
        """Đánh dấu doc 'xấu': tiêu đề login, nội dung quá ngắn, thiếu content_html."""
        title = (d.get("title") or "").strip().lower()
        clen = int(d.get("content_length") or 0)
        if "đăng nhập" in title:
            return True
        if clen < 500:  # ngưỡng tuỳ chỉnh
            return True
        if "content_html" in d and not d.get("content_html"):
            return True
        return False

    def _needs_fallback(self, docs: list) -> bool:
        """Quyết định có cần fallback Playwright không."""
        if not docs:
            return True
        bad = sum(1 for d in docs if self._is_bad_doc(d))
        ratio = bad / max(1, len(docs))
        # nếu tỉ lệ doc xấu cao -> fallback
        return ratio >= 0.4

    def _hybrid_crawl(self, keyword: str, max_pages: int, docs_per_page: int, max_docs: int, headless: bool):
        """Chạy simple trước → nếu xấu thì fallback Playwright để tăng Recall."""
        self.log("[HYBRID] Bắt đầu SIMPLE trước...")
        simple_docs = self.simple_crawl_search_results(
            keyword=keyword,
            max_pages=max_pages,
            docs_per_page=docs_per_page
        )

        if not self._needs_fallback(simple_docs):
            self.log(f"[HYBRID] Simple đủ tốt (docs={len(simple_docs)}). Không cần fallback.")
            return simple_docs[:max_docs]

        self.log(f"[HYBRID] Simple chưa đạt (docs tốt ít). Fallback sang PLAYWRIGHT...")
        # 1) Dò URL qua Playwright (click phân trang)
        urls = self._find_document_urls_paginated(
            keyword=keyword,
            max_pages=max_pages,
            docs_per_page=docs_per_page,
            max_docs=max_docs,
            headless=headless
        )

        # 2) Crawl chi tiết các URL mới (không trùng với simple)
        existing = {d.get("url") for d in simple_docs if d.get("url")}
        merged = list(simple_docs)
        for i, url in enumerate(urls):
            if len(merged) >= max_docs:
                break
            if url in existing:
                continue
            self.log(f"[HYBRID] Crawl bổ sung (Playwright) {i+1}/{len(urls)}: {url}")
            d = self._crawl_document_detail(url)
            if d:
                merged.append(d)
                existing.add(url)
            time.sleep(Config.DELAY_BETWEEN_REQUESTS)

        self.log(f"[HYBRID] Hoàn tất. Simple={len(simple_docs)}, +Playwright={len(merged)-len(simple_docs)}, tổng={len(merged)}")
        return merged[:max_docs]
