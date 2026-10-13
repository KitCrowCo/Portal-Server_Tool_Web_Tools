import requests
from bs4 import BeautifulSoup
import json
import typing

class WebScraper:
    def __init__(self, auth_token: str = None, login_url: str = None, credentials: dict = None):
        self.session = requests.Session()
        # Suppress SSL warnings if your internal intranet uses self-signed certs
        self.session.verify = False 
        if auth_token:
            self.session.headers.update({"Authorization": f"Bearer {auth_token}"})
        elif login_url and credentials:
            self.session.post(login_url, data=credentials)

    def extract_tables_to_json(self, url: str, table_class: str = None) -> list:
        """Pulls target URL and parses <tbody> elements into structured JSON."""
        response = self.session.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        extracted_data = []
        tables = soup.find_all('table', class_=table_class) if table_class else soup.find_all('table')
        for table in tables:
            tbody = table.find('tbody')
            if not tbody: continue
            table_data = []
            for tr in tbody.find_all('tr'):
                row_data = {"_row_meta": tr.attrs} # Capture data- attributes from the row
                cells = tr.find_all(['td', 'th'])
                for i, td in enumerate(cells):
                    cell_text = td.get_text(strip=True)
                    cell_attrs = td.attrs
                    # If the cell has data attributes, store them alongside the text
                    if cell_attrs:
                        row_data[f"col_{i}"] = {"value": cell_text, "meta": cell_attrs}
                    else:
                        row_data[f"col_{i}"] = cell_text
                table_data.append(row_data)
            extracted_data.append(table_data)
        return extracted_data

    @staticmethod
    def render_json_tree(data: typing.Any, name: str = "root") -> str:
        """Generates a zero-JS collapsible HTML tree using details/summary tags."""
        css = """<style>
                     .json-tree { font-family: var(--font-mono, monospace); font-size: 0.85rem; line-height: 1.4; }
                     .json-tree details { margin-left: 1.2rem; border-left: 1px dashed var(--border); padding-left: 0.5rem; }
                     .json-tree summary { cursor: pointer; color: var(--accent); font-weight: 600; list-style: none; }
                     .json-tree summary::-webkit-details-marker { display: none; }
                     .json-tree summary::before { content: '\\25B6'; font-size: 0.6rem; display: inline-block; margin-right: 0.4rem; transition: transform 0.2s; }
                     .json-tree details[open] > summary::before { transform: rotate(90deg); }
                     .json-value { color: var(--text); }
                     .json-string { color: #6aab73; }
                 </style>"""
        def build_node(obj, key):
            if isinstance(obj, dict):
                inner = "".join(build_node(v, k) for k, v in obj.items())
                return f"<details open><summary>{key} {{}}</summary>{inner}</details>"
            elif isinstance(obj, list):
                inner = "".join(build_node(item, f"[{i}]") for i, item in enumerate(obj))
                return f"<details open><summary>{key} []</summary>{inner}</details>"
            else:
                val_str = f'"{obj}"' if isinstance(obj, str) else str(obj)
                val_class = "json-string" if isinstance(obj, str) else "json-value"
                return f'<div style="margin-left: 1.2rem;"><span style="color: var(--text_muted);">{key}:</span> <span class="{val_class}">{val_str}</span></div>'

        return f"{css}<div class='json-tree'>{build_node(data, name)}</div>"