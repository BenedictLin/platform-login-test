import os
import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, expect

load_dotenv()

BASE_URL = "https://swag.live/?lang=zh-TW"
LOGIN_API = "https://api.swag.live/login/password?login_only=1"

class SwagLoginPage:
    """Page Object Model: 封裝 SWAG 登入頁面的核心操作元件"""
    def __init__(self, page):
        self.page = page
        self.login_entry_btn = page.locator("[class*='HeaderActionsWrapper'] button[data-element_id='button-login']")
        self.login_others_btn = page.locator('button[data-element_id="button-login-others"]').filter(has_text="帳號密碼登入")
        self.username_input = page.locator("#username-form")
        self.password_input = page.locator("#password-form")
        self.submit_btn = page.locator('button[type="submit"][data-element_id="button-login"]').filter(has_text="登入")
        self.success_avatar = page.locator("[class*='DesktopOnlySection'] button[data-element_id='tab-button-hamburger'] img[data-key='target']")
        self.error_message = page.locator("text=/.*(密碼|帳號).*錯誤.*/").first

    def navigate(self):
        self.page.goto(BASE_URL)
        self.page.wait_for_load_state("networkidle")

    def execute_login_flow(self, username, password):
        self.login_entry_btn.wait_for(state="visible", timeout=10000)
        self.login_entry_btn.click()
        self.login_others_btn.wait_for(state="visible", timeout=10000)
        self.login_others_btn.click()
        self.username_input.wait_for(state="visible", timeout=5000)
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.submit_btn.click()


def test_login_success_api():
    """
    【API 驗證】直接驗證登入 API 返回 token
    """
    username = os.getenv("SWAG_USERNAME")
    password = os.getenv("SWAG_PASSWORD")
    
    response = requests.post(
        LOGIN_API,
        json={"username": username, "password": password},
        headers={"Content-Type": "application/json"}
    )
    
    assert response.status_code == 200, f"API 返回 {response.status_code}，預期 200"
    data = response.json()
    assert "refresh_token" in data, "Response 無 refresh_token"
    
    print("PASS - API login successful")


def test_login_success_ui():
    """
    【混合式驗證】UI 自動化填寫 + 人工過驗證碼 + UI 斷言
    需要在 45 秒內手動完成 GeeTest 驗證碼
    """
    username = os.getenv("SWAG_USERNAME")
    password = os.getenv("SWAG_PASSWORD")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
        )
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")
        page = context.new_page()
        
        login_page = SwagLoginPage(page)
        login_page.navigate()
        login_page.execute_login_flow(username, password)
        
        print("\n[INFO] 驗證碼已觸發。請在 45 秒內『手動完成滑塊拼圖』...")
        
        try:
            login_page.success_avatar.wait_for(state="visible", timeout=45000)
            expect(login_page.success_avatar).to_be_visible()
            print("PASS - UI login successful (avatar appeared)")
            page.wait_for_timeout(2000)
        except Exception as e:
            print("FAIL - 驗證超時或未完成")
            raise e
        finally:
            browser.close()


def test_login_fail_api():
    """
    【API 驗證】輸入錯誤密碼，驗證 API 返回失敗
    """
    username = os.getenv("SWAG_USERNAME")
    wrong_password = "IncorrectPassword123"
    
    response = requests.post(
        LOGIN_API,
        json={"username": username, "password": wrong_password},
        headers={"Content-Type": "application/json"}
    )
    
    assert response.status_code != 200, f"預期失敗，但 API 返回 {response.status_code}"
    print("PASS - API correctly rejected wrong password")


def test_login_fail_ui():
    """
    【混合式驗證】錯誤密碼 + 人工過驗證碼 + 驗證錯誤訊息
    """
    username = os.getenv("SWAG_USERNAME")
    wrong_password = "IncorrectPassword123"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
        )
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")
        page = context.new_page()
        
        login_page = SwagLoginPage(page)
        login_page.navigate()
        login_page.execute_login_flow(username, wrong_password)
        
        print("\n[INFO] 驗證碼已觸發。請在 45 秒內『手動完成滑塊拼圖』...")
        
        try:
            login_page.error_message.wait_for(state="visible", timeout=45000)
            expect(login_page.error_message).to_be_visible()
            print("PASS - UI correctly showed error message")
            page.wait_for_timeout(2000)
        except Exception as e:
            print("FAIL - 未能偵測到錯誤訊息")
            raise e
        finally:
            browser.close()