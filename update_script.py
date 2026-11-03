import json
import re
import requests

def get_sport_icon(text=""):
    t = str(text).lower()
    if any(k in t for k in ['tennis', 'quần vợt', 'cirstea', 'timofeeva', 'gibson', 'tsitsipas', 'djokovic', 'shelton', 'paul', 'davidovich']):
        return "🥎"
    elif any(k in t for k in ['basketball', 'bóng rổ', 'sharks', 'liaoning', 'parma', 'bayern', 'townsville', 'sichuan']):
        return "🏀"
    elif any(k in t for k in ['volleyball', 'bóng chuyền', 'ibk', 'ziraat', 'sungurlu', 'hyundai']):
        return "🏐"
    elif any(k in t for k in ['lol', 'game', 'esports', 'top esports', 'gen.g', 'dplus', 'karmine', 'invictus']):
        return "🎮"
    elif any(k in t for k in ['badminton', 'cầu lông']):
        return "🏸"
    else:
        return "⚽"

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
            
            with open('xoilac.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            m3u_content = "#EXTM3U\n\n"
            count = 0
            seen_links = set()

            # Tìm danh sách trận đấu bên trong JSON
            match_items = []
            if isinstance(data, dict):
                # Thử tìm các khóa chứa danh sách trận
                for k in ["matches", "list", "items", "data", "match_list", "schedule", "channels", "matchs", "match", "content"]:
                    if k in data and isinstance(data[k], list):
                        match_items = data[k]
                        break
                if not match_items:
                    # Tìm trong các providers nếu có
                    provs = data.get("providers") or data.get("list") or []
                    if isinstance(provs, list):
                        for p in provs:
                            if isinstance(p, dict):
                                for pk in ["matches", "list", "items", "data", "matchs", "match"]:
                                    if pk in p and isinstance(p[pk], list):
                                        match_items.extend(p[pk])
                    if not match_items:
                        # Fallback: quét tất cả các list có sẵn trong dict
                        for v in data.values():
                            if isinstance(v, list) and len(v) > 0:
                                match_items = v
                                break
            elif isinstance(data, list):
                match_items = data

            print(f"Tìm thấy {len(match_items)} trận đấu chuẩn từ nguồn.")

            for item in match_items:
                if not isinstance(item, dict):
                    continue

                # 1. Trích xuất tên đội hoặc tiêu đề trận đấu chính xác
                home = item.get("home_team") or item.get("home") or ""
                away = item.get("away_team") or item.get("away") or ""
                raw_title = item.get("title") or item.get("name") or item.get("match_name") or ""
                
                teams_str = ""
                if home and away:
                    teams_str = f"{home} vs {away}"
                elif " vs " in raw_title.lower():
                    teams_str = raw_title
                else:
                    # Lấy từ href slug nếu tiêu đề không có vs
                    href = item.get("href") or item.get("url_info") or ""
                    if href:
                        parts = [p for p in href.strip('/').split('/') if p]
                        slug = parts[-1] if parts else ""
                        slug_clean = re.sub(r'-luc-\d+-ngay-[\d-]+', '', slug).strip('-')
                        slug_clean = re.sub(r'-[\d]{2}-[\d]{2}-[\d]{4}', '', slug_clean).strip('-')
                        slug_title = slug_clean.replace('-', ' ').title()
                        if ' vs ' in slug_title.lower():
                            teams_str = slug_title
                
                if not teams_str:
                    teams_str = raw_title if raw_title and len(raw_title) > 3 else "Trực Tiếp"

                # 2. Lấy thời gian (Giờ & Ngày tháng thực tế từ nguồn)
                time_val = item.get("time") or item.get("start_time") or item.get("hour") or item.get("match_time") or ""
                combined_txt = f"{item.get('href', '')} {raw_title} {time_val}"
                
                time_match = re.search(r'(\d{2}[:h]\d{2})', combined_txt)
                time_str = time_match.group(1).replace('h', ':') if time_match else (time_val if time_val else "14:00")
                
                date_match = re.search(r'(\d{2}[-/]\d{2})', combined_txt)
                date_str = date_match.group(1).replace('-', '/') if date_match else "03/11"

                # 3. Lấy icon môn thể thao và logo chuẩn
                sport_icon = get_sport_icon(teams_str + " " + raw_title)
                logo = item.get("home_logo") or item.get("logo") or item.get("icon") or ""
                if not logo or not str(logo).startswith("http") or any(ext in str(logo).lower() for ext in ['.png', '.jpg', '.jpeg', '.webp']):
                    logo = "https://imgts.sportpulseapiz.com/football/team/default/image/small"

                # 4. Trích xuất danh sách luồng phát (streams) và tên BLV/Server sạch sẽ
                streams = []
                
                # Kiểm tra url đơn
                for u_key in ["url", "stream_url", "m3u8", "link", "flv"]:
                    val = item.get(u_key)
                    if isinstance(val, str) and val.startswith("http"):
                        if not any(ext in val.lower() for ext in ['.png', '.jpg', '.jpeg', '.webp', '.gif', 'image/small']):
                            streams.append((val, "VIC"))

                # Kiểm tra mảng streams/links/servers/sources
                for sk in ["streams", "links", "servers", "sources"]:
                    arr = item.get(sk)
                    if isinstance(arr, list):
                        for s in arr:
                            if isinstance(s, str) and s.startswith("http"):
                                if not any(ext in s.lower() for ext in ['.png', '.jpg', '.jpeg', '.webp', '.gif', 'image/small']):
                                    streams.append((s, ""))
                            elif isinstance(s, dict):
                                s_url = s.get("url") or s.get("link") or s.get("m3u8") or s.get("flv") or ""
                                s_name = s.get("name") or s.get("title") or ""
                                if s_url.startswith("http") and not any(ext in s_url.lower() for ext in ['.png', '.jpg', '.jpeg', '.webp', '.gif', 'image/small']):
                                    streams.append((s_url, s_name))

                # Ghi ra file M3U theo đúng chuẩn cấu trúc mẫu của anh
                for idx, (s_url, s_name) in enumerate(streams):
                    if s_url not in seen_links:
                        seen_links.add(s_url)

                        # Xác định tên BLV / Server (VIC, LOGO, POLO, BEE,...)
                        blv_tag = s_name.upper() if s_name else "VIC"
                        if idx % 2 == 1 and not blv_tag.startswith("HD"):
                            blv_tag = f"HD {blv_tag}"
                        
                        display_title = f"🟢 {time_str} {date_str} {sport_icon} {teams_str} ({blv_tag})"

                        m3u_content += f'#EXTINF:-1 tvg-logo="{logo}" group-title="Xôi Lạc Z TV" , {display_title}\n'
                        m3u_content += '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36\n'
                        m3u_content += '#EXTVLCOPT:http-referrer=https://xlz.domainkqt.cc/\n'
                        m3u_content += f'{s_url}\n\n'
                        count += 1

            with open('playlist.m3u', 'w', encoding='utf-8') as f:
                f.write(m3u_content)
                
            print(f"Đã tạo xong Xôi Lạc Z TV với {count} luồng chuẩn xác mẫu yêu cầu!")
            
        else:
            print(f"Lỗi HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"Lỗi: {e}")

if __name__ == "__main__":
    generate_m3u_and_json()
    
