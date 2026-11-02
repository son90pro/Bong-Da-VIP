import json
import re
import requests

def parse_slug_to_title(href_str):
    if not href_str:
        return ""
    parts = [p for p in href_str.strip('/').split('/') if p]
    slug = parts[-1] if parts else ""
    if not slug or "truc-tiep" in slug:
        if len(parts) >= 2:
            slug = parts[-1]
        else:
            return ""

    time_str = ""
    match_slug = slug
    time_match = re.search(r'luc-(\d{2})(\d{2})-ngay-(\d{2})-(\d{2})-(\d{4})', slug)
    if time_match:
        h, m, d, mo, y = time_match.groups()
        time_str = f"{d}/{mo}/{y} {h}:{m}"
        match_slug = re.sub(r'-luc-\d+-ngay-[\d-]+', '', slug).strip('-')

    team_name = match_slug.replace('-', ' ').title()
    team_name = re.sub(r'\bVs\b', 'vs', team_name)

    if time_str:
        return f"[{time_str}] {team_name}"
    return team_name

def generate_m3u_and_json():
    target_url = "https://tinyurl.com/xoilacz3" 
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        print("Đang kết nối lấy dữ liệu...")
        response = requests.get(target_url, headers=headers, timeout=30, allow_redirects=True)
        
        if response.status_code == 200:
            data = response.json()
            
            with open('xoilac.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("Đã lưu file xoilac.json thành công!")
            
            m3u_content = "#EXTM3U x-tvg-url=\"\"\n"
            count = 0
            seen_links = set()

            providers = []
            if isinstance(data, dict):
                if "providers" in data and isinstance(data["providers"], list):
                    providers = data["providers"]
                else:
                    found_lists = [v for v in data.values() if isinstance(v, list)]
                    if found_lists:
                        providers = [{"name": k, "matches": v} for k, v in data.items() if isinstance(v, list)]
                    else:
                        providers = [data]
            elif isinstance(data, list):
                providers = data

            for prov in providers:
                if not isinstance(prov, dict):
                    continue
                
                prov_name = prov.get("name") or prov.get("title") or prov.get("provider_name") or "Kênh Trực Tiếp"
                prov_logo = prov.get("logo") or prov.get("icon") or ""
                
                matches = []
                for k in ["matches", "list", "items", "data", "match_list", "schedule", "channels", "matchs", "match", "content"]:
                    if k in prov and isinstance(prov[k], list):
                        matches = prov[k]
                        break
                
                if not matches:
                    for val in prov.values():
                        if isinstance(val, list):
                            matches = val
                            break

                if not matches:
                    matches = [prov]

                # Bước 1: Quét toàn bộ danh sách để thu thập các trận đấu (có tên đội / slug)
                match_pool = []
                for match in matches:
                    if not isinstance(match, dict):
                        continue
                    
                    home = match.get("home_team") or match.get("home") or ""
                    away = match.get("away_team") or match.get("away") or ""
                    match_title = ""
                    
                    if home and away:
                        match_title = f"{home} vs {away}"
                    else:
                        raw_t = match.get("title") or match.get("name") or match.get("match_name") or ""
                        if raw_t and not any(kw in raw_t.lower() for kw in ['url', 'href', 'logo', 'referer', 'http', 'live']):
                            match_title = raw_t

                    if not match_title:
                        href = match.get("href") or match.get("url_info") or ""
                        match_title = parse_slug_to_title(href)

                    logo = match.get("home_logo") or match.get("logo") or match.get("icon") or prov_logo
                    
                    if match_title and match_title != "Trận đấu trực tiếp":
                        match_pool.append({"title": match_title, "logo": logo})

                # Bước 2: Quét toàn bộ để lấy các luồng stream và ghép cặp thông minh
                match_idx = 0
                for match in matches:
                    if not isinstance(match, dict):
                        continue

                    # Lấy tên BLV hoặc tiêu đề hiển thị cho server phát
                    blv_name = match.get("title") or match.get("name") or match.get("match_name") or match.get("blv") or ""
                    if any(kw in blv_name.lower() for kw in ['url', 'href', 'logo', 'referer', 'http', 'truc-tiep']):
                        blv_name = ""

                    # Thu thập các link stream (.m3u8)
                    streams = []
                    for dk in ["url", "stream_url", "m3u8", "source"]:
                        val = match.get(dk)
                        if isinstance(val, str) and val.startswith("http"):
                            streams.append(val)

                    for sk in ["streams", "links", "servers", "sources"]:
                        arr = match.get(sk)
                        if isinstance(arr, list):
                            for s in arr:
                                if isinstance(s, str) and s.startswith("http"):
                                    streams.append(s)
                                elif isinstance(s, dict):
                                    s_url = s.get("url") or s.get("link") or s.get("m3u8") or ""
                                    if s_url.startswith("http"):
                                        streams.append(s_url)

                    if not streams:
                        for sub_k, sub_v in match.items():
                            if isinstance(sub_v, str) and sub_v.startswith("http") and (".m3u8" in sub_v or ".ts" in sub_v or "live" in sub_v):
                                streams.append(sub_v)

                    referer = match.get("Referer") or match.get("referer") or ""
                    ua = match.get("user_agent") or "Mozilla/5.0"

                    for s_url in streams:
                        s_lower = s_url.lower()
                        # Chặn tuyệt đối ảnh và link trang chủ rác
                        if any(ext in s_lower for ext in ['.png', '.jpg', '.jpeg', '.webp', '.gif']) or 'almafestival.info' in s_lower:
                            continue

                        if s_url not in seen_links:
                            seen_links.add(s_url.strip())
                            
                            # Xác định tên trận đấu và logo tương ứng trong pool
                            current_match_title = f"{prov_name} Trực Tiếp"
                            current_logo = prov_logo
                            
                            if match_pool:
                                current_match_title = match_pool[match_idx % len(match_pool)]["title"]
                                current_logo = match_pool[match_idx % len(match_pool)]["logo"] or prov_logo
                                match_idx += 1

                            # Gắn tên BLV vào tiêu đề nếu có
                            display_title = current_match_title
                            if blv_name and blv_name not in display_title:
                                display_title += f" [{blv_name}]"

                            m3u_content += f"#EXTINF:-1 tvg-logo=\"{current_logo}\" group-title=\"{prov_name}\",{display_title}\n"
                            
                            final_link = s_url.strip()
                            if referer:
                                final_link = f"{s_url.strip()}|User-Agent={ua}&Referer={referer.strip()}"
                            elif ua != "Mozilla/5.0":
                                final_link = f"{s_url.strip()}|User-Agent={ua}"
                                
                            m3u_content += f"{final_link}\n"
                            count += 1

            with open('playlist.m3u', 'w', encoding='utf-8') as f:
                f.write(m3u_content)
                
            print(f"Đã tạo xong file playlist.m3u với {count} luồng trận đấu đầy đủ thông tin chuẩn xác!")
            
        else:
            print(f"Lỗi HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"Lỗi: {e}")

if __name__ == "__main__":
    generate_m3u_and_json()
    ạo xong file playlist.m3u với {count} luồng trận đấu đầy đủ thông tin!")
            
        else:
            print(f"Lỗi HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")

if __name__ == "__main__":
    generate_m3u_and_json()
    
