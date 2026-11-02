import json
import re
import requests

def parse_slug_to_info(href_str):
    if not href_str:
        return "", ""
    parts = [p for p in href_str.strip('/').split('/') if p]
    slug = parts[-1] if parts else ""
    if not slug or "truc-tiep" in slug:
        if len(parts) >= 2:
            slug = parts[-1]
        else:
            return "", ""

    time_str = ""
    match_slug = slug
    # Bóc tách giờ phút và ngày tháng năm từ slug
    time_match = re.search(r'luc-(\d{2})(\d{2})-ngay-(\d{2})-(\d{2})-(\d{4})', slug)
    if time_match:
        h, m, d, mo, y = time_match.groups()
        time_str = f"{d}/{mo} {h}:{m}" # Hiển thị dạng chuẩn gọn gàng ngày/tháng giờ:phút
        match_slug = re.sub(r'-luc-\d+-ngay-[\d-]+', '', slug).strip('-')

    team_name = match_slug.replace('-', ' ').title()
    team_name = re.sub(r'\bVs\b', 'vs', team_name)

    return time_str, team_name

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

                # Quét và phẳng hóa cấu trúc để lấy toàn bộ dữ liệu trận đấu và luồng phát
                flat_nodes = []
                def extract_nodes(node):
                    if isinstance(node, list):
                        for sub in node:
                            extract_nodes(sub)
                    elif isinstance(node, dict):
                        flat_nodes.append(node)
                        for val in node.values():
                            if isinstance(val, (list, dict)):
                                extract_nodes(val)

                for m in matches:
                    extract_nodes(m)

                # Lưu vết thông tin trận đấu gần nhất để ghép cặp tuần tự
                latest_time = ""
                latest_match_title = ""
                latest_logo = prov_logo

                for node in flat_nodes:
                    if not isinstance(node, dict):
                        continue

                    # 1. Trích xuất thời gian và tên cặp đấu từ href hoặc các trường thông tin
                    href = node.get("href") or node.get("url_info") or ""
                    t_str, m_title = parse_slug_to_info(href)
                    if t_str:
                        latest_time = t_str
                    if m_title:
                        latest_match_title = m_title

                    home = node.get("home_team") or node.get("home") or ""
                    away = node.get("away_team") or node.get("away") or ""
                    if home and away:
                        latest_match_title = f"{home} vs {away}"

                    # Cập nhật logo
                    lg = node.get("home_logo") or node.get("logo") or node.get("icon") or ""
                    if lg and isinstance(lg, str) and lg.startswith("http") and not any(ext in lg.lower() for ext in ['.m3u8', '.ts']):
                        latest_logo = lg

                    # 2. Thu thập các luồng phát stream (.m3u8)
                    streams = []
                    for u_key in ["url", "stream_url", "m3u8", "link"]:
                        val = node.get(u_key)
                        if isinstance(val, str) and val.startswith("http"):
                            streams.append(val)

                    for sk in ["streams", "links", "servers", "sources"]:
                        arr = node.get(sk)
                        if isinstance(arr, list):
                            for s in arr:
                                if isinstance(s, str) and s.startswith("http"):
                                    streams.append(s)
                                elif isinstance(s, dict):
                                    s_url = s.get("url") or s.get("link") or s.get("m3u8") or ""
                                    if s_url.startswith("http"):
                                        streams.append(s_url)

                    if not streams:
                        for sub_k, sub_v in node.items():
                            if isinstance(sub_v, str) and sub_v.startswith("http") and (".m3u8" in sub_v or ".ts" in sub_v or "live" in sub_v):
                                streams.append(sub_v)

                    # Lấy tên BLV hoặc tên server từ title/name của node
                    raw_title = node.get("title") or node.get("name") or node.get("blv") or ""
                    blv_name = ""
                    if raw_title and not any(kw in raw_title.lower() for kw in ['url', 'href', 'logo', 'http', 'truc-tiep']):
                        blv_name = raw_title

                    for s_url in streams:
                        s_lower = s_url.lower()
                        if any(ext in s_lower for ext in ['.png', '.jpg', '.jpeg', '.webp', '.gif']) or 'almafestival.info' in s_lower:
                            continue

                        if s_url not in seen_links:
                            seen_links.add(s_url)

                            # Xây dựng tiêu đề hoàn chỉnh: [Giờ Ngày] Tên Đội [Tên BLV]
                            display_title = ""
                            if latest_time:
                                display_title += f"{latest_time} "
                            
                            display_title += latest_match_title if latest_match_title else f"{prov_name} Trực Tiếp"

                            if blv_name and blv_name.lower() not in display_title.lower():
                                display_title += f" ({blv_name})"

                            final_logo = latest_logo if latest_logo else prov_logo

                            m3u_content += f"#EXTINF:-1 tvg-logo=\"{final_logo}\" group-title=\"{prov_name}\",{display_title}\n"
                            
                            referer = node.get("Referer") or node.get("referer") or ""
                            ua = node.get("user_agent") or "Mozilla/5.0"
                            
                            final_link = s_url
                            if referer:
                                final_link = f"{s_url}|User-Agent={ua}&Referer={referer}"
                            elif ua != "Mozilla/5.0":
                                final_link = f"{s_url}|User-Agent={ua}"
                                
                            m3u_content += f"{final_link}\n"
                            count += 1

            with open('playlist.m3u', 'w', encoding='utf-8') as f:
                f.write(m3u_content)
                
            print(f"Đã tạo xong file playlist.m3u với {count} luồng trận đấu hiển thị đầy đủ thông tin!")
            
        else:
            print(f"Lỗi HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"Lỗi: {e}")

if __name__ == "__main__":
    generate_m3u_and_json()
    
