import socket
import threading

from chaoscomms.radio import HamlibRadio


def run_rigctld_stub(listener: socket.socket) -> threading.Thread:
    def serve() -> None:
        connection, _ = listener.accept()
        with connection:
            file = connection.makefile("rwb")
            while True:
                command = file.readline()
                if not command:
                    return
                if command == b"f\n":
                    file.write(b"14074000\nRPRT 0\n")
                elif command == b"m\n":
                    file.write(b"USB\n0\nRPRT 0\n")
                else:
                    file.write(b"RPRT -4\n")
                file.flush()

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    return thread


def test_hamlib_radio_reads_frequency_and_mode_without_write_commands() -> None:
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    run_rigctld_stub(listener)
    port = listener.getsockname()[1]

    status = HamlibRadio("ft891", "Yaesu FT-891", port=port).status()

    listener.close()
    assert status.connected is True
    assert status.frequency_hz == 14_074_000
    assert status.mode == "USB"
    assert status.ptt_enabled is False
    assert status.error is None


def test_hamlib_radio_reports_timeout_as_disconnected() -> None:
    status = HamlibRadio("ft2980r", "Yaesu FT-2980R", port=1).status()

    assert status.connected is False
    assert status.model == "Yaesu FT-2980R"
    assert status.ptt_enabled is False
    assert status.error
