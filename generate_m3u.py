# -*- coding: utf-8 -*-
import os
from badong_engine import get_live_channels, resolve_stream_url

# Link logo Bóng Đá VIP của anh Sơn
BONG_DA_VIP_LOGO = "https://raw.githubusercontent.com/son90pro/Bong-Da-VIP/refs/heads/main/10894352.png"

def generate_playlist():
    print("Đang lấy danh sách kênh từ các nguồn...")
    channels = get_live_channels(force_refresh=True, enable_tier3=False)
    
    if not channels:
        print("Cảnh báo: Không lấy được kênh nào!")
        return

    m3u_lines = ["#EXTM3U x-tvg-url=\"\""]
    
    for ch in channels:
        title = ch.get("title", "Trực tiếp Thể Thao")
        # Giữ nguyên nhóm gốc của từng kênh (VD: Vua Sân Cỏ TV, Chuối Chiên TV, v.v.)
        group = ch.get("group", "Thể Thao Live")
        raw_url = ch.get("url", "")
        provider = ch.get("provider", "")
        
        # Gán logo Bóng Đá VIP cho tất cả các kênh để hiển thị đẹp mắt ngoài giao diện chính
        logo = BONG_DA_VIP_LOGO
        
        # Gắn pipe parameters (User-Agent & Referer)
        stream_url = resolve_stream_url(raw_url, provider)
        
        extinf = f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}",{title}'
        m3u_lines.append(extinf)
        m3u_lines.append(stream_url)
        
    output_filename = "playlist.m3u"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines))
        
    print(f"Đã tạo thành công {output_filename} với {len(channels)} kênh phân theo nhóm!")

if __name__ == "__main__":
    generate_playlist()
    
