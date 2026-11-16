"""Family-gated subscription.

Run from the repo root, with the project virtualenv:

    .venv/bin/python tests/family_subscribe_smoke.py

Membership is the user row's family_id. When no family id is configured,
any valid email can still start the old verification flow.
"""

import os
import re
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

_TMP = tempfile.mkdtemp(prefix="subs-family-")
os.environ["DB_NAME"] = str(Path(_TMP) / "users.db")
os.environ["L10N"] = "繁中"
os.environ["FLASK_SECRET_KEY"] = "family-subscribe-smoke"
os.environ["LOGGING"] = "ERROR"
os.environ.pop("FAMILY_ID", None)
os.environ.pop("DB_ADMIN", None)

import db_utils  # noqa: E402
import email_utils  # noqa: E402
import ops_svr  # noqa: E402

BASE = "https://localhost"
FAMILY = "fam-1"
NEXT_STEP = "Please check {email} for the next step."
NEXT_STEP_ZH = "請查看 {email} 以完成下一步。"
SEND_FAILED = "Failed to send email. Please try again later."
OPEN_CONFIRM = "Please check {email} to confirm subscription."


def _alerts(body):
    """Flash text shown on the page after a redirect."""
    found = re.findall(r'role="alert">\s*(.*?)\s*<button', body, flags=re.S)
    return [re.sub(r"\s+", " ", item).strip() for item in found]


