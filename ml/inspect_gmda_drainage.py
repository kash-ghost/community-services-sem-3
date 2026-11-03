# -*- coding: utf-8 -*-
import requests, ssl
from urllib3.util.ssl_ import create_urllib3_context

class LegacyRenegotiationAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.options |= 0x4
        kwargs['ssl_context'] = ctx
        return super().init_poolmanager(*args, **kwargs)

s = requests.Session()
s.mount('https://', LegacyRenegotiationAdapter())

services = [
    'Water_Infrastructure_with_Runoff/MapServer',
    'FMDA_Master_SWD_D/MapServer',
    'flood_survey_2/FeatureServer',
    'Utilities_Services/MapServer',
    'Harsac_waterlog/MapServer'
]

for sname in services:
    try:
        r = s.get(f'https://onemapdepts.gmda.gov.in/server/rest/services/{sname}?f=json', timeout=15)
        if r.status_code == 200:
            d = r.json()
            print(f'=== {sname} ===')
            for lyr in d.get('layers', []):
                print(f"  [{lyr.get('id')}] {lyr.get('name')}")
    except Exception as e:
        print(f"Failed {sname}: {e}")
