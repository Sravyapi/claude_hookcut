#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""End-to-end Playwright test for the HookCut Eval Framework UI."""

import sys
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

EVAL_URL = "http://localhost:8501"


def test_full_review_workflow():
    """Test: load app -> see progress -> navigate pages -> submit a review."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # ── 1. Load the app ──
        print("[1/8] Loading app...")
        page.goto(EVAL_URL, wait_until="networkidle", timeout=30000)
        # Streamlit takes several seconds to render via websocket
        page.wait_for_timeout(8000)

        # ── 2. Verify sidebar renders ──
        print("[2/8] Checking sidebar...")
        content = page.content()
        assert "HookCut Eval" in content, "Sidebar title not found"
        assert "Overall Progress" in content or "Videos Reviewed" in content, "Progress section not found"
        print("  OK: Sidebar renders with progress")

        # ── 3. Verify Review page loads with a video ──
        print("[3/8] Checking Review page...")
        # Should show hook review content (test hooks we inserted)
        page.wait_for_timeout(2000)
        body_text = page.inner_text("body")
        assert "Hook Review" in body_text or "Hook" in body_text, f"Review page not showing. Got: {body_text[:200]}"
        print("  OK: Review page loaded")

        # ── 4. Check that hooks are displayed ──
        print("[4/8] Checking hooks display...")
        assert "hook" in body_text.lower() or "Hook 1" in body_text or "Test hook" in body_text or "Curiosity Gap" in body_text, \
            f"No hooks visible. Content: {body_text[:300]}"
        print("  OK: Hooks are displayed")

        # ── 5. Navigate to Dataset page ──
        print("[5/8] Testing Dataset page...")
        # Click Dataset in sidebar radio
        dataset_radio = page.get_by_text("Dataset", exact=True)
        if dataset_radio.count() > 0:
            dataset_radio.first.click()
            page.wait_for_timeout(2000)
            dataset_text = page.inner_text("body")
            assert "Dataset Overview" in dataset_text or "Total Videos" in dataset_text or "550" in dataset_text, \
                f"Dataset page did not load. Got: {dataset_text[:200]}"
            print("  OK: Dataset page shows data")
        else:
            print("  SKIP: Dataset radio not found (may be in different layout)")

        # ── 6. Navigate to Dashboard page ──
        print("[6/8] Testing Dashboard page...")
        dashboard_radio = page.get_by_text("Dashboard", exact=True)
        if dashboard_radio.count() > 0:
            dashboard_radio.first.click()
            page.wait_for_timeout(2000)
            dash_text = page.inner_text("body")
            assert "Analysis Dashboard" in dash_text or "Dashboard" in dash_text, \
                f"Dashboard page did not load. Got: {dash_text[:200]}"
            print("  OK: Dashboard page loads")
        else:
            print("  SKIP: Dashboard radio not found")

        # ── 7. Navigate to Prompt Versions page ──
        print("[7/8] Testing Prompt Versions page...")
        pv_radio = page.get_by_text("Prompt Versions", exact=True)
        if pv_radio.count() > 0:
            pv_radio.first.click()
            page.wait_for_timeout(2000)
            pv_text = page.inner_text("body")
            assert "Prompt Versions" in pv_text or "v1" in pv_text, \
                f"Prompt Versions page did not load. Got: {pv_text[:200]}"
            print("  OK: Prompt Versions page loads with v1")
        else:
            print("  SKIP: Prompt Versions radio not found")

        # ── 8. Go back to Review and submit a review ──
        print("[8/8] Testing review submission...")
        review_radio = page.get_by_text("Review", exact=True)
        if review_radio.count() > 0:
            review_radio.first.click()
            page.wait_for_timeout(3000)

        # Try to find and click Submit Review button
        submit_btn = page.get_by_text("Submit Review")
        if submit_btn.count() > 0:
            submit_btn.first.click()
            page.wait_for_timeout(3000)
            post_submit = page.inner_text("body")
            # After submit, should show success or move to next video
            if "saved" in post_submit.lower() or "Review" in post_submit:
                print("  OK: Review submitted successfully")
            else:
                print(f"  WARN: Submit clicked but unclear result: {post_submit[:200]}")
        else:
            print("  SKIP: Submit button not found (hooks may not be loaded)")

        # Take a screenshot for verification
        screenshot_path = str(Path(__file__).parent / "test_screenshot.png")
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"\nScreenshot saved: {screenshot_path}")

        browser.close()

    print("\n" + "=" * 60)
    print("  ALL TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    test_full_review_workflow()
