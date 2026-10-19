import io
import unittest
from unittest.mock import patch
from PIL import Image, ImageFont
from fx_core import parse_rates,latest_rates,compare
from report_image import make_png,_jalali_from_gregorian

class TestReport(unittest.TestCase):
    def test_png_on_pillow_without_libraqm(self):
        """Regression: deployed Streamlit Pillow raises KeyError on RTL direction."""
        vals=[['time','kind','source','rate','fee'],
              [46313.8774,'بازار آزاد','بازار',264000,0],
              [46313.8809,'کوتاژ','بازار',242000,0],
              [46313.8739,'بانک','ملی',246600,.6]]
        df,_=parse_rates(vals)
        latest=latest_rates(df)
        result,market=compare(latest,'بازار',100000)
        import report_image
        with patch.object(report_image.features, 'check_feature', return_value=False):
            # Use BASIC layout fonts, matching no-libraqm Pillow builds.
            normal=report_image.get_font_path('Regular')
            bold=report_image.get_font_path('Bold')
            paths={'Regular':normal,'Bold':bold}
            def basic_set(weight):
                name=paths.get(weight)
                return {size:ImageFont.truetype(name,size,layout_engine=ImageFont.Layout.BASIC)
                        for size in range(14,55)} if name else report_image.font_set(weight)
            with patch.object(report_image, 'font_set', side_effect=basic_set):
                png=make_png(result,market,latest[latest.kind=='بازار آزاد'].iloc[0].timestamp,'بازار',100000)
        im=Image.open(io.BytesIO(png))
        self.assertEqual(im.size,(1080,1350))
        self.assertEqual(im.format,'PNG')
        self.assertGreater(len(png),20000)

    def test_image_dimensions_and_farsi_calendar(self):
        vals=[['time','kind','source','rate','fee'],
              [46313.8774,'بازار آزاد','بازار',262000,0],
              [46313.8809,'کوتاژ','بازار',246000,0],
              [46313.8739,'بانک','ملی',247000,.6]]
        df,_=parse_rates(vals)
        latest=latest_rates(df)
        result,market=compare(latest,'بازار',100000)
        png=make_png(result,market,latest[latest.kind=='بازار آزاد'].iloc[0].timestamp,'بازار',100000)
        im=Image.open(io.BytesIO(png))
        self.assertEqual(im.size,(1080,1350))
        self.assertEqual(im.format,'PNG')
        self.assertEqual(_jalali_from_gregorian(2026,10,18),(1405,7,26))

if __name__=='__main__': unittest.main()
