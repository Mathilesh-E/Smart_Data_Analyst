import subprocess
import time
import requests
import json
import websocket
import base64
import os

out_dir = r'C:\Users\Mathi\OneDrive\Documents\Smart_Data_Analyst_Enhanced\report_screenshots'
os.makedirs(out_dir, exist_ok=True)

# Kill any existing chrome processes
subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], capture_output=True)
time.sleep(1)

chrome_cmd = [
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    '--headless=new',
    '--incognito',
    '--remote-debugging-port=9222',
    '--window-size=1600,1050',
    '--hide-scrollbars',
    '--disable-gpu',
    '--no-sandbox'
]
proc = subprocess.Popen(chrome_cmd)
time.sleep(2)

def cdp_send(ws, method, params=None):
    msg = {'id': int(time.time()*1000) % 1000000, 'method': method}
    if params:
        msg['params'] = params
    ws.send(json.dumps(msg))
    while True:
        res = json.loads(ws.recv())
        if res.get('id') == msg['id']:
            return res

def capture_page(target_url, filename, wait_time=4.0, js_action=None):
    print(f"--> Capturing {filename}...")
    new_tab = requests.put('http://127.0.0.1:9222/json/new').json()
    ws_url = new_tab['webSocketDebuggerUrl']
    tab_id = new_tab['id']
    ws = websocket.create_connection(ws_url, timeout=30)
    
    cdp_send(ws, 'Page.enable')
    cdp_send(ws, 'Runtime.enable')
    cdp_send(ws, 'Page.navigate', {'url': target_url})
    
    time.sleep(wait_time)
    
    if js_action:
        cdp_send(ws, 'Runtime.evaluate', {'expression': js_action})
        time.sleep(1.5)
        
    res = cdp_send(ws, 'Page.captureScreenshot', {'format': 'png'})
    img_data = base64.b64decode(res['result']['data'])
    
    out_path = os.path.join(out_dir, filename)
    with open(out_path, 'wb') as f:
        f.write(img_data)
    print(f"    Saved {filename}: {len(img_data)} bytes")
    
    ws.close()
    try:
        requests.get(f'http://127.0.0.1:9222/json/close/{tab_id}')
    except Exception:
        pass

targets = [
    ('http://127.0.0.1:8501/?welcome=1&theme=light', 'fig07_app_shell_welcome.png', 2.5, None),
    ('http://127.0.0.1:8501/?welcome=1&theme=light', 'fig12_welcome_screen.png', 2.5, None),
    ('http://127.0.0.1:8501/?page=overview&sample=retail_sales.csv&theme=light', 'fig14_overview_retail.png', 4.0, None),
    ('http://127.0.0.1:8501/?page=overview&sample=retail_sales.csv&theme=light', 'fig15_overview_slicer.png', 4.0, "document.querySelector('.dashboard-filter-actions .btn-quiet')?.click();"),
    ('http://127.0.0.1:8501/?page=explorer&sample=retail_sales.csv&theme=light', 'fig16_data_explorer.png', 4.0, None),
    ('http://127.0.0.1:8501/?page=quality&sample=retail_sales.csv&theme=light', 'fig17_data_quality.png', 4.0, None),
    ('http://127.0.0.1:8501/?page=cleaning&sample=retail_sales.csv&theme=light', 'fig18_cleaning_studio.png', 4.0, None),
    ('http://127.0.0.1:8501/?page=charts&sample=retail_sales.csv&theme=light', 'fig19_chart_studio.png', 4.5, None),
    ('http://127.0.0.1:8501/?page=workbench&sample=retail_sales.csv&theme=light', 'fig20_analysis_workbench.png', 4.5, None),
    ('http://127.0.0.1:8501/?page=insights&sample=retail_sales.csv&theme=light', 'fig21_insights.png', 4.0, None),
    ('http://127.0.0.1:8501/?page=statistics&sample=student_performance.csv&theme=light', 'fig22_statistical_lab.png', 4.5, None),
    ('http://127.0.0.1:8501/?page=ml&sample=student_performance.csv&theme=light', 'fig23_ml_lab.png', 5.0, None),
    ('http://127.0.0.1:8501/?page=segments&sample=student_performance.csv&theme=light', 'fig24_segments_anomalies.png', 4.5, None),
    ('http://127.0.0.1:8501/?page=timeseries&sample=retail_sales.csv&theme=light', 'fig25_time_series.png', 4.5, None),
    ('http://127.0.0.1:8501/?page=reports&sample=retail_sales.csv&theme=light', 'fig26_reports_exports.png', 4.0, None),
    ('http://127.0.0.1:8501/?page=overview&sample=retail_sales.csv&theme=dark', 'fig28_dark_theme.png', 4.0, None),
    ('http://127.0.0.1:8501/?page=overview&sample=retail_sales.csv&theme=light', 'fig29_light_theme.png', 4.0, None),
    ('http://127.0.0.1:8501/?page=overview&sample=student_performance.csv&theme=light', 'fig30_student_overview.png', 4.0, None),
    ('http://127.0.0.1:8501/?page=overview&sample=healthcare_sample.csv&theme=light', 'fig31_healthcare_overview.png', 4.0, None),
    ('http://127.0.0.1:8501/?page=overview&sample=flight_delays.csv&theme=light', 'fig32_flight_delays_overview.png', 4.0, None),
]

try:
    for url, fn, wait, js in targets:
        capture_page(url, fn, wait, js)
    print("\nAll screenshots captured successfully!")
finally:
    proc.terminate()
