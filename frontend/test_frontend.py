from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.on("console", lambda msg: print(f"Browser console: {msg.type}: {msg.text}"))
        page.on("pageerror", lambda err: print(f"Browser error: {err}"))
        
        print("Navigating to predictions page...")
        page.goto("http://localhost:5174/ml-predictions", timeout=60000)
        
        print("Waiting for 'Edit in IDE' button...")
        try:
            page.wait_for_selector("text='Edit in IDE'", timeout=5000)
            print("Clicking 'Edit in IDE'...")
            page.click("text='Edit in IDE'")
            page.wait_for_timeout(2000)
            print("Done clicking.")
        except Exception as e:
            print(f"Could not click Edit in IDE: {e}")
            
        browser.close()

if __name__ == "__main__":
    run()