def _insert_user(email, family_id, is_active=0, token=None, l10n="US"):
    with db_utils.get_db_connection() as conn:
        conn.execute(
            f"""
            INSERT INTO {db_utils.db_tables['user']}
                (email, is_active, l10n, token, family_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (email, is_active, l10n, token, family_id),
        )
        conn.commit()


def _user(email):
    return db_utils.get_subscriber(email)


class FamilySubscribeSmokeTest(unittest.TestCase):
    def setUp(self):
        self._csrf = ops_svr.app.config.get("WTF_CSRF_ENABLED", True)
        self._family_env = os.environ.get("FAMILY_ID")
        ops_svr.app.config["WTF_CSRF_ENABLED"] = False
        ops_svr.app.config["FAMILY_ID"] = None
        with db_utils.get_db_connection() as conn:
            conn.execute(f"DELETE FROM {db_utils.db_tables['user']}")
            conn.commit()

    def tearDown(self):
        ops_svr.app.config["FAMILY_ID"] = None
        ops_svr.app.config["WTF_CSRF_ENABLED"] = self._csrf
        if self._family_env is None:
            os.environ.pop("FAMILY_ID", None)
        else:
            os.environ["FAMILY_ID"] = self._family_env
        os.environ.pop("DB_ADMIN", None)

    def _post(self, email, action="subscribe", lang="US"):
        client = ops_svr.app.test_client()
        with client.session_transaction() as sess:
            sess["current_lang"] = lang
        return client.post(
            "/subscribe",
            data={"email": email, "action": action},
            base_url=BASE,
            follow_redirects=True,
        )

    def test_parser_accepts_family_id_and_still_defaults_open(self):
        parser = ops_svr.build_parser()
        specified = parser.parse_args(["--family_id", "kao", "--dev"])
        self.assertEqual(specified.family_id, "kao")
        self.assertTrue(specified.dev)
        omitted = parser.parse_args([])
        self.assertIsNone(omitted.family_id)
        self.assertFalse(omitted.dev)

    def test_configure_family_id_cli_overrides_env(self):
        os.environ["FAMILY_ID"] = "from-env"
        self.assertEqual(ops_svr.configure_family_id(None), "from-env")
        self.assertEqual(ops_svr.configure_family_id("  cli-id  "), "cli-id")
        self.assertEqual(ops_svr.app.config["FAMILY_ID"], "cli-id")
        self.assertEqual(ops_svr.configure_family_id("   "), "from-env")
        os.environ["FAMILY_ID"] = "   "
        self.assertIsNone(ops_svr.configure_family_id(None))
        self.assertIsNone(ops_svr.active_family_id())

    def test_legacy_user_table_gains_family_id(self):
        legacy_dir = tempfile.mkdtemp(prefix="subs-legacy-")
        legacy = str(Path(legacy_dir) / "legacy.db")
        conn = sqlite3.connect(legacy)
        conn.execute(
            """
            CREATE TABLE user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                is_active INTEGER DEFAULT 0
            )
            """
        )
        conn.execute("INSERT INTO user (email, is_active) VALUES ('old@example.com', 1)")
        conn.commit()
        conn.close()

        previous = db_utils.dbn
        db_utils.dbn = legacy
        try:
            db_utils.init_db()
            with db_utils.get_db_connection() as conn:
                columns = [row[1] for row in conn.execute("PRAGMA table_info(user)")]
                row = conn.execute(
                    "SELECT email, family_id FROM user WHERE email = 'old@example.com'"
                ).fetchone()
            self.assertIn("family_id", columns)
            self.assertEqual(row["email"], "old@example.com")
            self.assertIsNone(row["family_id"])
        finally:
            db_utils.dbn = previous

    def test_membership_is_family_id_on_the_user_row(self):
        _insert_user("member@example.com", " fam-1 ")
        _insert_user("other@example.com", "other-family")
        _insert_user("blank@example.com", None)
        _insert_user("numbered@example.com", 12)
        self.assertTrue(db_utils.is_family_member("member@example.com", "fam-1"))
        self.assertTrue(db_utils.is_family_member("member@example.com", " fam-1 "))
        self.assertFalse(db_utils.is_family_member("member@example.com", "Fam-1"))
        self.assertFalse(db_utils.is_family_member("other@example.com", "fam-1"))
        self.assertFalse(db_utils.is_family_member("blank@example.com", "fam-1"))
        self.assertFalse(db_utils.is_family_member("missing@example.com", "fam-1"))
        self.assertFalse(db_utils.is_family_member("member@example.com", None))
        self.assertFalse(db_utils.is_family_member("member@example.com", "  "))
        self.assertTrue(db_utils.is_family_member("numbered@example.com", "12"))
        self.assertFalse(db_utils.is_family_member("numbered@example.com", "012"))

        user = _user("blank@example.com")
        self.assertEqual(
            db_utils.update_user(user["id"], {"family_id": "fam-1"}),
            user["id"],
        )
        self.assertTrue(db_utils.is_family_member("blank@example.com", "fam-1"))

    def test_gated_member_and_non_member_see_the_same_page(self):
        ops_svr.app.config["FAMILY_ID"] = FAMILY
        os.environ["DB_ADMIN"] = "admin@example.com"
        _insert_user("member@example.com", FAMILY, token="keep-me")
        _insert_user("other@example.com", "other-family", is_active=1, token="leave-me")

        with patch.object(ops_svr.eu, "send_verification_email", return_value=True) as verify, \
             patch.object(ops_svr.eu, "send_membership_instruction_email", return_value=True) as instruction:
            member = self._post("member@example.com")
            other = self._post("other@example.com")
            stranger = self._post("stranger@example.com")

        self.assertEqual(member.status_code, 200)
        self.assertEqual(other.status_code, 200)
        self.assertEqual(stranger.status_code, 200)
        member_alerts = _alerts(member.get_data(as_text=True))
        other_alerts = _alerts(other.get_data(as_text=True))
        stranger_alerts = _alerts(stranger.get_data(as_text=True))
        self.assertEqual(member_alerts, [NEXT_STEP.format(email="member@example.com")])
        self.assertEqual(
            [item.replace("member@example.com", "ADDR") for item in member_alerts],
            [item.replace("other@example.com", "ADDR") for item in other_alerts],
        )
        self.assertEqual(
            [item.replace("other@example.com", "ADDR") for item in other_alerts],
            [item.replace("stranger@example.com", "ADDR") for item in stranger_alerts],
        )
        for alerts in (member_alerts, other_alerts, stranger_alerts):
            text = " ".join(alerts)
            self.assertNotIn("confirm subscription", text)
            self.assertNotIn("not registered", text)
            self.assertNotIn("尚未登記", text)
            self.assertNotIn("personal information", text)

        self.assertEqual(verify.call_count, 1)
        self.assertEqual(verify.call_args.args[1], "member@example.com")
        self.assertTrue(verify.call_args.kwargs["is_subscribe"])
        self.assertEqual(instruction.call_count, 2)
        instructed = {call.args[1] for call in instruction.call_args_list}
        self.assertEqual(instructed, {"other@example.com", "stranger@example.com"})
        for call in instruction.call_args_list:
            self.assertEqual(call.kwargs["admin_email"], "admin@example.com")

        member_row = _user("member@example.com")
        self.assertEqual(member_row["is_active"], db_utils.Subscriber_State["pending"])
        self.assertEqual(member_row["family_id"], FAMILY)
        self.assertNotEqual(member_row["token"], "keep-me")

        other_row = _user("other@example.com")
        self.assertEqual(other_row["is_active"], 1)
        self.assertEqual(other_row["token"], "leave-me")
        self.assertEqual(other_row["family_id"], "other-family")
        self.assertIsNone(_user("stranger@example.com"))

    def test_gated_failure_page_is_the_same_for_member_and_stranger(self):
        ops_svr.app.config["FAMILY_ID"] = FAMILY
        _insert_user("member@example.com", FAMILY)
        with patch.object(ops_svr.eu, "send_verification_email", return_value=False), \
             patch.object(ops_svr.eu, "send_membership_instruction_email", return_value=False):
            member = self._post("member@example.com")
            stranger = self._post("stranger@example.com")
        member_alerts = _alerts(member.get_data(as_text=True))
        stranger_alerts = _alerts(stranger.get_data(as_text=True))
        self.assertEqual(member_alerts, [SEND_FAILED])
        self.assertEqual(member_alerts, stranger_alerts)
        self.assertEqual(_user("member@example.com")["is_active"], 0)
        self.assertIsNone(_user("stranger@example.com"))

    def test_gated_page_follows_the_request_language(self):
        ops_svr.app.config["FAMILY_ID"] = FAMILY
        _insert_user("member@example.com", FAMILY)
        with patch.object(ops_svr.eu, "send_verification_email", return_value=True), \
             patch.object(ops_svr.eu, "send_membership_instruction_email", return_value=True):
            member = self._post("member@example.com", lang="繁中")
            stranger = self._post("stranger@example.com", lang="繁中")
        member_alerts = _alerts(member.get_data(as_text=True))
        stranger_alerts = _alerts(stranger.get_data(as_text=True))
        self.assertEqual(member_alerts, [NEXT_STEP_ZH.format(email="member@example.com")])
        self.assertEqual(
            [item.replace("member@example.com", "ADDR") for item in member_alerts],
            [item.replace("stranger@example.com", "ADDR") for item in stranger_alerts],
        )

    def test_open_gate_still_verifies_any_valid_email(self):
        self.assertIsNone(ops_svr.active_family_id())
        with patch.object(ops_svr.eu, "send_verification_email", return_value=True) as verify, \
             patch.object(ops_svr.eu, "send_membership_instruction_email", return_value=True) as instruction:
            response = self._post("new@example.com")
        self.assertEqual(response.status_code, 200)
        self.assertIn(OPEN_CONFIRM.format(email="new@example.com"), response.get_data(as_text=True))
        self.assertEqual(verify.call_count, 1)
        instruction.assert_not_called()
        created = _user("new@example.com")
        self.assertIsNotNone(created)
        self.assertEqual(created["is_active"], db_utils.Subscriber_State["pending"])
        self.assertIsNone(created["family_id"])

    def test_invalid_email_does_not_send_or_lookup_membership(self):
        ops_svr.app.config["FAMILY_ID"] = FAMILY
        with patch.object(ops_svr.eu, "send_verification_email") as verify, \
             patch.object(ops_svr.eu, "send_membership_instruction_email") as instruction, \
             patch.object(db_utils, "is_family_member") as membership:
            response = self._post("not-an-email")
        self.assertIn("not-an-email is not a valid email address", response.get_data(as_text=True))
        verify.assert_not_called()
        instruction.assert_not_called()
        membership.assert_not_called()

    def test_unsubscribe_does_not_require_membership(self):
        ops_svr.app.config["FAMILY_ID"] = FAMILY
        with patch.object(ops_svr.eu, "send_verification_email", return_value=True) as verify, \
             patch.object(ops_svr.eu, "send_membership_instruction_email") as instruction:
            response = self._post("stranger@example.com", action="unsubscribe")
        self.assertIn(
            "Please check stranger@example.com to confirm unsubscription.",
            response.get_data(as_text=True),
        )
        self.assertEqual(verify.call_count, 1)
        self.assertFalse(verify.call_args.kwargs["is_subscribe"])
        instruction.assert_not_called()
        self.assertIsNone(_user("stranger@example.com"))

    def test_instruction_email_is_bilingual(self):
        captured = {}

        def fake_send(mail, msg, max_retries=3):
            captured["subject"] = str(msg.subject)
            captured["html"] = msg.html
            captured["to"] = list(msg.recipients)
            return True

        with patch.object(email_utils, "_send_mail", fake_send):
            with ops_svr.app.app_context():
                sent = email_utils.send_membership_instruction_email(
                    ops_svr.g_fmail,
                    "person@example.com",
                    admin_email="admin@example.com",
                )
        self.assertTrue(sent)
        self.assertEqual(captured["to"], ["person@example.com"])
        self.assertIn("請先向家族管理員登記後再訂閱", captured["subject"])
        self.assertIn("Register with your family Admin before subscribing", captured["subject"])
        html = captured["html"]
        self.assertIn('lang="zh-Hant"', html)
        self.assertIn('lang="en"', html)
        self.assertIn("個人資料", html)
        self.assertIn("personal information", html)
        self.assertIn("person@example.com", html)
        self.assertIn("admin@example.com", html)
        self.assertIn("mailto:admin@example.com", html)

    def test_verify_activates_a_member_and_blocks_anyone_else(self):
        ops_svr.app.config["FAMILY_ID"] = FAMILY
        _insert_user("member@example.com", FAMILY, token="good-token")
        _insert_user("other@example.com", "other-family", token="other-token", is_active=-1)

        client = ops_svr.app.test_client()
        with client.session_transaction() as sess:
            sess["current_lang"] = "US"
        ok = client.get(
            "/verify-email",
            query_string={"email": "member@example.com", "token": "good-token", "action": "subscribe"},
            base_url=BASE,
            follow_redirects=True,
        )
        self.assertIn("successfully subscribed", ok.get_data(as_text=True))
        self.assertEqual(_user("member@example.com")["is_active"], db_utils.Subscriber_State["active"])

        blocked = client.get(
            "/verify-email",
            query_string={"email": "other@example.com", "token": "other-token", "action": "subscribe"},
            base_url=BASE,
            follow_redirects=True,
        )
        blocked_body = blocked.get_data(as_text=True)
        self.assertIn("could not be completed", blocked_body)
        self.assertNotIn("successfully subscribed", blocked_body)
        other = _user("other@example.com")
        self.assertEqual(other["is_active"], -1)
        self.assertEqual(other["token"], "other-token")

    def test_open_gate_verify_still_activates_without_a_family_id(self):
        _insert_user("legacy@example.com", None, token="legacy-token")
        client = ops_svr.app.test_client()
        response = client.get(
            "/verify-email",
            query_string={"email": "legacy@example.com", "token": "legacy-token", "action": "subscribe"},
            base_url=BASE,
            follow_redirects=True,
        )
        self.assertIn("successfully subscribed", response.get_data(as_text=True))
        self.assertEqual(
            _user("legacy@example.com")["is_active"],
            db_utils.Subscriber_State["active"],
        )


if __name__ == "__main__":
    unittest.main()
