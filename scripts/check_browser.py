#!/usr/bin/env python3
"""Smoke-check a served site using an installed Playwright Firefox browser.

Usage: python3 scripts/check_browser.py http://localhost:1313
"""

import re
import sys

from playwright.sync_api import sync_playwright, expect


def main():
    """Exercise data loading, setting selection, symbols, and URL state."""
    base = sys.argv[1].rstrip('/')
    errors = []
    with sync_playwright() as playwright:
        browser = playwright.firefox.launch(headless=True, firefox_user_prefs={"dom.events.testing.asyncClipboard": True})
        page = browser.new_page(viewport={'width': 1440, 'height': 1000})
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(base + '/')
        expect(page.locator('tr.sg-row')).to_have_count(230)
        expect(page.locator('#table-body [data-symbol-ascii], #table-body .symbol-copy')).to_have_count(0)
        page.locator('#settings-toggle-index').click()
        expect(page.locator('tr.sg-row')).to_have_count(527)
        page.locator('#search-input').fill('68:1ba-c')
        expect(page.locator('tr.sg-row')).to_have_count(1)
        page.locator('tr.sg-row').click()
        hall_select = page.locator('select[aria-label="Select Hall symbol"]')
        expect(hall_select.locator('option')).to_have_count(527)
        assert hall_select.evaluate('(s) => s.dataset.selected === s.selectedOptions[0].dataset.matchValue')
        # Both equivalent #68 n:c codes must remain selectable.
        expect(page.locator('select[data-secondary-select] option')).to_have_count(530)

        symbol = page.locator('.metric[data-symbol-ascii]:not([data-symbol-aliases])').first
        line = symbol.locator('.symbol-ascii')
        page.mouse.move(0, 0)
        expect(line).to_have_css('opacity', '0')
        expect(line).to_have_css('font-size', '10px')
        symbol.hover()
        expect(line).to_have_css('opacity', '1')
        ascii_text = symbol.get_attribute('data-symbol-ascii')
        expect(line.locator('code')).to_have_text(ascii_text)
        original_url = page.url
        line.locator('button').click()
        expect(line.locator('[role="status"]')).to_have_text('Copied')
        assert page.evaluate('navigator.clipboard.readText()') == ascii_text
        assert page.url == original_url, 'Copying must not navigate away from the details'
        # Users can select the literal ASCII text without activating navigation.
        line.locator('code').evaluate("""node => {
            const range = document.createRange(); range.selectNodeContents(node);
            getSelection().removeAllRanges(); getSelection().addRange(range);
        }""")
        line.locator('code').click()
        assert page.url == original_url
        page.evaluate('getSelection().removeAllRanges()')
        page.mouse.move(0, 0)
        line.locator('button').focus()
        expect(line).to_have_css('opacity', '1')
        # A rejected clipboard write leaves a selectable fallback, not a success message.
        page.evaluate("""() => {
            window.originalWriteText = navigator.clipboard.writeText;
            navigator.clipboard.writeText = () => Promise.reject(new Error('Denied'));
        }""")
        line.locator('button').click()
        expect(line.locator('[role="status"]')).to_have_text('Select and copy manually')
        assert page.evaluate('getSelection().toString()') == ascii_text
        page.evaluate("""() => {
            navigator.clipboard.writeText = window.originalWriteText;
            getSelection().removeAllRanges();
        }""")

        page.goto(base + '/nc/146:R/?theme=light&symops=closed#wyckoff-positions')
        expect(hall_select).to_have_value(re.compile(r'/hall/p_3\*/\?settings=all'))
        expect(page.locator('html')).to_have_attribute('data-theme', 'light')
        expect(page.locator('[data-section-body="symops"]')).to_be_hidden()
        assert page.url.endswith('#wyckoff-positions')
        page.locator('[data-settings-toggle]').click()
        expect(page).to_have_url(re.compile(r'/hall/r_3/\?settings=ita'))
        expect(hall_select.locator('option')).to_have_count(230)
        assert hall_select.evaluate('(s) => s.dataset.selected === s.selectedOptions[0].dataset.matchValue')

        page.goto(base + '/hall/p_4w/?settings=ita')
        expect(hall_select.locator('option')).to_have_count(230)
        tabs = page.locator('[data-section-body="max_subgroups"] [data-mapping-tab]')
        expect(tabs.filter(has_text=re.compile(r'#78 \(3\)'))).to_have_count(1)
        target = tabs.filter(has_text=re.compile(r'#78 \(7\)'))
        expect(target).to_have_count(1)
        target.click()
        panel = page.locator('#' + target.get_attribute('data-target-id'))
        expect(panel).to_be_visible()
        expect(panel).to_contain_text('P=')
        page.locator('[data-settings-toggle]').click()
        expect(page.locator('[data-section-body="max_subgroups"] .mapping-tab-external-link').first).to_have_attribute('href', re.compile('settings=all'))
        page.locator('[data-section-toggle="symops"]').click()
        expect(page.locator('a.inline-detail-link')).to_have_attribute('href', re.compile('symops=closed'))

        # Multiline extended symbols must copy exactly, including spaces/newlines.
        page.goto(base + '/hall/c_-2y/?settings=all')
        extended = page.locator('.metric-tall-two-rows[data-symbol-ascii]')
        expect(extended.locator('.symbol-copy')).to_have_count(1)
        extended.hover()
        extended.locator('.symbol-copy').click()
        expect(extended.locator('[role="status"]')).to_have_text('Copied')
        assert page.evaluate('navigator.clipboard.readText()') == 'C 1 m 1\n  a'
        assert page.locator('[data-section-body="setting_transforms"] [data-symbol-ascii]').first.get_attribute('data-symbol-ascii')

        page.goto(base + '/pointgroup/')
        expect(page.locator('tr.sg-row')).to_have_count(32)
        expect(page.locator('#table-body [data-symbol-ascii], #table-body .symbol-copy')).to_have_count(0)
        page.locator('#search-input').fill('cubic')
        expect(page.locator('tr.sg-row')).to_have_count(5)
        page.goto(base + '/pointgroup/3/?theme=light')
        expect(page.locator('[data-section-body="char_real"] tbody tr')).to_have_count(2)
        complex_rows = page.locator('[data-section-body="char_complex"] tbody tr')
        expect(complex_rows).to_have_count(3)
        expect(complex_rows).to_contain_text(['A', 'E (E_a)', 'E (E_b)'])
        complex_rows.nth(1).locator('.symbol-copy').focus()
        complex_rows.nth(1).locator('.symbol-copy').press('Enter')
        expect(complex_rows.nth(1).locator('[role="status"]')).to_have_text('Copied')
        assert page.evaluate('navigator.clipboard.readText()') == 'E_a'
        expect(complex_rows.nth(1)).to_contain_text('sqrt(3)/2')
        page.locator('[data-section-toggle="char_real"]').click()
        expect(page.locator('.related-link').first).to_have_attribute('href', re.compile('char_real=closed'))
        page.set_viewport_size({'width': 390, 'height': 844})
        expect(page.locator('[data-section-body="char_complex"]')).to_be_visible()

        # Exercise the raw-dataset fallback as well as the lightweight indices.
        page.route('**/data/*_index.json.gz', lambda route: route.fulfill(status=404, body='Unavailable'))
        page.goto(base + '/?settings=all')
        expect(page.locator('tr.sg-row')).to_have_count(527, timeout=30000)
        expect(page.locator('#table-body [data-symbol-ascii], #table-body .symbol-copy')).to_have_count(0)
        page.locator('#search-input').fill('68:1ba-c')
        expect(page.locator('tr.sg-row')).to_have_count(1)
        page.goto(base + '/pointgroup/')
        expect(page.locator('tr.sg-row')).to_have_count(32, timeout=30000)
        assert not errors, errors
        browser.close()
    print('Firefox checks passed: indices, fallback loading, aliases, setting modes, subgroup tabs, character tables, ASCII clipboard copying/selection, themes, and section/query state.')


if __name__ == '__main__':
    main()
