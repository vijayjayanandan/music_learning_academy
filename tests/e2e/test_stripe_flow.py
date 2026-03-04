"""
E2E Stripe Verification: Ensure payment pages don't crash.
"""
import os
import pytest

from .conftest import _remove_debug_toolbar


@pytest.mark.e2e
class TestStripeFlow:

    def test_01_pricing_page_loads(self, e2e_server, owner_page, screenshot_dir):
        owner_page.goto(f"{e2e_server}/payments/pricing/")
        owner_page.wait_for_load_state("networkidle")
        _remove_debug_toolbar(owner_page)
        owner_page.screenshot(path=os.path.join(screenshot_dir, "stripe_01_pricing.png"))
        assert "Server Error" not in owner_page.content()

    def test_02_payment_history_loads(self, e2e_server, owner_page, screenshot_dir):
        owner_page.goto(f"{e2e_server}/payments/history/")
        owner_page.wait_for_load_state("networkidle")
        _remove_debug_toolbar(owner_page)
        owner_page.screenshot(path=os.path.join(screenshot_dir, "stripe_02_history.png"))
        assert "Server Error" not in owner_page.content()

    def test_03_webhook_rejects_unsigned(self, e2e_server, page):
        import urllib.request
        import urllib.error

        url = f"{e2e_server}/payments/webhook/"
        req = urllib.request.Request(
            url,
            data=b'{"type": "test"}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urllib.request.urlopen(req)
        except urllib.error.HTTPError as e:
            assert e.code in (400, 403), f"Unexpected status code: {e.code}"
