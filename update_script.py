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
                
                # Tên danh mục bên cột trái TV
                prov_name = prov.get("name") or prov.get("title") or "Kênh Trực Tiếp"
                prov_logo = prov.get("logo") or prov.get("icon") or ""
                
                # Lấy danh sách các trận đấu bên trong mỗi provider
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

                for match in matches:
                    if not isinstance(match, dict):
                        continue
                    
                    # 1. Trích xuất chuẩn tên đội bóng (Home vs Away) từ cấu trúc JSON
                    home = match.get("home_team") or match.get("home") or match.get("team_home") or match.get("home_name") or ""
                    away = match.get("away_team") or match.get("away") or match.get("team_away") or match.get("away_name") or ""
                    
                    match_title = ""
                    if home and away:
                        match_title = f"{home} vs {away}"
                    else:
                        # Fallback nếu không có cấu trúc home/away riêng biệt
                        raw_t = match.get("match_name") or match.get("title") or match.get("name") or ""
                        if raw_t and not any(kw in raw_t.lower() for kw in ["đang phát trực tiếp", "lịch thi đấu", "tất cả", "href", "url", "logo", "referer"]):
                            match_title = raw_t

                    if not match_title:
                        match_title = f"{prov_name} Trực Tiếp"

                    # 2. Lấy thông tin thời gian, giải đấu, BLV, logo
                    league = match.get("league") or match.get("tournament") or match.get("category") or match.get("competition") or ""
                    time_str = match.get("time") or match.get("date") or match.get("start_time") or match.get("match_time") or ""
                    blv = match.get("blv") or match.get("commentator") or match.get("caster") or match.get("bình luận viên") or ""
                    
                    # Lấy logo đội nhà hoặc logo trận đấu
                    logo = match.get("logo") or match.get("home_logo") or match.get("icon") or prov_logo
                    
                    ua = match.get("user_agent", "Mozilla/5.0")
                    referer = match.get("referer", "")

                    # Xây dựng tiêu đề hiển thị hoàn chỉnh trên TV
                    title_parts = []
                    if time_str:
                        title_parts.append(f"[{time_str}]")
                    title_parts.append(match_title)
                    if league and league not in match_title:
                        title_parts.append(f"({league})")
                    if blv:
                        title_parts.append(f"- BLV: {blv}")

                    display_title = " ".join(title_parts)

                    # 3. Thu thập các luồng phát stream chính xác (lọc bỏ tuyệt đối các key rác href, logo, referer)
                    streams = []
                    
                    # Kiểm tra các mảng chứa server stream
                    for sk in ["streams", "links", "servers", "sources", "playlist"]:
                        if sk in match and isinstance(match[sk], list):
                            for s in match[sk]:
                                if isinstance(s, str) and s.startswith("http"):
                                    streams.append({"name": "Server", "url": s})
                                elif isinstance(s, dict):
                                    s_url = s.get("url") or s.get("link") or s.get("stream_url") or s.get("m3u8") or ""
                                    s_name = s.get("name") or s.get("server_name") or "Server"
                                    if s_url:
                                        streams.append({"name": s_name, "url": s_url})

                    # Kiểm tra các trường link đơn trực tiếp
                    for dk in ["stream_url", "url", "link", "m3u8", "source", "play_url", "hls"]:
                        val = match.get(dk)
                        if isinstance(val, str) and val.startswith("http"):
                            # Đảm bảo không lấy nhầm link ảnh hoặc link trang chủ thông tin trận đấu
                            val_lower = val.lower()
                            if not any(ext in val_lower for ext in ['.png', '.jpg', '.jpeg', '.webp', '.gif', 'almafestival.info']):
                                streams.append({"name": "Server chính", "url": val})

                    # Loại bỏ các stream trùng lặp
                    unique_streams = []
                    seen_stream_urls = set()
                    for st in streams:
                        u = st["url"]
                        if u not in seen_stream_urls and u.startswith("http"):
                            seen_stream_urls.add(u)
                            unique_streams.append(st)

                    for idx, stream in enumerate(unique_streams, 1):
                        s_url = stream["url"]
                        s_name = stream["name"]
                        
                        s_url_lower = s_url.lower()
                        # Bộ lọc an toàn: Chặn đứng mọi loại ảnh và trang web tin tức/trang chủ
                        is_image = any(ext in s_url_lower for ext in ['.png', '.jpg', '.jpeg', '.webp', '.gif', 'badge', 'logo', 'images/teams'])
                        is_homepage = ('almafestival.info' in s_url_lower or (s_url.count('/') <= 3 and not any(kw in s_url_lower for kw in ['.m3u8', '.ts', 'playlist', 'live', 'play', 'stream', 'token', 'server', 'hls'])))

                        if is_image or is_homepage:
                            continue

                        if s_url not in seen_links:
                            seen_links.add(s_url)
                            item_title = f"{display_title} [{s_name}]" if len(unique_streams) > 1 and s_name != "Server chính" else display_title
                            
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
                
            print(f"Đã tạo xong file playlist.m3u với {count} luồng trận đấu chuẩn xác tuyệt đối!")
            
        else:
            print(f"Lỗi phản hồi từ server: {response.status_code}")
            
    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")

if __name__ == "__main__":
    generate_m3u_and_json()
    
