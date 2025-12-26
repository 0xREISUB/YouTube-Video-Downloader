import unittest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from downloader import fetch_metadata, run_downloader

class TestPlaylistSelection(unittest.TestCase):
    
    @patch('downloader.yt_dlp.YoutubeDL')
    def test_fetch_metadata_playlist(self, mock_ydl):
        # Mock yt_dlp instance
        mock_instance = mock_ydl.return_value
        mock_instance.__enter__.return_value = mock_instance
        
        # Mock extracted info
        mock_instance.extract_info.return_value = {
            'entries': [
                {'title': 'Video 1', 'id': 'v1'},
                {'title': 'Video 2', 'id': 'v2'},
                {'title': 'Video 3', 'id': 'v3'}
            ],
            'title': 'Test Playlist'
        }
        
        result = fetch_metadata('http://playlist')
        
        self.assertEqual(result['type'], 'playlist')
        self.assertEqual(len(result['entries']), 3)
        self.assertEqual(result['entries'][0]['index'], 1)
        self.assertEqual(result['entries'][0]['title'], 'Video 1')
        self.assertEqual(result['entries'][2]['index'], 3)
        self.assertEqual(result['entries'][2]['id'], 'v3')

    @patch('downloader.yt_dlp.YoutubeDL')
    def test_run_downloader_filtering(self, mock_ydl):
        # We need to spy on what gets downloaded.
        # run_downloader creates a new ydl instance for download.
        
        mock_instance = mock_ydl.return_value
        mock_instance.__enter__.return_value = mock_instance
        
        # 1. extract_flat call
        mock_instance.extract_info.return_value = {
            'entries': [
                {'url': 'http://v1', 'title': 'V1'},
                {'url': 'http://v2', 'title': 'V2'},
                {'url': 'http://v3', 'title': 'V3'}
            ],
            'title': 'Test Playlist'
        }
        
        # Mock socketio
        mock_socket = MagicMock()
        
        # Run with filtered indices [1, 3]
        # Note: We need to mock the download call to avoid actual download
        # run_downloader calls download() on a NEW instance inside the loop.
        # Since we mocked the class, all instances are our mock.
        
        run_downloader(mock_socket, 'http://playlist', '/tmp', '720', 'sid', selected_indices=[1, 3])
        
        # Verify download was called only for v1 and v3
        # The code iterates entries.
        # It creates a new YDL for each download.
        # ydl.download(['http://v1'])
        
        # Check calls to download
        # Logic: 
        # 1. extract_flat (happens once)
        # 2. explicit video info extraction for format selection (happens inside loop) -> extract_info(url)
        # 3. download([url])
        
        # Let's check download calls
        download_calls = [c[0][0] for c in mock_instance.download.call_args_list]
        # download args is a list of urls: [['http://v1']]
        
        downloaded_urls = [args[0] for args in download_calls]
        
        self.assertIn('http://v1', downloaded_urls)
        self.assertIn('http://v3', downloaded_urls)
        self.assertNotIn('http://v2', downloaded_urls)
        
        # Verify socket emit done mentions 2 items
        done_call = [c for c in mock_socket.emit.call_args_list if c[0][0] == 'done']
        self.assertTrue(done_call)
        self.assertIn('2/2', done_call[0][0][1]['msg'])

if __name__ == '__main__':
    unittest.main()
