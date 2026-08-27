import httpx

def run_test():
    query = "artificial intelligence"
    url = f"http://localhost:8000/search?q={query}"
    
    print(f"--- TESTING SEARCH FOR: '{query}' ---")
    try:
        res = httpx.get(url, timeout=10.0)
        print(f"Status Code: {res.status_code}")
        if res.status_code == 200:
            data = res.json()
            results = data.get("results", [])
            print(f"Total Unique Results: {len(results)}\n")
            
            # Print top 10 ranked results with custom score and sources list
            for idx, item in enumerate(results[:10]):
                print(f"Rank [{idx+1}] Title: {item.get('title')}")
                print(f"         URL  : {item.get('url')}")
                print(f"         Domain: {item.get('domain')}")
                print(f"         Sources: {item.get('source')}")
                print(f"         Final Score: {item.get('raw_score')}")
                print(f"         Snippet: {item.get('snippet')[:90]}...\n")
        else:
            print("API Error:", res.text)
    except Exception as e:
        print("Failed to run test:", e)

if __name__ == "__main__":
    run_test()
