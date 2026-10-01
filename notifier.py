import html as html_lib
import logging

import httpx

log = logging.getLogger(__name__)


class Notifier:
    def __init__(self, bot_token: str, chat_id: str = ""):
        self.bot_token = bot_token
        # optional fixed chat id; when empty, chats are discovered from /start messages
        self.chat_id = chat_id.strip()
        self._offset = None

    @property
    def enabled(self) -> bool:
        return bool(self.bot_token)

    def _api(self, method: str, **params):
        resp = httpx.post(
            f"https://api.telegram.org/bot{self.bot_token}/{method}",
            json=params,
            timeout=15,
        )
        data = resp.json()
        if not data.get("ok"):
            log.error("telegram %s failed: %s", method, data)
        return data

    def poll(self, db, companies_count: int) -> None:
        """Long-poll getUpdates and register new chats."""
        if not self.enabled:
            return
        params = {"timeout": 45, "allowed_updates": ["message"]}
        if self._offset is not None:
            params["offset"] = self._offset
        try:
            resp = httpx.get(
                f"https://api.telegram.org/bot{self.bot_token}/getUpdates",
                params=params,
                timeout=60,
            )
            data = resp.json()
        except httpx.HTTPError as e:
            log.error("telegram getUpdates failed: %s", e)
            return
        if not data.get("ok"):
            log.error("telegram getUpdates failed: %s", data)
            return
        for update in data.get("result", []):
            self._offset = update["update_id"] + 1
            message = update.get("message")
            if not message:
                continue
            chat = message.get("chat") or {}
            chat_id = chat.get("id")
            if chat_id is None:
                continue
            name = (
                chat.get("title")
                or chat.get("username")
                or f"{chat.get('first_name', '')} {chat.get('last_name', '')}".strip()
            )
            is_new = chat_id not in db.chat_ids()
            db.add_chat(chat_id, name)
            text = message.get("text") or ""
            if is_new:
                log.info("registered chat %s (%s)", chat_id, name)
            if text.strip() == "/start" or is_new:
                self._send_to(
                    chat_id,
                    f"roBOTa subscribed. Watching {companies_count} companies, "
                    "new offers will be sent here.",
                )

    def targets(self, db) -> list[int]:
        ids = list(db.chat_ids())
        if self.chat_id:
            try:
                ids.append(int(self.chat_id))
            except ValueError:
                ids.append(self.chat_id)
        return list(dict.fromkeys(ids))

    def send_job(self, job, db) -> bool:
        lines = [f"<b>{html_lib.escape(job.company)}</b>"]
        lines.append(html_lib.escape(job.title))
        if job.location:
            lines.append(html_lib.escape(job.location))
        if job.salary:
            lines.append(f"💰 {html_lib.escape(job.salary)}")
        lines.append(html_lib.escape(job.url))
        text = "\n".join(lines)
        if not self.enabled:
            print(f"[telegram disabled]\n{text}\n")
            return False
        targets = self.targets(db)
        if not targets:
            log.warning("no chats subscribed yet - message the bot /start")
            return False
        sent = False
        for chat_id in targets:
            if self._send_to(chat_id, text):
                sent = True
        return sent

    def _send_to(self, chat_id, text: str) -> bool:
        data = self._api(
            "sendMessage",
            chat_id=chat_id,
            text=text,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
        return bool(data.get("ok"))
