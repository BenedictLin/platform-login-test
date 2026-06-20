# save_auth.py
# 【已棄用的方案】本腳本用於嘗試「憑證注入」自動化方案
# 執行流程：手動登入 → 備份 IndexedDB & LocalStorage → 存為 auth.json
# 
# 嘗試結果：注入 Token 後刷新頁面，但 Token 被清除，無法維持登入狀態
# 最終採取 Hybrid 混合策略（手動過驗證碼 + 自動化斷言）
#
# 保留此檔案作為實驗記錄參考

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    # 1. 啟動參數加固：除了關閉控制旗標，同時禁用自動化擴充件
    browser = p.chromium.launch(
        headless=False,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--no-sandbox",
            "--disable-extensions"
        ]
    )
    
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        viewport={"width": 1440, "height": 900},
        locale="zh-TW",
        timezone_id="Asia/Taipei"
    )
    
    # 2. 注入高階防偵測腳本 (Stealth Script)：完美偽裝瀏覽器特徵環境
    context.add_init_script("""
        // 抹除 navigator.webdriver
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

        // 偽裝 window.chrome 物件，許多防爬蟲會檢查此物件是否存在
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {}
        };

        // 偽裝 navigator.plugins，防止因長度為 0 被 GeeTest 識破
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                { description: "Portable Document Format", filename: "internal-pdf-viewer", name: "Chrome PDF Viewer" },
                { description: "Chromium PDF Plugin", filename: "internal-pdf-viewer", name: "Chromium PDF Viewer" }
            ]
        });

        // 偽裝 navigator.languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['zh-TW', 'zh', 'en-US', 'en']
        });
    """)
    
    page = context.new_page()
    page.goto("https://swag.live/?lang=zh-TW")
    
    print("\n======================================================================")
    print("【操作指引】防偵測特徵已全數注入。請在瀏覽器中完成登入與滑塊驗證。")
    print("看到首頁出現「追蹤中」頁籤後，『不要關閉瀏覽器』，回到這裡按 Enter！")
    print("======================================================================\n")
    
    input("請手動完成登入後，回到這裡按 [Enter] 鍵儲存狀態...")
    
    print("正在執行 IndexedDB 全量打包 (Full Dump)...")
    
    full_dump_script = """
    (() => {
        return new Promise((resolve) => {
            const request = indexedDB.open('localforage');
            request.onsuccess = function(e) {
                const db = e.target.result;
                if (!db.objectStoreNames.contains('keyvaluepairs')) {
                    return resolve('NO_STORE');
                }
                const tx = db.transaction('keyvaluepairs', 'readonly');
                const store = tx.objectStore('keyvaluepairs');
                const getAllKeys = store.getAllKeys();
                const getAllValues = store.getAll();
                
                getAllKeys.onsuccess = function() {
                    getAllValues.onsuccess = function() {
                        const dump = {};
                        for (let i = 0; i < getAllKeys.result.length; i++) {
                            dump[getAllKeys.result[i]] = getAllValues.result[i];
                        }
                        localStorage.setItem('INDEXEDDB_FULL_DUMP', JSON.stringify(dump));
                        resolve('DUMP_SUCCESS');
                    };
                };
            };
        });
    })()
    """
    res = page.evaluate(full_dump_script)
    print(f"資料庫備份狀態：{res}")
    
    page.wait_for_timeout(1500)
    context.storage_state(path="auth.json")
    browser.close()
    print("【成功】auth.json 錄製完成，已封裝完整儲存層快照。")
