import os
import sys
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, expect

load_dotenv()

BASE_URL = "https://swag.live/?lang=zh-TW"

class SwagLoginPage:
    """Page Object Model: 封裝 SWAG 登入頁面的核心操作元件與防禦性定位"""
    def __init__(self, page):
        self.page = page
        
        # 1. 入口按鈕：鎖定限制牆頂部區塊，防止與背景主要導覽列元件產生 Strict Mode 衝突
        self.login_entry_btn = page.locator("[class*='HeaderActionsWrapper'] button[data-element_id='button-login']")
        
        # 2. 切換帳密按鈕：鎖定具有「帳號密碼登入」文字的特定按鈕
        self.login_others_btn = page.locator('button[data-element_id="button-login-others"]').filter(has_text="帳號密碼登入")
        
        # 3. 帳密表單欄位
        self.username_input = page.locator("#username-form")
        self.password_input = page.locator("#password-form")
        
        # 4. 表單提交按鈕：指定 type="submit" 且過濾文字「登入」
        self.submit_btn = page.locator('button[type="submit"][data-element_id="button-login"]').filter(has_text="登入")
        
        # 5. 正向測試斷言目標：鎖定桌面版導覽列內的漢堡按鈕與大頭貼圖片 (data-key="target")
        # 完美規避內頁加載延遲與多重響應式元件衝突
        self.success_avatar = page.locator("[class*='DesktopOnlySection'] button[data-element_id='tab-button-hamburger'] img[data-key='target']")
        
        # 6. 反向測試斷言目標：利用正則表達式模糊匹配文字，並加上 .first
        # 完美防止表單紅字與下方彈窗（Toast）同時出現時引發的嚴格模式衝突
        self.error_message = page.locator("text=/.*(密碼|帳號).*錯誤.*/").first

    def navigate(self):
        self.page.goto(BASE_URL)
        self.page.wait_for_load_state("networkidle")

    def execute_login_flow(self, username, password):
        # 點擊進站限制牆頂部的登入入口
        self.login_entry_btn.wait_for(state="visible", timeout=20000)
        self.login_entry_btn.click()
        
        # 選擇帳號密碼登入
        self.login_others_btn.wait_for(state="visible", timeout=20000)
        self.login_others_btn.click()
        
        # 填寫帳密表單並送出
        self.username_input.wait_for(state="visible", timeout=5000)
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.submit_btn.click()


def test_login_success():
    """
    【加分題 - 正向測試】完整 UI 自動化表單互動 + 智能等待手動輔助過碼
    """
    username = os.getenv("SWAG_USERNAME")
    password = os.getenv("SWAG_PASSWORD")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36")
        
        # 移除 WebDriver 自動化特徵，對抗基礎反爬蟲偵測
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")
        page = context.new_page()
        
        login_page = SwagLoginPage(page)
        login_page.navigate()
        login_page.execute_login_flow(username, password)
        
        # 嘗試驗證 GeeTest 驗證碼是否出現（失敗不中斷）
        try:
            page.locator("div.geetest_box").first.wait_for(state="visible", timeout=20000)
            print("✓ GeeTest 驗證碼已確認出現")
        except:
            print("⚠ 驗證碼檢查超時，繼續等待登入結果...")
        
        # 強制顯示提示訊息
        print("\n" + "="*70)
        print("【請注意】GeeTest 驗證碼已出現在瀏覽器中")
        print("請在瀏覽器中『手動完成滑塊拼圖驗證』")
        print("測試有 45 秒等待時間，請在此期間完成驗證")
        print("="*70 + "\n")
        sys.stdout.flush()
        
        try:
            # 智能監聽策略：避免 sleep 硬等，動態監聽大頭貼元件現形
            login_page.success_avatar.wait_for(state="visible", timeout=45000)
            expect(login_page.success_avatar).to_be_visible()
            print("PASS - Login successful")
            print(f"  判斷根據：大頭貼圖片出現")
            print(f"  選擇器：[class*='DesktopOnlySection'] button[data-element_id='tab-button-hamburger'] img[data-key='target']")
            
            # 演示定格：留給錄影或評審視覺確認的時間
            page.wait_for_timeout(4000)
        except Exception as e:
            print("FAIL - Login failed (驗證超時或未完成)")
            raise e
        finally:
            browser.close()


def test_login_fail():
    """
    【加分題 - 反向測試】填入錯誤密碼，手動過碼後，驗證前端雙重錯誤提示（表單紅字/下方彈窗）
    """
    username = os.getenv("SWAG_USERNAME")
    wrong_password = "IncorrectPassword123"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36")
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")
        page = context.new_page()
        
        login_page = SwagLoginPage(page)
        login_page.navigate()
        login_page.execute_login_flow(username, wrong_password)
        
        # 嘗試驗證 GeeTest 驗證碼是否出現（失敗不中斷）
        try:
            page.locator("div.geetest_box").first.wait_for(state="visible", timeout=20000)
            print("✓ GeeTest 驗證碼已確認出現")
        except:
            print("⚠ 驗證碼檢查超時，繼續等待登入結果...")
        
        # 強制顯示提示訊息
        print("\n" + "="*70)
        print("【請注意】GeeTest 驗證碼已出現在瀏覽器中")
        print("請在瀏覽器中『手動完成滑塊拼圖驗證』")
        print("測試有 45 秒等待時間，請在此期間完成驗證")
        print("="*70 + "\n")
        sys.stdout.flush()
        
        try:
            # 智能監聽策略：手動過完驗證後，等待前端非同步渲染錯誤訊息
            login_page.error_message.wait_for(state="visible", timeout=45000)
            expect(login_page.error_message).to_be_visible()
            print("PASS - Login correctly failed and UI error message verified")
            print(f"  判斷根據：錯誤訊息出現")
            print(f"  選擇器：text=/.*(密碼|帳號).*錯誤.*/")
            
            # 演示定格：留給錄影或評審視覺確認的時間
            page.wait_for_timeout(4000)
        except Exception as e:
            print("FAIL - 反向測試未在規定時間內偵測到 UI 錯誤提示")
            raise e
        finally:
            browser.close()