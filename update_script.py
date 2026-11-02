import json
import requests

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
            
            # Lưu file JSON gốc để kiểm tra
            with open('xoilac.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("Đã lưu file xoilac.json thành công!")
            
            m3u_content = "#EXTM3U x-tvg-url=\"\"\n"
            count = 0
            seen_links = set()

            providers = data.get("providers", [])
            if not isinstance(providers, list):
                providers = []

            for prov in providers:
                if not isinstance(prov, dict):
                    continue
                
                # Giữ nguyên tên nhà cung cấp làm danh mục nhóm bên sidebar TV (Xôi Lạc TV, Khô Gà TV,...)
                prov_name = prov.get("name") or prov.get("title") or "Kênh Trực Tiếp"
                prov_logo = prov.get("logo") or prov.get("icon") or ""
                
                # Lấy danh sách trận đấu bên trong provider
                matches = []
                for k in ["matches", "list", "items", "data", "match_list", "schedule", "channels", "matchs"]:
                    if k in prov and isinstance(prov[k], list):
                        matches = prov[k]
                        break
                
                if not matches:
                    for val in prov.values():
                        if isinstance(val, list):
                            matches = val
                            break

                # Quét đệ quy dự phòng nếu dữ liệu lồng sâu hơn
                if not matches:
                    def deep_find_list(obj):
                        res = []
                        if isinstance(obj, list):
                            return obj
                        elif isinstance(obj, dict):
                            for v in obj.values():
                                res.extend(deep_find_list(v))
                        return res
                    matches = deep_find_list(prov)

                for match in matches:
                    if not isinstance(match, dict):
                        continue
                    
                    # 1. Trích xuất tên đội bóng (Home vs Away)
                    home = match.get("home_team") or match.get("home") or match.get("team_home") or match.get("home_name") or ""
                    away = match.get("away_team") or match.get("away") or match.get("team_away") or match.get("away_name") or ""
                    
                    match_title = ""
                    if home and away:
                        match_title = f"{home} vs {away}"
                    else:
                        match_title = match.get("match_name") or match.get("title") or match.get("name") or ""
                        if not match_title or any(kw in match_title.lower() for kw in ["đang phát trực tiếp", "lịch thi đấu", "tất cả", "href", "url"]):
                            match_title = f"{prov_name} Live"

                    # 2. Trích xuất thông tin chi tiết: Thời gian, Giải đấu, BLV, Logo
                    league = match.get("league") or match.get("tournament") or match.get("category") or match.get("competition") or ""
                    time_str = match.get("time") or match.get("date") or match.get("start_time") or match.get("match_time") or ""
                    blv = match.get("blv") or match.get("commentator") or match.get("caster") or match.get("bình luận viên") or ""
                    logo = match.get("logo") or match.get("icon") or match.get("match_logo") or prov_logo
                    
                    ua = match.get("user_agent", "Mozilla/5.0")
                    referer = match.get("referer", "")

                    # Xây dựng tiêu đề hiển thị chuẩn trên TV: [Thời gian] Đội A vs Đội B (Giải đấu) - BLV: Tên
                    title_parts = []
                    if time_str:
                        title_parts.append(f"[{time_str}]")
                    title_parts.append(match_title)
                    if league and league not in match_title:
                        title_parts.append(f"({league})")
                    if blv:
                        title_parts.append(f"- BLV: {blv}")

                    display_title = " ".join(title_parts)

                    # 3. Thu thập các luồng phát stream
                    streams = []
                    for sk in ["streams", "links", "servers", "sources", "playlist"]:
                        if sk in match and isinstance(match[sk], list):
                            streams.extend(match[sk])
                    
                    for dk in ["stream_url", "url", "link", "m3u8", "source", "play_url", "hls"]:
                        if dk in match and isinstance(match[dk], str):
                            streams.append({"name": "Server chính", "url": match[dk]})

                    if not streams:
                        def find_urls_in_dict(d):
                            found = []
                            if isinstance(d, dict):
                                for sub_k, sub_v in d.items():
                                    if isinstance(sub_v, str) and sub_v.startswith("http"):
                                        found.append((sub_v, sub_k))
                                    elif isinstance(sub_v, (dict, list)):
                                        found.extend(find_urls_in_dict(sub_v))
                            elif isinstance(d, list):
                                for item in d:
                                    found.extend(find_urls_in_dict(item))
                            return found
                        
                        raw_urls = find_urls_in_dict(match)
                        for r_url, r_name in raw_urls:
                            streams.append({"name": r_name, "url": r_url})

                    for idx, stream in enumerate(streams, 1):
                        s_url = ""
                        s_name = f"Server {idx}"
                        
                        if isinstance(stream, str):
                            s_url = stream
                        elif isinstance(stream, dict):
                            s_url = stream.get("url") or stream.get("link") or stream.get("stream_url") or stream.get("m3u8") or ""
                            s_name = stream.get("name") or stream.get("server_name") or f"Server {idx}"
                            ua = stream.get("user_agent", ua)
                            referer = stream.get("referer", referer)

                        if s_url and isinstance(s_url, str) and s_url.startswith("http"):
                            s_url_lower = s_url.lower()
                            
                            # Loại bỏ hình ảnh và link trang chủ gốc
                            is_image = any(ext in s_url_lower for ext in ['.png', '.jpg', '.jpeg', '.webp', '.gif', 'badge', 'logo', 'images/teams'])
                            is_homepage = (s_url.count('/') <= 3 and not any(kw in s_url_lower for kw in ['.m3u8', '.ts', 'playlist', 'live', 'play', 'stream', 'token', 'server', 'hls']))

                            if is_image or is_homepage:
                                continue

                            if s_url not in seen_links:
                                seen_links.add(s_url)
                                item_title = f"{display_title} [{s_name}]" if len(streams) > 1 and s_name != "Server chính" else display_title
                                
                                m3u_content += f"#EXTINF:-1 tvg-logo=\"{logo}\" group-title=\"{prov_name}\",{item_title}\n"
                                
                                final_link = s_url
                                if referer:
                                    final_link = f"{s_url}|User-Agent={ua}&Referer={referer}"
                                elif ua != "Mozilla/5.0":
                                    final_link = f"{s_url}|User-Agent={ua}"
                                    
                                m3u_content += f"{final_link}\n"
                                count += 1

            with open('playlist.m3u', 'w', encoding='utf-8') as f:
                f.write(m3u_content)
                
            print(f"Đã tạo xong file playlist.m3u với {count} luồng trận đấu đầy đủ chi tiết!")
            
        else:
            print(f"Lỗi phản hồi từ server: {response.status_code}")
            
    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")

if __name__ == "__main__":
    generate_m3u_and_json()
    
