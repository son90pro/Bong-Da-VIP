import json
import re
import requests

def clean_text(text):
    if not text:
        return ""
    garbage = ['bee', 'hấu', 'tỵ', 'redbull', 'quốc khánh', 'typn', 'a páo', 'thạch tú', 
               'cr bưởi', 'a bệu', 'xuân tóc đỏ', 'mp3', 'xuân son', '5 lửa', 'tuấn cùi', 
               'tạ biên giới', 'lão lâm', 'loka', 'người cá', 'curry', 'kenchu', 'nhà đài',
               'tencent', 'alibaba']
    cleaned = text.strip()
    if cleaned.lower() in garbage or (len(cleaned) <= 3 and not any(c.isdigit() for c in cleaned)):
        return ""
    return cleaned

def get_sport_icon(category_name, team_or_title=""):
    text = f"{category_name} {team_or_title}".lower()
    if any(k in text for k in ['tennis', 'quần vợt', 'bellucci', 'sonego']):
        return "🎾"
    elif any(k in text for k in ['basketball', 'bóng rổ', 'nba', 'cavaliers', 'pacers', 'celtics', 'lakers', 'denver']):
        return "🏀"
    elif any(k in text for k in ['volleyball', 'bóng chuyền', 'ziraat']):
        return "🏐"
    else:
        return "⚽"

def parse_xoilac_node(node):
    href = node.get("href") or node.get("url_info") or ""
    raw_title = node.get("title") or node.get("name") or node.get("match_name") or ""
    
    time_str = ""
    date_str = ""
    match_title = ""

    combined = f"{href} {raw_title}"
    
    time_match = re.search(r'(?:luc-)?(\d{2})[:h](\d{2})', combined.lower())
    if time_match:
        h, m = time_match.groups()
        time_str = f"{h}:{m}"
    else:
        luc_match = re.search(r'luc-(\d{2})(\d{2})', combined.lower())
        if luc_match:
            h, m = luc_match.groups()
            time_str = f"{h}:{m}"

    date_match = re.search(r'(?:ngay-)?(\d{2})[-/](\d{2})', combined)
    if date_match:
        d, mo = date_match.groups()
        date_str = f"{d}/{mo}"

    if href:
        parts = [p for p in href.strip('/').split('/') if p]
        slug = parts[-1] if parts else ""
        if slug and not slug.startswith('channel') and not slug.isdigit():
            slug_clean = re.sub(r'-luc-\d+-ngay-[\d-]+', '', slug).strip('-')
            slug_clean = re.sub(r'-[\d]{2}-[\d]{2}-[\d]{4}', '', slug_clean).strip('-')
            slug_clean = re.sub(r'-id\d+', '', slug_clean)
            slug_title = slug_clean.replace('-', ' ').title()
            slug_title = re.sub(r'\bVs\b', 'vs', slug_title)
            if ' vs ' in slug_title.lower() or len(slug_title.split()) >= 3:
                match_title = slug_title

    home = node.get("home_team") or node.get("home") or ""
    away = node.get("away_team") or node.get("away") or ""
    if home and away:
        match_title = f"{home} vs {away}"

    if not match_title and raw_title:
        ct = clean_text(raw_title)
        if ct and not any(kw in ct.lower() for kw in ['live', 'trực tiếp', 'channel', 'server']):
            match_title = ct

    match_title = re.sub(r'\b(live|trực tiếp)\b', '', match_title, flags=re.IGNORECASE).strip(' -')

    time_prefix = ""
    if date_str and time_str:
        time_prefix = f"🟢 {date_str} {time_str}"
    elif time_str:
        time_prefix = f"🟢 {time_str}"
    elif date_str:
        time_prefix = f"🟢 {date_str}"
    else:
        time_prefix = "🟢 LIVE"

    return time_prefix, match_title

