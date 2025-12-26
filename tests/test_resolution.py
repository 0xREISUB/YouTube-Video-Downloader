import unittest
import sys
import os

# Add parent directory to path to import downloader
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from downloader import select_format

class TestResolutionSelection(unittest.TestCase):
    def setUp(self):
        self.formats = [
            {'format_id': '240p', 'height': 240, 'vcodec': 'avc1'},
            {'format_id': '360p', 'height': 360, 'vcodec': 'avc1'},
            {'format_id': '480p', 'height': 480, 'vcodec': 'vp9'},
            {'format_id': '720p', 'height': 720, 'vcodec': 'avc1'},
            {'format_id': '1080p', 'height': 1080, 'vcodec': 'avc1'},
            {'format_id': '1440p', 'height': 1440, 'vcodec': 'vp9'},
            {'format_id': '4k', 'height': 2160, 'vcodec': 'vp9'},
            {'format_id': 'audio', 'height': None, 'vcodec': 'none'}, 
        ]

    def test_exact_match(self):
        self.assertEqual(select_format(self.formats, '1080'), '1080p')
        self.assertEqual(select_format(self.formats, 720), '720p')

    def test_higher_fallback(self):
        # Target 1000 (missing) -> Higher is 1080.
        self.assertEqual(select_format(self.formats, 1000), '1080p')
        
    def test_lower_fallback_from_above(self):
        # Target 3000 (missing). No higher.
        # Fallback to Lower. Best lower is 4k (2160).
        self.assertEqual(select_format(self.formats, 3000), '4k')
        
    def test_gap_logic(self):
        # Remove 1080p from list
        formats = [f for f in self.formats if f['format_id'] != '1080p']
        # Target 1080.
        # Exact: None.
        # Higher: 1440p exists. Should pick 1440p.
        self.assertEqual(select_format(formats, 1080), '1440p')
        
    def test_only_lower(self):
        # Only have small formats
        formats = [
            {'format_id': '240p', 'height': 240, 'vcodec': 'avc1'},
            {'format_id': '360p', 'height': 360, 'vcodec': 'avc1'},
        ]
        # Target 1080.
        # Higher: None.
        # Lower: 360p (best of lower).
        self.assertEqual(select_format(formats, 1080), '360p')

    def test_no_formats(self):
        self.assertEqual(select_format([], 1080), None)

if __name__ == '__main__':
    unittest.main()
