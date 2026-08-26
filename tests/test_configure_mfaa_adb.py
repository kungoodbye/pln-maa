import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.configure_mfaa_adb import configure_adb_screencap


class ConfigureMfaAdbTests(unittest.TestCase):
    @patch("tools.configure_mfaa_adb.is_mfaavalonia_running", return_value=False)
    def test_forces_encode_without_replacing_existing_instance_settings(self, _):
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = Path(temp_dir)
            config_path = runtime / "config" / "instances" / "default.json"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                json.dumps(
                    {
                        "CurrentController": "Adb",
                        "AdbDevice": {"AdbSerial": "emulator-5554"},
                    }
                ),
                encoding="utf-8",
            )

            result = configure_adb_screencap(runtime)

            config = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(result, config_path)
            self.assertEqual(config["AdbControlScreenCapType"], "Encode")
            self.assertEqual(config["AdbDevice"]["AdbSerial"], "emulator-5554")

    @patch("tools.configure_mfaa_adb.is_mfaavalonia_running", return_value=True)
    def test_refuses_to_write_while_mfaavalonia_is_running(self, _):
        with self.assertRaisesRegex(RuntimeError, "MFAAvalonia is running"):
            configure_adb_screencap(Path("unused"))


if __name__ == "__main__":
    unittest.main()
