"""Standalone local report; repository data is never interpreted as HTML."""
import json
import pathlib


def render(graph, output):
    data = json.dumps(graph, ensure_ascii=True).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    template = pathlib.Path(__file__).with_name('viewer.html').read_text()
    output.write_text(template.replace('ATLAS_GRAPH_DATA', data))
