"""
CredStrike - Multi-Threaded Authentication Brute-Forcer
Synthetic Password Auditing Lab

Phase 2 (Member 2): Authentication Testing Module

Features:
- SSH credential testing (paramiko)
- FTP credential testing (ftplib)
- HTTP login-form credential testing (requests)
- Thread-pool based concurrent testing
- SafetyHook extension point for Phase 3 (rate limiting / lockout protection)

Only test systems and accounts you are explicitly authorized to test.
Use synthetic/lab targets. This module performs no safety throttling of
its own beyond a flat per-attempt delay - real lockout protection is
Phase 3's responsibility (CredSafety), which can be plugged in via
SafetyHook without modifying this file.
"""

from dataclasses import dataclass, field
from pathlib import Path
from queue import Queue
from threading import Thread, Lock, Event
from time import sleep, time
import ftplib
import socket

import requests

try:
    import paramiko
except ImportError:
    paramiko = None


@dataclass
class AttackConfig:
    service: str            # "ssh" | "ftp" | "http"
    target: str
    port: int
    usernames: list
    wordlist_path: str
    threads: int = 4
    delay: float = 0.0
    timeout: float = 5.0

    # HTTP login-form specific
    http_url: str = ""
    http_user_field: str = "username"
    http_pass_field: str = "password"
    http_fail_text: str = "invalid"


class SafetyHook:
    """
    Default no-op hook. Phase 3 (CredSafety) can supply its own instance
    with real lockout-threshold / backoff logic without BruteForcer
    needing to know about it.
    """

    def before_attempt(self):
        pass

    def after_attempt(self, success):
        pass

    def should_stop(self):
        return False


class BruteForcer:

    def __init__(self, config, safety=None):

        self.config = config
        self.safety = safety or SafetyHook()

        self.found = []
        self.attempts = 0

        self.lock = Lock()
        self.stop_event = Event()

    def _count_attempt(self):

        with self.lock:
            self.attempts += 1

    def _record_success(self, username, password):

        with self.lock:
            self.found.append((username, password))

        print(f"[+] VALID CREDENTIALS FOUND -> {username}:{password}")

    def test_ssh(self, username, password):

        if paramiko is None:
            raise RuntimeError(
                "paramiko is not installed. Run: pip install paramiko"
            )

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            client.connect(
                self.config.target,
                port=self.config.port,
                username=username,
                password=password,
                timeout=self.config.timeout,
                banner_timeout=self.config.timeout,
                auth_timeout=self.config.timeout,
                look_for_keys=False,
                allow_agent=False,
            )
            return True

        except paramiko.AuthenticationException:
            return False

        except (socket.timeout, socket.error, paramiko.SSHException) as error:
            print(f"[-] Connection issue for {username}: {error}")
            return False

        finally:
            client.close()

    def test_ftp(self, username, password):

        ftp = ftplib.FTP(timeout=self.config.timeout)

        try:
            ftp.connect(self.config.target, self.config.port)
            ftp.login(username, password)
            return True

        except ftplib.error_perm:
            return False

        except (socket.timeout, socket.error, OSError) as error:
            print(f"[-] Connection issue for {username}: {error}")
            return False

        finally:
            try:
                ftp.quit()
            except Exception:
                ftp.close()

    def test_http(self, username, password):

        payload = {
            self.config.http_user_field: username,
            self.config.http_pass_field: password,
        }

        try:
            response = requests.post(
                self.config.http_url,
                data=payload,
                timeout=self.config.timeout,
                allow_redirects=True,
            )

            return self.config.http_fail_text.lower() not in response.text.lower()

        except requests.RequestException as error:
            print(f"[-] Connection issue for {username}: {error}")
            return False

    def attempt(self, username, password):

        if self.stop_event.is_set() or self.safety.should_stop():
            self.stop_event.set()
            return

        self.safety.before_attempt()

        service = self.config.service

        if service == "ssh":
            success = self.test_ssh(username, password)
        elif service == "ftp":
            success = self.test_ftp(username, password)
        elif service == "http":
            success = self.test_http(username, password)
        else:
            raise ValueError(f"Unsupported service: {service}")

        self._count_attempt()
        self.safety.after_attempt(success)

        if success:
            self._record_success(username, password)

        if self.config.delay:
            sleep(self.config.delay)

    def _worker(self, job_queue):

        while not self.stop_event.is_set():

            try:
                username, password = job_queue.get_nowait()
            except Exception:
                return

            try:
                self.attempt(username, password)
            finally:
                job_queue.task_done()

    def load_passwords(self):

        wordlist = Path(self.config.wordlist_path)

        if not wordlist.exists():
            raise FileNotFoundError(f"Wordlist not found: {wordlist}")

        return [
            line.strip()
            for line in wordlist.read_text(encoding="utf-8", errors="ignore").splitlines()
            if line.strip()
        ]

    def run(self):

        passwords = self.load_passwords()

        job_queue = Queue()

        for username in self.config.usernames:
            for password in passwords:
                job_queue.put((username, password))

        total_jobs = job_queue.qsize()

        print(f"\n[*] Target: {self.config.target}:{self.config.port} ({self.config.service})")
        print(f"[*] Loaded {len(passwords)} password(s) for {len(self.config.usernames)} username(s)")
        print(f"[*] Total attempts queued: {total_jobs}")
        print(f"[*] Launching {self.config.threads} worker thread(s)...\n")

        start_time = time()

        workers = [
            Thread(target=self._worker, args=(job_queue,), daemon=True)
            for _ in range(self.config.threads)
        ]

        for worker in workers:
            worker.start()

        job_queue.join()

        for worker in workers:
            worker.join(timeout=1)

        elapsed = time() - start_time

        print("\n" + "=" * 45)
        print("           AUDIT SUMMARY")
        print("=" * 45)
        print(f"{'Attempts made':20}: {self.attempts}")
        print(f"{'Valid pairs found':20}: {len(self.found)}")
        print(f"{'Elapsed time':20}: {elapsed:.2f}s")
        print("=" * 45)

        return self.found


