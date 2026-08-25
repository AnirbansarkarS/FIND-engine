import xml.etree.ElementTree as ET
from typing import List
import httpx
from .base import BaseProvider, SearchResult

class ArxivProvider(BaseProvider):
    def __init__(self):
        super().__init__(name="arxiv")
        self.api_url = "https://export.arxiv.org/api/query"

    async def search(self, client: httpx.AsyncClient, query: str) -> List[SearchResult]:
        params = {
            "search_query": f"all:{query}",
            "max_results": 10
        }
        
        try:
            # ArXiv API requests XML format
            response = await client.get(self.api_url, params=params, timeout=5.0)
            response.raise_for_status()
            
            # Parse Atom XML
            xml_data = response.text
            root = ET.fromstring(xml_data)
            
            # Atom Namespace
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            
            entries = root.findall("atom:entry", ns)
            results = []
            
            for entry in entries:
                id_elem = entry.find("atom:id", ns)
                title_elem = entry.find("atom:title", ns)
                summary_elem = entry.find("atom:summary", ns)
                
                if title_elem is None or id_elem is None:
                    continue
                
                # ArXiv titles and abstracts often have linebreaks and extra spaces
                title = " ".join(title_elem.text.split()) if title_elem.text else "Untitled"
                summary = " ".join(summary_elem.text.split()) if summary_elem.text else ""
                url = id_elem.text.strip() if id_elem.text else ""
                
                # Gather authors
                author_nodes = entry.findall("atom:author/atom:name", ns)
                authors = [node.text.strip() for node in author_nodes if node.text]
                authors_str = ", ".join(authors) if authors else "Unknown"
                
                description = f"Authors: {authors_str} | Abstract: {summary}"
                if len(description) > 300:
                    description = description[:297] + "..."
                
                results.append(
                    SearchResult(
                        title=title,
                        url=url,
                        description=description,
                        source=self.name
                    )
                )
                
            return results
        except Exception as e:
            print(f"arXiv search failed: {e}")
            return []
