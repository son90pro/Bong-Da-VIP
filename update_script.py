import json
import requests

def extract_streams(data, group_name="Bóng Đá"):
    """Hàm đệ quy quét toàn bộ các tầng trong JSON để tìm tên và link stream"""
    streams = []
    
    if isinstance(data, list):
        for item in data:
            streams.extend(extract_streams(item, group_name))
            
    elif isinstance(data, dict):
        # Lấy tiêu đề / tên trận / tên kênh
        title = (data.get("title") or data.get("name") or data.get("match_name") or 
                 data.get("channel_name") or data.get("match") or data.get("team"))
        
        # Lấy đường dẫn link (ưu tiên các trường stream, url, link, m3u8...)
        url = (data.get("stream_url") or data.get("url") or data.get("link") or 
               data.get("m3u8") or data.get("stream") or data.get("source") or data.get("play_url"))
        
        category = (data.get("category") or data.get("group") or data.get("league") or 
                    data.get("sport") or data.get("type") or group_name)
        
        logo = data.get("logo") or data.get("icon") or data.get("thumb") or ""

        # Nếu tìm thấy URL hợp lệ
        if url and isinstance(url, str) and url.startswith("http"):
            if not title:
                title = "Trận đấu trực tiếp"
            streams.append({
                "title": title,
                "group": category,
                "url": url,
                "logo": logo,
                "ua": data.get("user_agent", "Mozilla/5.0"),
                "referer": data.get("referer", "")
            })
        
        # Tiếp tục quét sâu vào bên trong các nhánh con của từ điển này
        for k, v in data.items():
            if isinstance(v, (list, dict)):
                sub_group = category if isinstance(category, str) else group_name
                streams.extend(extract_streams(v, sub_group))
                
    return streams

def generate_m3u_and_json():
    target_url = "https://tinyurl.com/xoilacz3" 
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        print("Đang kết nối để lấy dữ liệu từ link...")
        response = requests.get(target_url, headers=headers, timeout=30, allow_redirects=True)
        
        if response.status_code == 200:
            data = response.json()
            
            # 1. Lưu file JSON gốc
            with open('xoilac.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("Đã cập nhật file xoilac.json thành công!")
            
            # 2. Bóc tách toàn bộ dữ liệu bên trong JSON
            all_streams = extract_streams(data)
            print(f"Quét được tổng cộng {len(all_streams)} mục chứa link.")
            
            m3u_content = "#EXTM3U x-tvg-url=\"\"\n"
            count = 0
            seen_urls = set()

            for s in all_streams:
                url = s["url"]
                url_lower = url.lower()
                
                # BỘ LỌC THÔNG MINH: 
                # Loại bỏ các đường dẫn chỉ là trang chủ gốc (vd: https://khoga1.live/ có dưới 4 dấu / và không có đuôi stream)
                is_root_domain = (url.count('/') <= 3 and not any(ext in url_lower for ext in ['.m3u8', '.ts', 'playlist', 'live', 'play', 'stream', 'hls', 'index', 'watch']))
                
                if is_root_domain:
                    continue  # Bỏ qua trang chủ, chỉ giữ lại link chi tiết trận đấu
                    
                if url not in seen_urls:
                    seen_urls.add(url)
                    title = s["title"]
                    group = s["group"]
                    logo = s["logo"]
                    ua = s["ua"]
                    referer = s["referer"]
                    
                    final_link = url
                    if referer:
                        final_link = f"{url}|User-Agent={ua}&Referer={referer}"
                    elif ua != "Mozilla/5.0":
                        final_link = f"{url}|User-Agent={ua}"

                    m3u_content += f"#EXTINF:-1 tvg-logo=\"{logo}\" group-title=\"{group}\",{title}\n"
                    m3u_content += f"{final_link}\n"
                    count += 1

            with open('playlist.m3u', 'w', encoding='utf-8') as f:
                f.write(m3u_content)
                
            print(f"Đã lọc và tạo xong file playlist.m3u với {count} link phát thực tế!")
            
        else:
            print(f"Lỗi phản hồi từ server: {response.status_code}")
            
    except Exception as e:
        print(f"Đã xảy ra lỗi trong quá trình thực thi: {e}")

if __name__ == "__main__":
    generate_m3u_and_json()
    
