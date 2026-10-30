import sys
import time
from playwright.sync_api import sync_playwright

def run_smoke_test():
    print("=== SMOKE TEST: Launching System Chrome (/usr/bin/google-chrome) ===")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path='/usr/bin/google-chrome',
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
        )
        context = browser.new_context()
        page = context.new_page()

        print("Navigating to http://localhost:8069...")
        response = page.goto("http://localhost:8069", wait_until="networkidle")
        
        url = page.url
        title = page.title()
        status = response.status if response else None
        
        print(f"Final Page URL: {url}")
        print(f"Page Title: {title}")
        print(f"HTTP Status: {status}")

        content = page.content()
        is_odoo_visible = "odoo" in content.lower() or "Odoo" in title
        is_login_page_visible = "login" in content.lower() or "password" in content.lower() or page.locator("input[name='login']").count() > 0

        print(f"Odoo Visible: {is_odoo_visible}")
        print(f"Login Page Accessible: {is_login_page_visible}")

        browser.close()

        if is_odoo_visible and is_login_page_visible:
            print("BROWSER SMOKE TEST: PASS")
            return True
        else:
            print("BROWSER SMOKE TEST: FAIL")
            return False

if __name__ == "__main__":
    success = run_smoke_test()
    sys.exit(0 if success else 1)
