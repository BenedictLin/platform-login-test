# SWAG 平台自動化登入測試

本專案為 SWAG 平台 QA 工程師面試作業之第二題（加分項）。

採用 **Page Object Model (POM)** 架構設計，結合 **Hybrid 混合式自動化策略**。

---

## 📋 專案概述

### 測試目標
- 驗證 SWAG 平台登入成功的 UI 表現（大頭貼圖片出現）
- 驗證登入失敗時的錯誤提示（密碼/帳號錯誤訊息）

### 為什麼是混合式自動化？

#### 初期嘗試：憑證注入方案

1. **第一步**：執行 `save_auth.py` 手動登入，使用 IndexedDB dump 腳本將 `_accessToken` 和 `_refreshToken` 備份到 localStorage
2. **結果**：成功儲存，auth.json 中確實包含完整的 JWT token 值
3. **測試**：在無痕窗口注入 token 後刷新頁面，期望直接進入登入狀態
4. **失敗現象**：刷新後，前端偵測到異常登入行為，自動將 token 清除為 `undefined`，阻斷進站

推測 SWAG 前端具有安全驗證機制，會在檢測到異常登入環境時清除憑證。

#### 最終方案：Hybrid 混合策略

因此改採 **Hybrid 混合策略**：
1. **Playwright 自動化**：填寫帳號、密碼表單並送出
2. **人工介入點**：停頓 45 秒，讓測試者手動滑動 GeeTest 驗證碼
3. **自動化接手**：驗證碼通過後，進行 UI 狀態斷言

---

## 🛠️ 開發環境與安裝

### 系統要求
- Python 3.10+
- pip 套件管理

### 步驟 1：Clone 專案
```bash
git clone https://github.com/BenedictLin/SWAG-QA-.git
cd SWAG-QA-
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

---

## 🚀 快速開始

### 步驟 4：執行測試

```bash
# 執行全量測試（正向 + 反向案例）
pytest test_login.py

# 執行特定測試
pytest test_login.py::test_login_success -v -s
pytest test_login.py::test_login_fail -v -s
```

### 3. 測試流程

#### ✅ test_login_success（正向測試）
1. 自動化填寫帳號、密碼並點擊「登入」
2. GeeTest 驗證碼出現，測試卡住，Console 提示「請在 45 秒內手動完成滑塊拼圖」
3. **人工操作**：在瀏覽器中手動滑動驗證碼
4. 驗證碼通過後，自動化檢查大頭貼圖片是否出現
5. 若出現 ✅ **PASS**，若 45 秒內未出現 ❌ **FAIL**

#### ❌ test_login_fail（反向測試）
1. 自動化填寫帳號、**錯誤密碼**並點擊「登入」
2. GeeTest 驗證碼出現，測試卡住，Console 提示「請在 45 秒內手動完成滑塊拼圖」
3. **人工操作**：在瀏覽器中手動滑動驗證碼
4. 驗證碼通過後，後端拋回登入失敗，前端顯示錯誤提示（表單紅字 + 下方 Toast）
5. 自動化檢查錯誤訊息是否出現
6. 若出現 ✅ **PASS**，若 45 秒內未出現 ❌ **FAIL**

---

## 💡 技術決策與架構說明

### 1. Page Object Model (POM) 架構

```python
class SwagLoginPage:
    """封裝登入頁面的操作與定位"""
    - login_entry_btn        # 進站限制牆的登入入口
    - login_others_btn       # 帳號密碼登入按鈕
    - username_input         # 帳號輸入框
    - password_input         # 密碼輸入框
    - submit_btn            # 提交按鈕
    - success_avatar        # 登入成功斷言目標（大頭貼圖片）
    - error_message         # 登入失敗斷言目標（錯誤訊息）
```

**優勢**：
- 集中管理 DOM 定位
- 定位策略變動時只需修改一處
- 測試邏輯與 UI 結構分離

### 2. 防禦性定位策略 (Scoping Locator)

#### 破開進站限制牆
```python
# ❌ 問題做法
page.locator('button[data-element_id="button-login"]').click()  # 會命中多個重複元件

