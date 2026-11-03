import json
import re
import requests

def get_sport_icon(category, title=""):
    text = f"{category} {title}".lower()
    if any(k in text for k in ['tennis', 'quần vợt', 'cirstea', 'timofeeva', 'gibson', 'tsitsipas', 'djokovic', 'shelton', 'paul']):
        return "🥎"
    elif any(k in text for k in ['basketball', 'bóng rổ', 'nba', 'sharks', 'liaoning', 'parma', 'bayern']):
        return "🏀"
    elif any(k in text for k in ['volleyball', 'bóng chuyền', 'ibk', 'ziraat']):
        return "🏐"
    elif any(k in text for k in ['lol', 'game', 'esports', 'top esports', 'gen.g', 'dplus', 'karmine']):
        return "🎮"
    else:
        return "⚽"

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
            
            m3u_content = "#EXTM3U\n\n"
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
                
                prov_name = prov.get("name") or prov.get("title") or prov.get("provider_name") or ""
                # Chỉ lọc Xôi Lạc Z TV theo đúng yêu cầu làm từng nguồn 1
                if "xôi lạc" not in prov_name.lower() and "xoilac" not in prov_name.lower():
                    continue
                
                group_title = "Xôi Lạc Z TV"
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

                def process_node(node):
                    nonlocal count, m3u_content, seen_links
                    if isinstance(node, list):
                        for item in node:
                            process_node(item)
                    elif isinstance(node, dict):
                        home = node.get("home_team") or node.get("home") or ""
                        away = node.get("away_team") or node.get("away") or ""
                        match_title = node.get("title") or node.get("name") or node.get("match_name") or ""
                        
                        if home and away:
                            teams_str = f"{home} vs {away}"
                        elif " vs " in match_title.lower():
                            teams_str = match_title
                        else:
                            href = node.get("href") or node.get("url_info") or ""
                            if href:
                                parts = [p for p in href.strip('/').split('/') if p]
                                slug = parts[-1] if parts else ""
                                slug_clean = re.sub(r'-luc-\d+-ngay-[\d-]+', '', slug).strip('-')
                                slug_clean = re.sub(r'-[\d]{2}-[\d]{2}-[\d]{4}', '', slug_clean).strip('-')
                                slug_title = slug_clean.replace('-', ' ').title()
                                if ' vs ' in slug_title.lower():
                                    teams_str = slug_title
                                else:
                                    teams_str = match_title or "Trực Tiếp"
                            else:
                                teams_str = match_title or "Trực Tiếp"

                        time_val = node.get("time") or node.get("start_time") or node.get("hour") or ""
                        combined = f"{node.get('href', '')} {match_title} {time_val}"
                        
                        time_match = re.search(r'(\d{2}[:h]\d{2})', combined)
                        time_str = time_match.group(1).replace('h', ':') if time_match else (time_val if time_val else "14:00")
                        
                        date_match = re.search(r'(\d{2}[-/]\d{2})', combined)
                        date_str = date_match.group(1).replace('-', '/') if date_match else "03/11"

                        status_dot = "🟢"
                        sport_icon = get_sport_icon(prov_name, teams_str)
                        logo = node.get("home_logo") or node.get("logo") or node.get("icon") or prov_logo

                        streams = []
                        for u_key in ["url", "stream_url", "m3u8", "link", "flv"]:
                            val = node.get(u_key)
                            if isinstance(val, str) and val.startswith("http"):
                                streams.append((val, "VIC"))

                        for sk in ["streams", "links", "servers", "sources"]:
                            arr = node.get(sk)
                            if isinstance(arr, list):
                                for s in arr:
                                    if isinstance(s, str) and s.startswith("http"):
                                        streams.append((s, ""))
                                    elif isinstance(s, dict):
                                        s_url = s.get("url") or s.get("link") or s.get("m3u8") or s.get("flv") or ""
                                        s_name = s.get("name") or s.get("title") or ""
                                        if s_url.startswith("http"):
                                            streams.append((s_url, s_name))

                        if not streams:
                            for sub_k, sub_v in node.items():
                                if isinstance(sub_v, str) and sub_v.startswith("http") and ("live" in sub_v or ".flv" in sub_v or ".m3u8" in sub_v):
                                    streams.append((sub_v, ""))

                        for idx, (s_url, s_name) in enumerate(streams):
                            if s_url not in seen_links:
                                seen_links.add(s_url)

                                tag = s_name.upper() if s_name else "VIC"
                                if idx % 2 == 1:
                                    tag = f"HD {tag}" if not tag.startswith("HD") else tag
                                
                                display_title = f"{status_dot} {time_str} {date_str} {sport_icon} {teams_str} ({tag})"

                                m3u_content += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group_title}" , {display_title}\n'
                                m3u_content += '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36\n'
                                m3u_content += '#EXTVLCOPT:http-referrer=https://xlz.domainkqt.cc/\n'
                                m3u_content += f'{s_url}\n\n'
                                count += 1

                        for k, v in node.items():
                            if isinstance(v, (list, dict)):
                                process_node(v)

                for m in matches:
                    process_node(m)

            with open('playlist.m3u', 'w', encoding='utf-8') as f:
                f.write(m3u_content)
                
            print(f"Đã tạo xong Xôi Lạc Z TV với {count} luồng chuẩn xác mẫu yêu cầu!")
            
        else:
            print(f"Lỗi HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"Lỗi: {e}")

if __name__ == "__main__":
    generate_m3u_and_json()
