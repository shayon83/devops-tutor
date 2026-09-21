import asyncio

from playwright.async_api import async_playwright


async def run_traffic_simulation(num_sessions: int = 3):
    print(f"🚀 Starting Playwright traffic simulation ({num_sessions} sessions)...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--use-fake-ui-for-media-stream",
                "--use-fake-device-for-media-stream",
                "--allow-file-access-from-files"
            ]
        )

        for i in range(1, num_sessions + 1):
            print(f"\n--- [SESSION {i}/{num_sessions}] STARTING ---")
            context = await browser.new_context(permissions=["microphone"])
            page = await context.new_page()

            errors = []
            def log_console(msg):
                interesting = msg.type in ("error", "warning") or "connected" in msg.text
                if interesting:
                    print(f"  [BROWSER LOG ({msg.type.upper()})] {msg.text}")

            page.on("console", log_console)
            page.on("pageerror", lambda err, sink=errors: sink.append(str(err)))

            await page.goto("http://localhost:3000")
            await page.wait_for_selector("text=Ready to Learn DevOps?")

            start_btn = page.locator("button:has-text('Start Voice Lesson')")
            await start_btn.click()

            # Wait for connection
            await page.wait_for_selector("text=Tutor Session Active", timeout=10000)
            print("  ✅ WebRTC voice session connected successfully!")

            # Simulate active voice conversation delay
            await asyncio.sleep(4)

            # Mute toggle test
            mute_btn = page.locator("button:has-text('Mute Mic')")
            if await mute_btn.is_visible():
                await mute_btn.click()
                print("  🎙️ Mute toggled successfully.")
                await asyncio.sleep(1)

            # End lesson
            end_btn = page.locator("button:has-text('End Lesson')")
            await end_btn.click()
            print("  ⏹️ Ended lesson.")

            # CSAT Feedback Modal
            await page.wait_for_selector("text=How was your tutoring session?", timeout=5000)
            submit_btn = page.locator("button:has-text('Submit Session Feedback')")
            await submit_btn.click()
            print("  ⭐ Submitted 5-star CSAT feedback.")

            if errors:
                print(f"  ❌ Errors captured in browser for session {i}: {errors}")
            else:
                print(f"  ✨ Session {i} completed with ZERO browser errors!")

            await context.close()
            await asyncio.sleep(1)

        await browser.close()
        print("\n🎉 Traffic simulation complete across all 3 sessions!")

if __name__ == "__main__":
    asyncio.run(run_traffic_simulation(3))
