import httpx
import json

def test():
    query = "quantum mechanics"
    url = f"http://localhost:8000/search?q={query}"
    
    print(f"Sending test query: '{query}' to {url}\n")
    try:
        r = httpx.get(url, timeout=10.0)
        print(f"Status Code: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            results = data.get("results", [])
            print(f"Total Unique Results: {len(results)}\n")
            
            # Print top 8 results with new schema details
            for i, res in enumerate(results[:8]):
                print(f"[{i+1}] Title: {res.get('title')}")
                print(f"    URL: {res.get('url')}")
                print(f"    Domain: {res.get('domain')}")
                print(f"    Source(s): {res.get('source')}")
                print(f"    Score: {res.get('raw_score')}")
                print(f"    Date: {res.get('published_date')}")
                print(f"    Snippet: {res.get('snippet')[:100]}...\n")
        else:
            print("API error:", r.text)
    except Exception as e:
        print("Failed to query API:", e)

if __name__ == "__main__":
    test()
