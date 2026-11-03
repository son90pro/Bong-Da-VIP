import json
import re
import requests

def get_sport_icon(sport_type=""):
    s = str(sport_type).lower()
    if 'tennis' in s or 'quần vợt' in s:
        return "🥎"
    elif 'basketball' in s or 'bóng rổ' in s:
        return "🏀"
    elif 'volleyball' in s or 'bóng chuyền' in s:
        return "🏐"
    elif 'lol' in s or 'game' in s or 'esports' in s:
        return "🎮"
    elif 'badminton' in s or 'cầu lông' in s:
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

            # Tìm đến đúng node chứa danh sách trận đấu của Xôi Lạc Z TV
            providers = []
            if isinstance(data, dict):
                if "providers" in data and isinstance(data["providers"], list):
                    providers = data["providers"]
                else:
                    providers = [data]
            elif isinstance(data, list):
                providers = data

            matches_list = []
            for prov in providers:
                if not isinstance(prov, dict):
                    continue
                p_name = prov.get("name") or prov.get("title") or ""
                if "xôi lạc" in p_name.lower() or "xoilac" in p_name.lower() or "z" in p_name.lower():
                    for k in ["matches", "list", "items", "data", "match_list", "schedule", "channels", "matchs", "match"]:
                        if k in prov and isinstance(prov[k], list):
                            matches_list = prov[k]
                            break
                    if not matches_list:
                        # Lấy danh sách đầu tiên tìm thấy
                        for v in prov.values():
                            if isinstance(v, list) and len(v) > 0:
                                matches_list = v
                                break

            # Nếu không tìm thấy qua provider, quét toàn bộ dict
            if not matches_list and isinstance(data, dict):
                for k, v in data.items():
                    if isinstance(v, list):
                        matches_list = v
                        break

            print(f"Tìm thấy {len(matches_list)} trận đấu từ nguồn.")

            for match in matches_list:
                if not isinstance(match, dict):
                    continue

                # Trích xuất tên đội nhà / đội khách hoặc tiêu đề trận
                home = match.get("home_team") or match.get("home") or ""
                away = match.get("away_team") or match.get("away") or ""
                raw_title = match.get("title") or match.get("name") or match.get("match_name") or ""

                teams_str = ""
                if home and away:
                    teams_str = f"{home} vs {away}"
                elif " vs " in raw_title.lower():
                    teams_str = raw_title
                else:
                    # Lấy từ href slug nếu có
                    href = match.get("href") or match.get("url_info") or ""
                    if href:
                        parts = [p for p in href.strip('/').split('/') if p]
                        slug = parts[-1] if parts else ""
                        slug_clean = re.sub(r'-luc-\d+-ngay-[\d-]+', '', slug).strip('-')
                        slug_clean = re.sub(r'-[\d]{2}-[\d]{2}-[\d]{4}', '', slug_clean).strip('-')
                        slug_title = slug_clean.replace('-', ' ').title()
                        if ' vs ' in slug_title.lower():
                            teams_str = slug_title
                    
                if not teams_str:
                    teams_str = raw_title if raw_title else "Trực Tiếp"

                # Lấy thời gian
                time_val = match.get("time") or match.get("start_time") or match.get("hour") or ""
                combined_txt = f"{match.get('href', '')} {raw_title} {time_val}"
                
                time_match = re.search(r'(\d{2}[:h]\d{2})', combined_txt)
                time_str = time_match.group(1).replace('h', ':') if time_match else "14:00"
                
                date_match = re.search(r'(\d{2}[-/]\d{2})', combined_txt)
                date_str = date_match.group(1).replace('-', '/') if date_match else "03/11"

                # Logo môn thể thao / đội bóng
                sport_type = match.get("sport") or match.get("category") or match.get("type") or ""
                sport_icon = get_sport_icon(sport_type)
                logo = match.get("home_logo") or match.get("logo") or match.get("icon") or ""
                if not logo or not logo.startswith("http"):
                    logo = "https://imgts.sportpulseapiz.com/football/team/default/image/small"

                # Lọc danh sách luồng phát (streams) hợp lệ, loại bỏ các link ảnh rác (.png, .jpg, v.v.)
                streams = []
                
                # Kiểm tra các khóa URL đơn lẻ
                for u_key in ["url", "stream_url", "m3u8", "link", "flv"]:
                    val = match.get(u_key)
                    if isinstance(val, str) and val.startswith("http"):
                        if not any(ext in val.lower() for ext in ['.png', '.jpg', '.jpeg', '.webp', '.gif', 'image/small']):
                            streams.append((val, "VIC"))

                # Kiểm tra các mảng streams/links/servers
                for sk in ["streams", "links", "servers", "sources"]:
                    arr = match.get(sk)
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

                # Nếu vẫn chưa có stream, quét các giá trị bên trong dict
                if not streams:
                    for sub_k, sub_v in match.items():
                        if isinstance(sub_v, str) and sub_v.startswith("http") and not any(ext in sub_v.lower() for ext in ['.png', '.jpg', '.jpeg', '.webp', '.gif', 'image/small']):
                            if any(ext in sub_v.lower() for ext in ['.m3u8', '.flv', 'live', 'playlist', 'channel']):
                                streams.append((sub_v, ""))

                # Ghi ra file M3U theo đúng mẫu chuẩn
                for idx, (s_url, s_name) in enumerate(streams):
                    if s_url not in seen_links:
                        seen_links.add(s_url)

                        tag = s_name.upper() if s_name else "VIC"
                        if idx % 2 == 1 and not tag.startswith("HD"):
                            tag = f"HD {tag}"
                        
                        display_title = f"🟢 {time_str} {date_str} {sport_icon} {teams_str} ({tag})"

                        m3u_content += f'#EXTINF:-1 tvg-logo="{logo}" group-title="Xôi Lạc Z TV" , {display_title}\n'
                        m3u_content += '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36\n'
                        m3u_content += '#EXTVLCOPT:http-referrer=https://xlz.domainkqt.cc/\n'
                        m3u_content += f'{s_url}\n\n'
                        count += 1

            with open('playlist.m3u', 'w', encoding='utf-8') as f:
                f.write(m3u_content)
                
            print(f"Đã tạo xong Xôi Lạc Z TV với {count} luồng sạch đẹp chuẩn chỉnh!")
            
        else:
            print(f"Lỗi HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"Lỗi: {e}")

if __name__ == "__main__":
    generate_m3u_and_json()
    
