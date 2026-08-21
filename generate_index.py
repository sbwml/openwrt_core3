import os
import html
import urllib.parse
from datetime import datetime

EXCLUDE_FILES = ['index.html', 'generate_index.py', 'commit_msg.txt', 'CNAME']

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
    <title>Index of {directory_plain}</title>
    <style>
        :root {{
            --bg-color: #fafafa;
            --card-bg: #ffffff;
            --text-main: #202124;
            --text-sub: #5f6368;
            --link-color: #1a73e8;
            --border-color: #f0f0f0;
            --hover-bg: #f8f9fa;
        }}

        * {{
            box-sizing: border-box;
        }}

        html, body {{
            height: 100%;
        }}

        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 12px 12px 0 12px;
            color: var(--text-main); 
            background-color: var(--bg-color); 
            line-height: 1.5;
            display: flex;
            flex-direction: column;
        }}

        .main-content {{
            flex: 1 0 auto;
            width: 100%;
        }}

        .container {{ 
            background: var(--card-bg); 
            border-radius: 8px; 
            box-shadow: 0 1px 3px rgba(0,0,0,0.1); 
            padding: 16px; 
            max-width: 1000px; 
            margin: 0 auto; 
        }}

        .breadcrumbs-wrapper {{
            overflow-x: auto;
            white-space: nowrap;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid #e0e0e0;
            -webkit-overflow-scrolling: touch;
        }}

        .breadcrumbs {{ 
            font-size: 16px; 
            color: var(--text-main); 
            font-weight: 400; 
            display: inline-block;
        }}

        .breadcrumbs a {{ 
            color: var(--link-color); 
            text-decoration: none; 
        }}

        .breadcrumbs a:hover {{ 
            text-decoration: underline; 
        }}

        .breadcrumbs .separator {{ 
            margin: 0 4px; 
            color: var(--text-sub); 
            user-select: none; 
        }}

        .table-responsive {{
            width: 100%;
            overflow-x: auto;
        }}

        table {{ 
            width: 100%; 
            border-collapse: collapse; 
            text-align: left; 
            table-layout: fixed;
        }}

        th, td {{ 
            padding: 12px 8px; 
            border-bottom: 1px solid var(--border-color); 
            word-break: break-word;
        }}

        th {{ 
            font-weight: 600; 
            color: var(--text-sub); 
            background-color: #f8f9fa; 
            font-size: 13px;
            cursor: pointer;
            user-select: none;
            transition: background-color 0.2s;
        }}

        th:hover {{
            background-color: #e8eaed;
            color: var(--text-main);
        }}

        th::after {{
            content: ' ↕';
            opacity: 0.3;
            font-size: 11px;
        }}

        th.asc::after {{
            content: ' ▲';
            opacity: 1;
            color: var(--link-color);
        }}

        th.desc::after {{
            content: ' ▼';
            opacity: 1;
            color: var(--link-color);
        }}

        tr:hover {{ 
            background-color: var(--hover-bg); 
        }}

        .col-name {{ width: 55%; }}
        .col-date {{ width: 25%; }}
        .col-size {{ width: 20%; }}

        td a {{ 
            color: var(--link-color); 
            text-decoration: none; 
            font-weight: 500; 
            display: block; 
            width: 100%;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}

        td a:hover {{ 
            text-decoration: underline; 
        }}

        .parent-dir {{ 
            font-weight: bold; 
            color: var(--text-sub); 
        }}

        .size, .date {{ 
            color: var(--text-sub); 
            font-size: 13px; 
        }}

        .footer {{
            flex-shrink: 0;
            text-align: center;
            padding: 20px 0;
            font-size: 13px;
            color: var(--text-sub);
        }}

        .footer a {{
            color: var(--text-sub);
            text-decoration: underline;
        }}

        .footer a:hover {{
            color: var(--link-color);
        }}

        @media (max-width: 600px) {{
            body {{
                padding: 8px 8px 0 8px;
            }}

            .container {{
                padding: 12px;
                border-radius: 6px;
            }}

            .breadcrumbs {{
                font-size: 15px;
            }}

            th, td {{
                padding: 10px 4px;
            }}

            .col-date, .date {{
                display: none;
            }}

            .col-name {{ width: 70%; }}
            .col-size {{ width: 30%; text-align: right; }}
            th.col-size {{ text-align: right; }}

            td a {{
                padding: 4px 0;
            }}

            .footer {{
                padding: 16px 0;
                font-size: 12px;
            }}
        }}
    </style>
</head>
<body>
    <div class="main-content">
        <div class="container">
            <div class="breadcrumbs-wrapper">
                <div class="breadcrumbs">
                    {breadcrumbs}
                </div>
            </div>
            <div class="table-responsive">
                <table id="file-table">
                    <thead>
                        <tr>
                            <th class="col-name" onclick="sortTable(0, 'string')">Name</th>
                            <th class="col-date" onclick="sortTable(1, 'number')">Last Modified</th>
                            <th class="col-size" onclick="sortTable(2, 'number')">Size</th>
                        </tr>
                    </thead>
                    <tbody>
                        {parent_row}
                        {rows}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    <footer class="footer">
        Powered by <a href="https://pages.github.com/" target="_blank" rel="noopener">GitHub Pages</a> | Served by EdgeOne
    </footer>
    <script>
        let sortDirections = [true, true, true];

        function sortTable(colIndex, type) {{
            const table = document.getElementById("file-table");
            const tbody = table.querySelector("tbody");
            const rows = Array.from(tbody.querySelectorAll("tr"));
            const headers = table.querySelectorAll("th");

            let parentRow = null;
            if (rows.length > 0 && rows[0].querySelector(".parent-dir")) {{
                parentRow = rows.shift();
            }}

            const isAscending = sortDirections[colIndex];
            sortDirections[colIndex] = !isAscending;

            headers.forEach((h, idx) => {{
                if (idx === colIndex) {{
                    h.classList.remove("asc", "desc");
                    h.classList.add(isAscending ? "asc" : "desc");
                }} else {{
                    h.classList.remove("asc", "desc");
                }}
            }});

            rows.sort((rowA, rowB) => {{
                const cellA = rowA.children[colIndex];
                const cellB = rowB.children[colIndex];

                let valA = cellA.getAttribute("data-sort") || cellA.textContent.trim();
                let valB = cellB.getAttribute("data-sort") || cellB.textContent.trim();

                if (type === "number") {{
                    valA = parseFloat(valA) || 0;
                    valB = parseFloat(valB) || 0;
                }} else {{
                    valA = valA.toLowerCase();
                    valB = valB.toLowerCase();
                }}

                if (valA < valB) return isAscending ? -1 : 1;
                if (valA > valB) return isAscending ? 1 : -1;
                return 0;
            }});

            tbody.innerHTML = "";
            if (parentRow) tbody.appendChild(parentRow);
            rows.forEach(row => tbody.appendChild(row));
        }}
    </script>
</body>
</html>
"""

def get_readable_size(size_in_bytes):
    if size_in_bytes >= 1024 * 1024:
        return f"{size_in_bytes / (1024 * 1024):.2f} MiB"
    elif size_in_bytes >= 1024:
        return f"{size_in_bytes / 1024:.2f} KiB"
    return f"{size_in_bytes} B"

def make_breadcrumbs(rel_path):
    if rel_path == ".":
        return "<span>Index of /</span>"
        
    parts = [p for p in rel_path.split(os.sep) if p and p != "."]
    total_parts = len(parts)
    
    html_snippets = ['<a href="' + '../' * total_parts + '">Index of</a>']
    
    for i, part in enumerate(parts):
        if i == total_parts - 1:
            html_snippets.append(f"<span>{html.escape(part)}</span>")
        else:
            back_depth = "../" * (total_parts - 1 - i)
            html_snippets.append(f'<a href="{back_depth}">{html.escape(part)}</a>')
            
    return '<span class="separator">/</span>'.join(html_snippets) + '<span class="separator">/</span>'

def generate_repo_indexes(base_dir):
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if not d.startswith('.')]

        rel_path = os.path.relpath(root, base_dir)
        display_path = "/" if rel_path == "." else f"/{rel_path}/"
        
        breadcrumbs_html = make_breadcrumbs(rel_path)
        
        parent_row = ""
        if rel_path != ".":
            parent_row = '<tr><td class="col-name"><a class="parent-dir" href="../">📁 ..</a></td><td class="date" data-sort="0">-</td><td class="size" data-sort="-1">-</td></tr>'
            
        rows = []
        
        for d in sorted(dirs):
            dir_path = os.path.join(root, d)
            mtime_obj = os.path.getmtime(dir_path)
            mtime_str = datetime.fromtimestamp(mtime_obj).strftime('%Y-%m-%d %H:%M')
            quoted_name = urllib.parse.quote(d)
            rows.append(
                f'<tr>'
                f'<td class="col-name" data-sort="0_{html.escape(d)}"><a href="{quoted_name}/">📂 {html.escape(d)}/</a></td>'
                f'<td class="date" data-sort="{mtime_obj}">{mtime_str}</td>'
                f'<td class="size" data-sort="-1">-</td>'
                f'</tr>'
            )
            
        for f in sorted(files):
            if f in EXCLUDE_FILES or f.startswith('.'): 
                continue
                
            file_path = os.path.join(root, f)
            mtime_obj = os.path.getmtime(file_path)
            mtime_str = datetime.fromtimestamp(mtime_obj).strftime('%Y-%m-%d %H:%M')
            size_bytes = os.path.getsize(file_path)
            size_str = get_readable_size(size_bytes)
            quoted_name = urllib.parse.quote(f)
            rows.append(
                f'<tr>'
                f'<td class="col-name" data-sort="1_{html.escape(f)}"><a href="{quoted_name}">📄 {html.escape(f)}</a></td>'
                f'<td class="date" data-sort="{mtime_obj}">{mtime_str}</td>'
                f'<td class="size" data-sort="{size_bytes}">{size_str}</td>'
                f'</tr>'
            )
            
        html_content = TEMPLATE.format(
            directory_plain=html.escape(display_path),
            breadcrumbs=breadcrumbs_html,
            parent_row=parent_row,
            rows="\n".join(rows)
        )
        
        with open(os.path.join(root, 'index.html'), 'w', encoding='utf-8') as f_out:
            f_out.write(html_content)

if __name__ == "__main__":
    generate_repo_indexes(".")
