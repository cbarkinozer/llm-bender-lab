"""Fail-closed export/upload preflight checks; no model loads or network calls."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GGUFExportTests(unittest.TestCase):
    def test_invalid_adapter_is_rejected_before_merge(self):
        module = load('export_occam_gguf')
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            (work / 'adapter').mkdir()
            (work / 'adapter' / 'adapter_model.safetensors').write_bytes(b'not the released adapter')
            with patch('sys.argv', ['export', '--work', str(work)]), self.assertRaises(SystemExit):
                module.main()
            self.assertFalse((work / 'merged').exists())

    def test_existing_merged_folder_is_not_overwritten(self):
        module = load('export_occam_gguf')
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            (work / 'merged').mkdir()
            with patch('sys.argv', ['export', '--work', str(work)]), self.assertRaises(SystemExit):
                module.main()

    def test_upload_refuses_extra_files_before_reading_credentials(self):
        module = load('upload_occam_gguf')
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            (work / 'upload').mkdir()
            (work / 'upload' / '.env').write_text('synthetic fixture')
            with patch('sys.argv', ['upload', '--work', str(work)]), patch.object(module, 'dotenv_values') as credentials:
                with self.assertRaises(ValueError):
                    module.main()
                credentials.assert_not_called()

    def test_upload_receipt_prevents_blind_duplicate_commit(self):
        module = load('upload_occam_gguf')
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            (work / 'gguf-upload-receipt.json').write_text('{}')
            with patch('sys.argv', ['upload', '--work', str(work)]), patch.object(module, 'HfApi') as api:
                with self.assertRaises(ValueError):
                    module.main()
                api.assert_not_called()


if __name__ == '__main__':
    unittest.main()
