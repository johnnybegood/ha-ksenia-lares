"""Focused command-log regression check; no HA installation or panel required."""
import ast
import logging
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock


class CommandLoggingTests(unittest.IsolatedAsyncioTestCase):
    async def test_pin_stays_in_request_but_not_logs(self):
        source = Path(__file__).resolve().parents[1] / (
            "custom_components/ksenia_lares/base.py"
        )
        # Execute the real client class without importing HA or network dependencies.
        tree = ast.parse(source.read_text())
        client_class = next(
            node for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "LaresBase"
        )
        logger = logging.getLogger("test.ksenia_lares.commands")
        namespace = {"_LOGGER": logger}
        exec(compile(ast.Module(body=[client_class], type_ignores=[]), str(source), "exec"), namespace)
        client = namespace["LaresBase"].__new__(namespace["LaresBase"])
        pin = "739182"  # Synthetic test credential.
        cases = [
            ("activate_scenario", (2, pin), "setMacro", "&macroId=2"),
            ("bypass_zone", (0, pin, True), "setByPassZone", "&zoneId=1&zoneValue=1"),
            ("bypass_zone", (0, pin, False), "setByPassZone", "&zoneId=1&zoneValue=0"),
        ]
        for method, args, command, parameters in cases:
            for status in ("cmdSent", "cmdError"):
                with self.subTest(method=method, args=args, status=status):
                    response = Mock()
                    response.xpath.return_value = [SimpleNamespace(text=status)]
                    client.get = AsyncMock(return_value=response)
                    with self.assertLogs(logger, level="DEBUG") as captured:
                        result = await getattr(client, method)(*args)
                    self.assertEqual(result, status == "cmdSent")
                    client.get.assert_awaited_once_with(
                        f"cmd/cmdOk.xml?cmd={command}&pin={pin}"
                        f"&redirectPage=/xml/cmd/cmdError.xml{parameters}"
                    )
                    messages = "\n".join(captured.output)
                    self.assertIn(f"Sending command {command}", messages)
                    self.assertNotIn(pin, messages)
                    self.assertNotIn("pin=", messages)
                    self.assertNotIn("cmd/cmdOk.xml", messages)


if __name__ == "__main__":
    unittest.main()
