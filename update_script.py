import json
import requests

def find_items_recursive(data):
    """Hàm đệ quy quét sâu vào bên trong JSON để tìm ra các mục dữ liệu"""
    results = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                has_link = any(k in item for k in ["url", "link", "stream", "m3u8", "stream_url", "source"])
                has_title = any(k in item for k in ["title", "name", "match", "match_name", "channel", "room_name"])
                if has_link or has_title:
                    results.append(item)
                else:
                    results.extend(find_items_recursive(item))
            elif isinstance(item, list):
                results.extend(find_items_recursive(item))
    elif isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, list):
                results.extend(find_items_recursive(value))
            elif isinstance(value, dict):
                results.extend(find_items_recursive(value))
    return results

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
            
            # 2. Quét dữ liệu
            raw_items = find_items_recursive(data)
            if not raw_items and isinstance(data, list):
                raw_items = data

            m3u_content = "#EXTM3U x-tvg-url=\"\"\n"
            count = 0

            for item in raw_items:
                if not isinstance(item, dict):
                    continue
                
                title = (item.get("title") or item.get("name") or item.get("match_name") or 
                         item.get("channel_name") or item.get("match") or "Trận đấu trực tiếp")
                
                group = (item.get("category") or item.get("group") or item.get("league") or 
                         item.get("sport") or item.get("type") or "Bóng Đá")
                
                stream_url = (item.get("stream_url") or item.get("url") or item.get("link") or 
                              item.get("m3u8") or item.get("stream") or item.get("source") or "")
                
                logo = (item.get("logo") or item.get("icon") or item.get("thumb") or "")
                
                # BỘ LỌC CHẶT CHẼ: Chỉ lấy link stream thực thụ (phải chứa .m3u8, .ts, hoặc các từ khóa luồng phát)
                # Loại bỏ hoàn toàn các trang chủ/website chung chung (như .com, .love, .live trơn không có đuôi stream)
                stream_url_lower = str(stream_url).lower()
                is_valid_stream = (
                    stream_url.startswith("http") and 
                    not stream_url_lower.endswith(tuple([".com", ".love", ".live", ".me", ".top", ".gg", ".vn"])) or
                    any(keyword in stream_url_lower for keyword in [".m3u8", ".ts", "playlist", "live/", "m3u", "stream", "hls"])
                )

                # Nếu là link stream hợp lệ thì mới đưa vào M3U
                if is_valid_stream:
                    ua = item.get("user_agent", "Mozilla/5.0")
                    referer = item.get("referer", "")
                    
                    final_link = stream_url
                    if referer:
                        final_link = f"{stream_url}|User-Agent={ua}&Referer={referer}"
                    elif ua != "Mozilla/5.0":
                        final_link = f"{stream_url}|User-Agent={ua}"

                    m3u_content += f"#EXTINF:-1 tvg-logo=\"{logo}\" group-title=\"{group}\",{title}\n"
                    m3u_content += f"{final_link}\n"
                    count += 1

            with open('playlist.m3u', 'w', encoding='utf-8') as f:
                f.write(m3u_content)
                
            print(f"Đã tạo xong file playlist.m3u với {count} luồng trận đấu chuẩn!")
            
        else:
            print(f"Lỗi phản hồi từ server: {response.status_code}")
            
    except Exception as e:
        print(f"Đã xảy ra lỗi trong quá trình thực thi: {e}")

if __name__ == "__main__":
    generate_m3u_and_json()
    
