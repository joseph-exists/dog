from __future__ import annotations

from pathlib import Path
import sys
import termios

import pytest


KENNEL_SRC = Path(__file__).resolve().parents[1] / "src"
if str(KENNEL_SRC) not in sys.path:
    sys.path.insert(0, str(KENNEL_SRC))

import server


def test_parse_terminal_control_message_accepts_resize_payload() -> None:
    control = server._parse_terminal_control_message(
        '{"type":"terminal_control","control":"resize","cols":132,"rows":43}'
    )

    assert control is not None
    assert control.control == "resize"
    assert control.cols == 132
    assert control.rows == 43


@pytest.mark.parametrize(
    "payload",
    [
        "ls -la\n",
        '{"hello":"world"}',
        '{"type":"terminal_control","control":"resize","cols":0,"rows":24}',
        '{"type":"terminal_control","control":"unknown"}',
    ],
)
def test_parse_terminal_control_message_rejects_non_control_input(payload: str) -> None:
    assert server._parse_terminal_control_message(payload) is None


def test_set_pty_winsize_uses_terminal_ioctl(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_ioctl(fd: int, op: int, data: bytes) -> None:
        captured["fd"] = fd
        captured["op"] = op
        captured["data"] = data

    monkeypatch.setattr(server.fcntl, "ioctl", fake_ioctl)

    server._set_pty_winsize(9, 120, 34)

    assert captured["fd"] == 9
    assert captured["op"] == termios.TIOCSWINSZ
    assert captured["data"] == server.struct.pack("HHHH", 34, 120, 0, 0)
