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
                
                # Thu thập toàn bộ các node con theo dạng danh sách phẳng tuần tự
                flat_items = []
                def flatten_nodes(node):
                    if isinstance(node, list):
                        for sub in node:
                            flatten_nodes(sub)
                    elif isinstance(node, dict):
                        flat_items.append(node)
                        for val in node.values():
                            if isinstance(val, (list, dict)):
                                flatten_nodes(val)

                flatten_nodes(prov)

                # Duyệt tuần tự để lưu ngữ cảnh trận đấu và logo gần nhất
                current_match_title = f"{prov_name} Trực Tiếp"
                current_logo = prov_logo

                for item in flat_items:
                    # 1. Cập nhật ngữ cảnh tên trận / thời gian từ slug href hoặc tên đội
                    href = item.get("href") or item.get("url_info") or ""
                    slug_title = parse_slug_to_title(href)
                    if slug_title:
                        current_match_title = slug_title

                    home = item.get("home_team") or item.get("home") or ""
                    away = item.get("away_team") or item.get("away") or ""
                    if home and away:
                        current_match_title = f"{home} vs {away}"
                    else:
                        t_val = item.get("title") or item.get("name") or item.get("match_name") or ""
                        if t_val and " vs " in t_val.lower():
                            current_match_title = t_val

                    # Cập nhật logo nếu item hiện tại chứa logo
                    logo_val = item.get("home_logo") or item.get("logo") or item.get("icon") or ""
                    if logo_val and isinstance(logo_val, str) and logo_val.startswith("http") and not any(ext in logo_val.lower() for ext in ['.m3u8', '.ts']):
                        current_logo = logo_val

                    # 2. Kiểm tra xem item này có chứa luồng phát stream (.m3u8) không
                    streams = []
                    for u_key in ["url", "stream_url", "m3u8", "link"]:
                        val = item.get(u_key)
                        if isinstance(val, str) and val.startswith("http"):
                            streams.append(val)

                    for sk in ["streams", "links", "servers", "sources"]:
                        arr = item.get(sk)
                        if isinstance(arr, list):
                            for s in arr:
                                if isinstance(s, str) and s.startswith("http"):
                                    streams.append(s)
                                elif isinstance(s, dict):
                                    s_url = s.get("url") or s.get("link") or s.get("m3u8") or ""
                                    if s_url.startswith("http"):
                                        streams.append(s_url)

                    if not streams:
                        for sub_k, sub_v in item.items():
                            if isinstance(sub_v, str) and sub_v.startswith("http") and (".m3u8" in sub_v or ".ts" in sub_v or "live" in sub_v):
                                streams.append(sub_v)

                    # Nếu tìm thấy stream, ghép chung với ngữ cảnh tên trận, logo và tên BLV/Server hiện tại
                    if streams:
                        item_title_raw = item.get("title") or item.get("name") or item.get("blv") or ""
                        blv_tag = ""
                        if item_title_raw and not any(kw in item_title_raw.lower() for kw in ['url', 'href', 'logo', 'http', 'truc-tiep']):
                            blv_tag = item_title_raw

                        for s_url in streams:
                            s_lower = s_url.lower()
                            if any(ext in s_lower for ext in ['.png', '.jpg', '.jpeg', '.webp', '.gif']) or 'almafestival.info' in s_lower:
                                continue

                            if s_url not in seen_links:
                                seen_links.add(s_url)

                                final_title = current_match_title
                                if blv_tag and blv_tag not in final_title:
                                    final_title += f" [{blv_tag}]"

                                m3u_content += f"#EXTINF:-1 tvg-logo=\"{current_logo}\" group-title=\"{prov_name}\",{final_title}\n"
                                
                                referer = item.get("Referer") or item.get("referer") or ""
                                ua = item.get("user_agent") or "Mozilla/5.0"
                                
                                final_link = s_url
                                if referer:
                                    final_link = f"{s_url}|User-Agent={ua}&Referer={referer}"
                                elif ua != "Mozilla/5.0":
                                    final_link = f"{s_url}|User-Agent={ua}"
                                    
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
    
