import re

with open('web_app/static/index.html', 'r') as f:
    html = f.read()

# Add SEO meta tags
seo_tags = """
    <meta name="description" content="Rojger Downloader is the ultimate universal media acquisition tool. Download videos from 1000+ sites including YouTube, Instagram, Facebook, TikTok, XHamster, and more in HD lossless quality. No logs, zero disk usage, absolute speed.">
    <meta name="keywords" content="video downloader, universal downloader, download videos, youtube downloader, instagram reel downloader, tiktok downloader, facebook downloader, hd video downloader, xhamster downloader, media acquisition">
    <meta name="robots" content="index, follow">
    <link rel="canonical" href="https://rojgar.site">
"""

if "meta name=\"description\"" not in html:
    html = html.replace('<title>', seo_tags.lstrip() + '    <title>')

# Read modal content
with open('sites_modal.html', 'r') as f:
    modal_html = f.read()

# Inject modal just before closing body if not present
if "sites-modal" not in html:
    html = html.replace('</body>', f'    {modal_html}\n\n    <script>\n        function openSitesModal() {{\n            document.getElementById("sites-modal").classList.remove("opacity-0", "pointer-events-none");\n            document.getElementById("sites-modal-content").classList.remove("scale-95");\n        }}\n        function closeSitesModal() {{\n            document.getElementById("sites-modal").classList.add("opacity-0", "pointer-events-none");\n            document.getElementById("sites-modal-content").classList.add("scale-95");\n        }}\n    </script>\n</body>')

# Update icon click handler
html = html.replace(
    '<div class="w-16 h-16 rounded-full glass border border-primary/20 flex flex-col items-center justify-center group hover:scale-110 bg-primary/5 transition-all cursor-pointer shadow-sm">',
    '<div onclick="openSitesModal()" class="w-16 h-16 rounded-full glass border border-primary/20 flex flex-col items-center justify-center group hover:scale-110 bg-primary/5 transition-all cursor-pointer shadow-sm">'
)

with open('web_app/static/index.html', 'w') as f:
    f.write(html)
