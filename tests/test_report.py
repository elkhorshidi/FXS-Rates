import io
import unittest
from PIL import Image
from fx_core import parse_rates,latest_rates,compare
from report_image import make_png,_jalali_from_gregorian

class TestReport(unittest.TestCase):
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