def generate_m3u_and_json():
    target_url = "https://tinyurl.com/xoilacz3" 
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        print("Đang kết nối lấy dữ liệu Xôi Lạc Z...")
        response = requests.get(target_url, headers=headers, timeout=30, allow_redirects=True)
        
        if response.status_code == 200:
            data = response.json()
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
                
                prov_name = prov.get("name") or prov.get("title") or prov.get("provider_name") or "Xôi Lạc Z TV"
                if "xôi lạc" not in prov_name.lower():
                    continue

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

                def process_node(node, cur_time_prefix="", cur_title="", cur_logo=prov_logo):
                    nonlocal count, m3u_content, seen_links
                    if isinstance(node, list):
                        for item in node:
                            process_node(item, cur_time_prefix, cur_title, cur_logo)
                    elif isinstance(node, dict):
                        href = node.get("href") or node.get("url_info") or ""
                        raw_t = node.get("title") or node.get("name") or node.get("match_name") or ""
                        
                        t_prefix, m_title = parse_xoilac_node(node)
                        if t_prefix and t_prefix != "🟢 LIVE":
                            cur_time_prefix = t_prefix
                        if m_title:
                            cur_title = m_title

                        lg = node.get("home_logo") or node.get("logo") or node.get("icon") or ""
                        if lg and isinstance(lg, str) and lg.startswith("http") and not any(ext in lg.lower() for ext in ['.m3u8', '.ts', 'playlist']):
                            cur_logo = lg

                        streams = []
                        for u_key in ["url", "stream_url", "m3u8", "link"]:
                            val = node.get(u_key)
                            if isinstance(val, str) and val.startswith("http"):
                                if not any(ext in val.lower() for ext in ['.png', '.jpg', '.jpeg', '.webp', '.gif', 'image/small']):
                                    streams.append((val, raw_t))

                        for sk in ["streams", "links", "servers", "sources"]:
                            arr = node.get(sk)
                            if isinstance(arr, list):
                                for s in arr:
                                    if isinstance(s, str) and s.startswith("http"):
                                        if not any(ext in s.lower() for ext in ['.png', '.jpg', '.jpeg', '.webp', '.gif', 'image/small']):
                                            streams.append((s, ""))
                                    elif isinstance(s, dict):
                                        s_url = s.get("url") or s.get("link") or s.get("m3u8") or ""
                                        s_name = s.get("name") or s.get("title") or ""
                                        if s_url.startswith("http") and not any(ext in s_url.lower() for ext in ['.png', '.jpg', '.jpeg', '.webp', '.gif', 'image/small']):
                                            streams.append((s_url, s_name))

                        if not streams:
                            for sub_k, sub_v in node.items():
                                if isinstance(sub_v, str) and sub_v.startswith("http") and (".m3u8" in sub_v or ".ts" in sub_v or "live" in sub_v):
                                    if not any(ext in sub_v.lower() for ext in ['.png', '.jpg', '.jpeg', '.webp', '.gif', 'image/small']):
                                        streams.append((sub_v, raw_t))

                        for s_url, s_name in streams:
                            if s_url not in seen_links:
                                seen_links.add(s_url)

                                t_out = cur_time_prefix if cur_time_prefix else "🟢 LIVE"
                                sport_icon = get_sport_icon(prov_name, cur_title)
                                
                                title_out = cur_title if cur_title else "Trực Tiếp"
                                display_line = f"{t_out} {sport_icon} {title_out}"

                                blv_tag = clean_text(s_name) or clean_text(node.get("blv", ""))
                                if blv_tag and blv_tag.lower() not in display_line.lower():
                                    if len(blv_tag.split()) <= 2:
                                        display_line += f" ({blv_tag.upper()})"

                                final_logo = cur_logo if cur_logo else prov_logo
                                group_title_name = "Xôi Lạc Z TV"
                                m3u_content += f"#EXTINF:-1 tvg-logo=\"{final_logo}\" group-title=\"{group_title_name}\",{display_line}\n"

                                referer = node.get("Referer") or node.get("referer") or ""
                                ua = node.get("user_agent") or "Mozilla/5.0"
                                final_link = s_url
                                if referer:
                                    final_link = f"{s_url}|User-Agent={ua}&Referer={referer}"
                                elif ua != "Mozilla/5.0":
                                    final_link = f"{s_url}|User-Agent={ua}"
                                m3u_content += f"{final_link}\n"
                                count += 1

                        for k, v in node.items():
                            if isinstance(v, (list, dict)):
                                process_node(v, cur_time_prefix, cur_title, cur_logo)

                for m in matches:
                    process_node(m, "", "", prov_logo)

            with open('playlist.m3u', 'w', encoding='utf-8') as f:
                f.write(m3u_content)
                
            print(f"Đã tạo xong Xôi Lạc Z TV với {count} luồng chuẩn mẫu hình ảnh!")
            
        else:
            print(f"Lỗi HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"Lỗi: {e}")

if __name__ == "__main__":
    generate_m3u_and_json()
    
