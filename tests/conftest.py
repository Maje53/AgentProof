"""Cross-platform test setup for the GenLayer direct runner.

genlayer-test 0.30.0rc2 unlinks its stdin backing file immediately. POSIX allows
that while the duplicated descriptor is open; Windows does not. This shim keeps
the temporary path until pytest exits, without changing contract behavior.
"""

from __future__ import annotations

import os
import tempfile


_DEFERRED_STDIN_FILES: list[str] = []


if os.name == "nt":
    from gltest.direct import loader

    def _inject_message_to_fd0_windows(vm):
        try:
            calldata = loader.import_calldata()
            address_type = loader.import_address()
        except ImportError:
            return

        sender = vm.sender
        if isinstance(sender, bytes):
            sender = address_type(sender)

        contract_address = vm._contract_address
        if isinstance(contract_address, bytes):
            contract_address = address_type(contract_address)

        origin = vm.origin
        if isinstance(origin, bytes):
            origin = address_type(origin)

        encoded = calldata.encode(
            {
                "contract_address": contract_address,
                "sender_address": sender,
                "origin_address": origin,
                "stack": [],
                "value": vm._value,
                "datetime": vm._datetime,
                "is_init": False,
                "chain_id": vm._chain_id,
                "entry_kind": 0,
                "entry_data": b"",
                "entry_stage_data": None,
            }
        )

        fd, path = tempfile.mkstemp(prefix="agentproof-gltest-")
        try:
            os.write(fd, encoded)
            os.lseek(fd, 0, os.SEEK_SET)
            vm._original_stdin_fd = os.dup(0)
            os.dup2(fd, 0)
            _DEFERRED_STDIN_FILES.append(path)
        finally:
            os.close(fd)

    loader._inject_message_to_fd0 = _inject_message_to_fd0_windows


def pytest_sessionfinish(session, exitstatus):
    del session, exitstatus
    for path in _DEFERRED_STDIN_FILES:
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass
