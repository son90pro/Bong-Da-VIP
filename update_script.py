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
            
            # Lưu lại file JSON để kiểm tra cấu trúc nếu cần
            with open('xoilac.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("Đã lưu file xoilac.json thành công!")
            
            valid_items = []
            seen_links = set()

            providers = data.get("providers", [])
            if not isinstance(providers, list):
                providers = []

            for prov in providers:
                if not isinstance(prov, dict):
                    continue
                
                prov_name = prov.get("name") or prov.get("title") or "Kênh Trực Tiếp"
                prov_logo = prov.get("logo") or prov.get("icon") or ""

                # Hàm quét đệ quy tìm các node chứa thông tin trận đấu thực sự
                def extract_matches(node, current_category):
                    if isinstance(node, list):
                        for item in node:
                            extract_matches(item, current_category)
                    elif isinstance(node, dict):
                        # Cập nhật danh mục nếu node có tên nhóm riêng
                        cat = node.get("name") or node.get("title") or current_category
                        
                        # Kiểm tra xem node này có phải là một trận đấu hay không dựa trên sự xuất hiện của tên đội bóng
                        home = node.get("home_team") or node.get("home") or node.get("team_home") or node.get("home_name") or ""
                        away = node.get("away_team") or node.get("away") or node.get("team_away") or node.get("away_name") or ""
                        
                        match_title = ""
                        if home and away:
                            match_title = f"{home} vs {away}"
                        else:
                            # Thử tìm các trường tên khác nhưng loại bỏ các từ khóa rác giao diện
                            raw_t = node.get("match_name") or node.get("title") or node.get("name") or ""
                            if raw_t and not any(kw in raw_t.lower() for kw in ["đang phát trực tiếp", "lịch thi đấu", "tất cả", "href", "url", "logo"]):
                                match_title = raw_t

                        # Nếu tìm thấy trận đấu hoặc các trường thông tin chi tiết
                        if match_title:
                            league = node.get("league") or node.get("tournament") or node.get("category") or ""
                            time_str = node.get("time") or node.get("date") or node.get("start_time") or node.get("schedule") or ""
                            blv = node.get("blv") or node.get("commentator") or node.get("caster") or ""
                            logo = node.get("logo") or node.get("icon") or prov_logo
                            ua = node.get("user_agent", "Mozilla/5.0")
                            referer = node.get("referer", "")

                            # Xây dựng tiêu đề hiển thị chuẩn trên TV: [Thời gian] Tên trận (Giải đấu) - BLV: Tên
                            display_parts = [match_title]
                            if league and league not in match_title:
                                display_parts.append(f"({league})")
                            if time_str:
                                display_parts.insert(0, f"[{time_str}]")
                            if blv:
                                display_parts.append(f"- BLV: {blv}")
                            
                            full_title = " ".join(display_parts)

                            # Thu thập các link stream phát sóng
                            streams = []
                            for k in ["stream_url", "url", "link", "m3u8", "source", "play_url", "hls"]:
                                val = node.get(k)
                                if isinstance(val, str) and val.startswith("http"):
                                    streams.append((val, "Server chính"))

                            for k in ["streams", "links", "servers", "sources", "playlist"]:
                                arr = node.get(k)
                                if isinstance(arr, list):
                                    for s in arr:
                                        if isinstance(s, str) and s.startswith("http"):
                                            streams.append((s, "Server"))
                                        elif isinstance(s, dict):
                                            s_url = s.get("url") or s.get("link") or s.get("stream_url") or s.get("m3u8") or ""
                                            s_name = s.get("name") or s.get("server_name") or "Server"
                                            if isinstance(s_url, str) and s_url.startswith("http"):
                                                streams.append((s_url, s_name))

                            for s_url, s_name in streams:
                                s_url_lower = s_url.lower()
                                # Loại bỏ ảnh và link trang chủ
                                is_image = any(ext in s_url_lower for ext in ['.png', '.jpg', '.jpeg', '.webp', '.gif', 'badge', 'logo'])
                                is_homepage = (s_url.count('/') <= 3 and not any(kw in s_url_lower for kw in ['.m3u8', '.ts', 'playlist', 'live', 'play', 'stream', 'token', 'server', 'hls']))

                                if is_image or is_homepage:
                                    continue

                                if s_url not in seen_links:
                                    seen_links.add(s_url)
                                    
                                    item_title = full_title
                                    if len(streams) > 1 and s_name != "Server chính":
                                        item_title += f" [{s_name}]"

                                    valid_items.append({
                                        "group": prov_name,
                                        "title": item_title,
                                        "url": s_url,
                                        "logo": logo,
                                        "ua": ua,
                                        "referer": referer
                                    })

                        # Tiếp tục duyệt sâu vào các nhánh con bên trong node
                        for k, v in node.items():
                            if isinstance(v, (list, dict)):
                                extract_matches(v, cat)

                extract_matches(prov, prov_name)

            # Ghi file playlist.m3u
            m3u_content = "#EXTM3U x-tvg-url=\"\"\n"
            for item in valid_items:
                m3u_content += f"#EXTINF:-1 tvg-logo=\"{item['logo']}\" group-title=\"{item['group']}\",{item['title']}\n"
                final_link = item["url"]
                if item["referer"]:
                    final_link = f"{item['url']}|User-Agent={item['ua']}&Referer={item['referer']}"
                elif item["ua"] != "Mozilla/5.0":
                    final_link = f"{item['url']}|User-Agent={item['ua']}"
                m3u_content += f"{final_link}\n"

            with open('playlist.m3u', 'w', encoding='utf-8') as f:
                f.write(m3u_content)
                
            print(f"Đã tạo xong file playlist.m3u với {len(valid_items)} luồng trận đấu chi tiết!")
            
        else:
            print(f"Lỗi phản hồi từ server: {response.status_code}")
            
    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")

if __name__ == "__main__":
    generate_m3u_and_json()
    
