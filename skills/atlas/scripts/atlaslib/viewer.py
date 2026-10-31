"""Standalone local report; repository data is never interpreted as HTML."""
import json
import pathlib
import base64
import os


def render(graph, output):
    data = json.dumps(graph, ensure_ascii=True).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    template = pathlib.Path(__file__).with_name('viewer.html').read_text()
    if graph.get('workspace', {}).get('connection'):
        template = template.replace("connect-src 'none'", "connect-src 'self'")
    css = pathlib.Path(__file__).with_name('viewer.css').read_text()
    font = (pathlib.Path(__file__).parent / 'assets/plex-sans.woff2').read_bytes()
    css = css.replace('ATLAS_FONT_DATA', base64.b64encode(font).decode())
    vietnamese_font = (pathlib.Path(__file__).parent / 'assets/plex-sans-vietnamese.woff2').read_bytes()
    css = css.replace('ATLAS_VIETNAMESE_FONT_DATA', base64.b64encode(vietnamese_font).decode())
    js = pathlib.Path(__file__).with_name('viewer.js').read_text()
    d3 = (pathlib.Path(__file__).parent / 'assets/d3.min.js').read_text()
    if output.is_symlink():
        raise ValueError('Refusing symlinked HTML output.')
    descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'w') as file:
        file.write(template.replace('ATLAS_STYLE_DATA', css).replace('ATLAS_GRAPH_DATA', data).replace('ATLAS_SCRIPT_DATA', js).replace('ATLAS_D3_DATA', d3))
