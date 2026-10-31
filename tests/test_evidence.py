import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'skills/atlas/scripts'))
from atlaslib.evidence import sanitize
from atlaslib.viewer import render


class EvidenceTest(unittest.TestCase):
    def test_redaction_preserves_structured_metadata_and_scrubs_literal_values(self):
        record = {'argv': ['tool', '--token=arbitrary-sensitive-value'], 'nested': {'message': 'password=secret-value'}}
        value = sanitize(record)
        self.assertEqual(value['argv'][1], '--token=[REDACTED]')
        self.assertEqual(value['nested']['message'], 'password=[REDACTED]')
        self.assertEqual(json.loads(json.dumps(value)), value)

    def test_html_cannot_break_out_of_graph_data_script(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            output = pathlib.Path(directory) / 'report.html'
            render({'nodes': [{'label': '</script><script>alert(1)</script>'}]}, output)
            html = output.read_text()
            self.assertNotIn('</script><script>alert(1)</script>', html)
            self.assertNotIn('innerHTML', html)
