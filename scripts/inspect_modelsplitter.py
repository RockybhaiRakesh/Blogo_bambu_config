import urllib.request
import re
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}

def inspect_site():
    url = "https://modelsplitter.com/"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            print(f"Status: {resp.status}, HTML length: {len(html)}")
            
            # Save raw HTML to inspect
            with open("modelsplitter_raw.html", "w", encoding="utf-8") as f:
                f.write(html)
            
            title = re.findall(r'<title>(.*?)</title>', html, re.I)
            print("Title:", title)
            
            # Find all script src
            scripts = re.findall(r'<script[^>]*src=["\'](.*?)["\']', html, re.I)
            print(f"Found {len(scripts)} scripts:")
            for s in scripts:
                print("  Script:", s)
                
            # Find text headers, buttons, tools
            headings = re.findall(r'<h[1-4][^>]*>(.*?)</h[1-4]>', html, re.I | re.S)
            print("Headings:", [re.sub(r'<[^>]+>', '', h).strip() for h in headings[:15]])
            
            # Look for keywords: cut, split, pin, connector, tenon, paint, mask, wasm
            keywords = ["paint", "brush", "seam", "loop", "rope", "band", "connector", "pin", "tenon", "magnet", "socket", "plane", "repair", "decimate", "mold", "chamfer"]
            for kw in keywords:
                matches = len(re.findall(kw, html, re.I))
                print(f"Keyword '{kw}': {matches} occurrences")
                
    except Exception as e:
        print("Error fetching site:", e)

if __name__ == "__main__":
    inspect_site()