def get_positive_integer(message, default=None):

    while True:

        raw = input(message).strip()

        if not raw and default is not None:
            return default

        try:
            value = int(raw)
            if value > 0:
                return value
            print("[-] Enter a number greater than zero.")

        except ValueError:
            print("[-] Invalid input. Please enter an integer.")


def get_service_choice():

    print("\n[1] SSH")
    print("[2] FTP")
    print("[3] HTTP login form")

    mapping = {"1": "ssh", "2": "ftp", "3": "http"}

    while True:
        choice = input("[?] Select target service: ").strip()
        if choice in mapping:
            return mapping[choice]
        print("[-] Invalid choice.")


def get_usernames():

    raw = input(
        "[?] Username(s), comma-separated (or path to a username file): "
    ).strip()

    path = Path(raw)

    if path.exists():
        return [
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    return [username.strip() for username in raw.split(",") if username.strip()]


def main():

    print("\n" + "=" * 45)
    print("     CREDSTRIKE AUTHENTICATION AUDIT")
    print("=" * 45)
    print("\nOnly use this against systems you are explicitly")
    print("authorized to test (lab / synthetic targets).\n")

    service = get_service_choice()

    target = input("[?] Target host/IP: ").strip()

    default_ports = {"ssh": 22, "ftp": 21, "http": 80}
    port = get_positive_integer(
        f"[?] Port (default {default_ports[service]}): ",
        default=default_ports[service],
    )

    usernames = get_usernames()

    wordlist_path = input("[?] Path to wordlist (.txt): ").strip()

    threads = get_positive_integer("[?] Number of threads (default 4): ", default=4)
    delay = input("[?] Delay between attempts in seconds (default 0): ").strip()
    delay = float(delay) if delay else 0.0

    config_kwargs = dict(
        service=service,
        target=target,
        port=port,
        usernames=usernames,
        wordlist_path=wordlist_path,
        threads=threads,
        delay=delay,
    )

    if service == "http":
        config_kwargs["http_url"] = input("[?] Login form URL: ").strip()
        config_kwargs["http_user_field"] = input(
            "[?] Username field name (default 'username'): "
        ).strip() or "username"
        config_kwargs["http_pass_field"] = input(
            "[?] Password field name (default 'password'): "
        ).strip() or "password"
        config_kwargs["http_fail_text"] = input(
            "[?] Text present only on failed login (default 'invalid'): "
        ).strip() or "invalid"

    config = AttackConfig(**config_kwargs)

    forcer = BruteForcer(config)
    forcer.run()

    print("\n[+] CredAttack finished.")


if __name__ == "__main__":
    main()
