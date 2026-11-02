import json
import requests

def parse_node(node, group_name="Bóng Đá"):
    streams = []
    if isinstance(node, list):
        for item in node:
            streams.extend(parse_node(item, group_name))
    elif isinstance(node, dict):
        # Lấy tên / tiêu đề
        title = (node.get("title") or node.get("name") or node.get("match_name") or 
                 node.get("channel_name") or node.get("match") or "")
        
        # Lấy link stream hoặc url
        url = (node.get("stream_url") or node.get("url") or node.get("link") or 
               node.get("m3u8") or node.get("stream") or node.get("source") or node.get("play_url"))
        
        category = (node.get("category") or node.get("group") or node.get("league") or 
                    node.get("sport") or node.get("type") or group_name)
        
        logo = node.get("logo") or node.get("icon") or node.get("thumb") or ""

        if url and isinstance(url, str) and url.startswith("http"):
            if not title:
                title = "Trận đấu trực tiếp"
            streams.append({
                "title": title,
                "group": category,
                "url": url,
                "logo": logo,
                "ua": node.get("user_agent", "Mozilla/5.0"),
                "referer": node.get("referer", "")
            })

        # Đệ quy quét tất cả các key con (đặc biệt là các nhánh matches, channels, items bên trong groups/providers)
import json
import requests

def extract_all_links(data):
    results = []
    
    def recursive_search(obj, current_group="Bóng Đá"):
        if isinstance(obj, list):
            for item in obj:
                recursive_search(item, current_group)
        elif isinstance(obj, dict):
            # Cập nhật group nếu có
            group = obj.get("category") or obj.get("group") or obj.get("league") or current_group
            title = obj.get("title") or obj.get("name") or obj.get("match_name") or obj.get("channel_name") or ""
            logo = obj.get("logo") or obj.get("icon") or ""
            
            # Quét các trường chứa link
            for k, v in obj.items():
                if isinstance(v, str) and v.startswith("http"):
                    # Nếu key mang ý nghĩa là link/stream/url
                    if any(key_word in k.lower() for key_word in ["url", "link", "stream", "m3u8", "source", "play"]):
                        results.append({
                            "title": title or f"Kênh {k}",
                            "group": group,
                            "url": v,
                            "logo": logo,
                            "ua": obj.get("user_agent", "Mozilla/5.0"),
                            "referer": obj.get("referer", "")
                        })
                elif isinstance(v, (list, dict)):
                    recursive_search(v, group)

    recursive_search(data)
    return results

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
            
            # 1. Lưu file JSON gốc
            with open('xoilac.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("Đã lưu file xoilac.json thành công!")
            
            # 2. Trích xuất toàn bộ các link ẩn sâu bên trong các nhánh groups/providers
            all_links = extract_all_links(data)
            print(f"Tổng số link tìm thấy trong mọi ngóc ngách: {len(all_links)}")
            
            m3u_content = "#EXTM3U x-tvg-url=\"\"\n"
            count = 0
            seen_urls = set()

            for item in all_links:
                url = item["url"]
                if url not in seen_urls:
                    seen_urls.add(url)
                    
                    # Lọc bớt các link trang chủ nếu cần, nhưng giữ lại toàn bộ link có tiềm năng stream
                    m3u_content += f"#EXTINF:-1 tvg-logo=\"{item['logo']}\" group-title=\"{item['group']}\",{item['title']}\n"
                    
                    final_link = url
                    if item["referer"]:
                        final_link = f"{url}|User-Agent={item['ua']}&Referer={item['referer']}"
                    elif item["ua"] != "Mozilla/5.0":
                        final_link = f"{url}|User-Agent={item['ua']}"
                        
                    m3u_content += f"{final_link}\n"
                    count += 1

            with open('playlist.m3u', 'w', encoding='utf-8') as f:
                f.write(m3u_content)
                
            print(f"Đã tạo xong file playlist.m3u với {count} mục hoàn chỉnh!")
            
        else:
            print(f"Lỗi server: {response.status_code}")
            
    except Exception as e:
        print(f"Lỗi thực thi: {e}")

if __name__ == "__main__":
    generate_m3u_and_json()
    