# ✅ 防禦做法
page.locator("[class*='HeaderActionsWrapper'] button[data-element_id='button-login']").click()
```
用父容器 `HeaderActionsWrapper` 限縮範圍，精準命中桌面版入口。

#### 正向登入斷言
```python
self.success_avatar = page.locator("[class*='DesktopOnlySection'] button[data-element_id='tab-button-hamburger'] img[data-key='target']")
```
鎖定導覽列內的實體大頭貼圖片，不受語言變動或加載延遲影響。

#### 反向登入斷言
```python
self.error_message = page.locator("text=/.*(密碼|帳號).*錯誤.*/").first
```
使用正則表達式文字匹配，應對表單紅字與下方 Toast 同時出現的情況。

### 3. 等待策略

```python
login_page.success_avatar.wait_for(state="visible", timeout=45000)
```

使用 `wait_for()` 監聽元件出現，而非硬等待固定時間。45 秒預留給人工手動滑驗證碼的時間。

### 4. 反爬蟲對抗

```python
context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")
browser.launch(args=["--disable-blink-features=AutomationControlled"])
```

移除 Playwright 的自動化特徵標記。

---

## 📊 測試結果範例

### 執行成功（正向測試）
```
pytest test_login_gemini.py::test_login_success -v -s

[INFO] 正向測試驗證碼已觸發。請在 45 秒內『手動完成滑塊拼圖』以驗證成功登入態...
PASS - Login successful
```

### 執行成功（反向測試）
```
pytest test_login_gemini.py::test_login_fail -v -s

[INFO] 反向測試驗證碼已觸發。請在 45 秒內『手動完成滑塊拼圖』以驗證錯誤提示...
PASS - Login correctly failed and UI error message verified
```

## ⚠️ 關於人工介入點

本專案在 GeeTest 驗證碼處停頓 45 秒，讓測試者手動完成滑塊驗證。

**為什麼無法自動化過 GeeTest？**
- GeeTest 驗證碼的 token（`x-geetest-pass-token`）為一次性，無法重複使用
- 本專案嘗試過憑證注入方案，成功儲存了 token 到 auth.json，但在新瀏覽器注入並刷新時，前端會自動清除 token
- 無法找到可行的自動化方案

**為什麼採用混合式？**
- 這是目前唯一可行的方案
- 自動化部分（表單填寫、送出、驗證成功/失敗）仍由 Playwright 執行
- 只有驗證碼部分需要人工協助

---

| 項目 | 做法 | 原因 |
|-----|------|------|
| 驗證碼處理 | 混合式（人工 + 自動化） | 無法繞過 GeeTest，憑證注入方案失敗 |
| 登入成功判定 | 大頭貼圖片出現 | 不受語言或加載延遲影響 |
| 登入失敗判定 | 錯誤訊息文字匹配 | 相容表單紅字與 Toast 同時出現 |
| 帳密管理 | 環境變數 | 不寫死程式碼 |
| 架構設計 | POM | 集中管理定位，易於維護 |

---

## 📝 故障排除

### 測試卡在驗證碼等待，但沒看到提示信息
確保執行時加上 `-s` 參數以看到 print 輸出：
```bash
pytest test_login_gemini.py -v -s
```

### 超時後仍未登入成功
可能原因：
- 驗證碼手動過碼失敗
- 網路延遲
- 帳號被臨時限制

### 大頭貼圖片始終找不到
排查：
1. 開啟 DevTools → Application → 檢查 localStorage
2. 確認已成功登入（頁面應進入首頁）
3. 驗證 DOM 定位是否有效

---

## 🔗 相關資源

- [Playwright 官方文件](https://playwright.dev/python/)
- [Pytest 文件](https://docs.pytest.org/)
- [GeeTest 驗證碼](https://www.geetest.com/)

---

## 👤 作者

Benedict Lin（林可晏）  
SWAG QA 工程師面試作業 - 第二題加分項