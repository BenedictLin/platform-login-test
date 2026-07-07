# 平台自動化登入測試

平台 QA 工程師面試作業 - 第二題（加分項）

## 🛠️ 技術棧

- **語言**：Python 3.13
- **框架**：Playwright 1.60.0、pytest 8.3.4
- **架構**：Page Object Model (POM)

## 📦 安裝

### 步驟 1：Clone 專案
```bash
git clone https://github.com/BenedictLin/platform-login-test.git
cd platform-login-test
```

### 步驟 2：安裝依賴
```bash
pip install -r requirements.txt
playwright install chromium
```

### 步驟 3：設定環境變數
複製 `.env.example` 為 `.env`，並填入你的測試帳號和密碼：
```bash
SWAG_USERNAME=your_email@example.com
SWAG_PASSWORD=your_password
```

## 🚀 執行測試

```bash
# 執行全量測試（正向 + 反向案例）
pytest test_login.py

# 執行特定測試
pytest test_login.py::test_login_success -v -s
pytest test_login.py::test_login_fail -v -s
```

## 💡 設計取捨說明

### 為什麼採用 Hybrid 混合式方案？

初期嘗試了**憑證注入方案**（備份 token 到 auth.json → 在新瀏覽器注入），成功儲存 token，但刷新頁面後前端自動清除 token。推測前端有安全驗證機制，會在檢測到異常登入環境時清除憑證。

因此改採 **Hybrid 混合策略**：
- **Playwright 自動化**：填寫帳號、密碼並送出
- **人工介入**：停頓 45 秒，手動完成 GeeTest 驗證碼
- **自動化驗證**：驗證碼通過後，檢查大頭貼或錯誤訊息

### 選擇大頭貼圖片作為登入成功斷言
- 不受語言變動影響
- 不受加載延遲影響  
- 代表已進入首頁，登入確實成功

### 使用正則表達式匹配錯誤訊息
應對表單紅字與 Toast 同時出現的情況，提高定位穩定性。

### 避免 Sleep 硬等
全程使用 `wait_for()` 動態監聽元件，而非固定時間等待。

### 環境變數管理
帳號密碼以 `.env` 管理，不寫死在程式碼中，提高安全性。
