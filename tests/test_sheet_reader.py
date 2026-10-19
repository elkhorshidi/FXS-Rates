import unittest
from unittest.mock import Mock, patch
from sheet_reader import standard_urls, validate_published_url, parse_google_csv, download_public_sheet, SheetAccessError

class ReaderTests(unittest.TestCase):
    def test_default_contains_target_gid(self):
        url=standard_urls()[0]
        self.assertIn("gid=982784865",url)
        self.assertIn("format=csv",url)
    def test_csv_persian(self):
        raw=('زمان استعلام (تهران),نوع مسیر,نام منبع / بانک,نرخ خام (تومان/دلار),کارمزد اظهار (%)\n'
             '18/10/2026 21:03,بازار آزاد,بازار,"262,000",0\n').encode('utf-8-sig')
        rows=parse_google_csv(raw)
        self.assertEqual(rows[1][3],'262,000')
    def test_html_not_misidentified_as_csv(self):
        with self.assertRaises(SheetAccessError):
            parse_google_csv(b'<!DOCTYPE html><html>Sign in</html>')
    def test_restrict_urls(self):
        with self.assertRaises(ValueError):
            validate_published_url('https://example.com/data.csv')
    @patch('sheet_reader.requests.get')
    def test_requests_no_secrets(self,m):
        mock=Mock(status_code=200,content=('timestamp,نوع مسیر,source,raw,fee\n'
                         '2026-10-19,بانک,ملی,247000,0.6\n').encode('utf-8'))
        mock.raise_for_status.return_value=None
        m.return_value=mock
        rows,url=download_public_sheet()
        self.assertEqual(rows[1][2],'ملی')
        self.assertTrue(url.startswith('https://docs.google.com/'))
        m.assert_called_once()
    @patch('sheet_reader.requests.get')
    def test_no_public_access(self,m):
        m.return_value=Mock(status_code=403)
        with self.assertRaisesRegex(SheetAccessError,'Anyone with the link'):
            download_public_sheet()

if __name__=='__main__': unittest.main()
