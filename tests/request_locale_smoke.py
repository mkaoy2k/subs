"""Overlapping requests must keep the language stored on flask.g.

Run from the repo root, with the project virtualenv:

    .venv/bin/python tests/request_locale_smoke.py
"""

import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

_TMP = tempfile.mkdtemp(prefix="subs-locale-")
os.environ["DB_NAME"] = str(Path(_TMP) / "users.db")
os.environ["L10N"] = "繁中"
os.environ["FLASK_SECRET_KEY"] = "request-locale-smoke"
os.environ["LOGGING"] = "ERROR"
os.environ.pop("OPS_SVR_THREADS", None)

import db_utils  # noqa: E402

db_utils.init_db()

import ops_svr  # noqa: E402

EN_HEADER = "The Owon Kaos Journal"
ZH_HEADER = "渤海漚汪高氏族譜通訊期刊"
BASE = "https://localhost"


def _home(lang):
    client = ops_svr.app.test_client()
    with client.session_transaction() as sess:
        sess["current_lang"] = lang
    response = client.get("/", base_url=BASE)
    return response.status_code, response.get_data(as_text=True)


class RequestLocaleSmokeTest(unittest.TestCase):
    def test_request_language_is_not_a_module_global(self):
        for name in ("g_loc_key", "g_loc", "g_menu", "g_home", "g_faq", "g_about"):
            self.assertFalse(hasattr(ops_svr, name), name)
        self.assertEqual(ops_svr.g_default_loc_key, "繁中")

    def test_session_language_is_isolated_per_client(self):
        us_status, us_body = _home("US")
        zh_status, zh_body = _home("繁中")
        self.assertEqual(us_status, 200)
        self.assertIn(EN_HEADER, us_body)
        self.assertIn(">Home</a>", us_body)
        self.assertNotIn(ZH_HEADER, us_body)
        self.assertEqual(zh_status, 200)
        self.assertIn(ZH_HEADER, zh_body)
        self.assertIn(">主頁</a>", zh_body)
        self.assertNotIn(EN_HEADER, zh_body)

    def test_overlapping_requests_do_not_mix_languages(self):
        barrier = threading.Barrier(2)
        observed = {}
        errors = []
        lock = threading.Lock()
        original = ops_svr.app.view_functions["home"]

        def wrapped():
            try:
                before = (
                    ops_svr.g.loc_key,
                    ops_svr.g.loc["HOME_HTML_H1"],
                    ops_svr.g.menu[0][1],
                )
                barrier.wait(timeout=5)
                after = (
                    ops_svr.g.loc_key,
                    ops_svr.g.loc["HOME_HTML_H1"],
                    ops_svr.g.menu[0][1],
                )
                with lock:
                    observed[threading.get_ident()] = (before, after)
            except Exception as exc:
                errors.append(exc)
                try:
                    barrier.abort()
                except Exception:
                    pass
            return original()

        results = {}

        def hit(lang):
            try:
                results[lang] = _home(lang)
            except Exception as exc:
                errors.append(exc)

        ops_svr.app.view_functions["home"] = wrapped
        threads = [
            threading.Thread(target=hit, args=("US",)),
            threading.Thread(target=hit, args=("繁中",)),
        ]
        try:
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=10)
        finally:
            ops_svr.app.view_functions["home"] = original

        self.assertEqual(errors, [])
        self.assertFalse(any(thread.is_alive() for thread in threads))
        self.assertEqual(len(observed), 2)
        for before, after in observed.values():
            self.assertEqual(before, after)
        self.assertEqual({before[0] for before, _after in observed.values()}, {"US", "繁中"})

        us_status, us_body = results["US"]
        zh_status, zh_body = results["繁中"]
        self.assertEqual(us_status, 200)
        self.assertIn(EN_HEADER, us_body)
        self.assertIn(">Home</a>", us_body)
        self.assertNotIn(ZH_HEADER, us_body)
        self.assertEqual(zh_status, 200)
        self.assertIn(ZH_HEADER, zh_body)
        self.assertIn(">主頁</a>", zh_body)
        self.assertNotIn(EN_HEADER, zh_body)

    def test_catalog_refresh_does_not_rewrite_a_bound_request(self):
        with ops_svr.app.test_request_context("/"):
            ops_svr.session["current_lang"] = "US"
            ops_svr.before_request()
            header = ops_svr.g.loc["HOME_HTML_H1"]
            menu_label = ops_svr.g.menu[0][1]
            ops_svr.init_globals()
            self.assertEqual(header, EN_HEADER)
            self.assertEqual(menu_label, "Home")
            self.assertEqual(ops_svr.g.loc["HOME_HTML_H1"], header)
            self.assertEqual(ops_svr.g.menu[0][1], menu_label)

    def test_plain_http_keeps_the_language_cookie(self):
        client = ops_svr.app.test_client()
        switched = client.get(
            "/setL10N?lang=US&page=home",
            base_url="http://localhost",
            follow_redirects=False,
        )
        self.assertEqual(switched.status_code, 302)
        set_cookie = " ".join(switched.headers.getlist("Set-Cookie"))
        self.assertIn("current_lang=", set_cookie)
        self.assertNotIn("current_lang=US; Secure", set_cookie)
        # The session cookie stays Secure. The language cookie must not.
        self.assertIn("Secure", set_cookie)
        self.assertIn("current_lang=", set_cookie.split("Secure")[0])

        followed = client.get(
            "/setL10N?lang=US&page=home",
            base_url="http://localhost",
            follow_redirects=True,
        )
        self.assertIn(EN_HEADER, followed.get_data(as_text=True))
        again = client.get("/", base_url="http://localhost")
        body = again.get_data(as_text=True)
        self.assertEqual(again.status_code, 200)
        self.assertIn(EN_HEADER, body)
        self.assertIn(">Home</a>", body)
        self.assertNotIn(ZH_HEADER, body)

    def test_set_l10n_stores_language_on_the_session_only(self):
        client = ops_svr.app.test_client()
        with client.session_transaction() as sess:
            sess["current_lang"] = "繁中"
        response = client.get(
            "/setL10N?lang=US&page=home",
            base_url=BASE,
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn(EN_HEADER, body)
        self.assertNotIn(ZH_HEADER, body)
        with client.session_transaction() as sess:
            self.assertEqual(sess["current_lang"], "US")
        self.assertFalse(hasattr(ops_svr, "g_loc_key"))

    def test_thread_default_stays_one_and_can_be_raised(self):
        os.environ.pop("OPS_SVR_THREADS", None)
        _host, _port, threads = ops_svr.server_settings()
        self.assertEqual(threads, 1)
        os.environ["OPS_SVR_THREADS"] = "4"
        try:
            _host, _port, threads = ops_svr.server_settings()
            self.assertEqual(threads, 4)
        finally:
            os.environ.pop("OPS_SVR_THREADS", None)


if __name__ == "__main__":
    unittest.main()
