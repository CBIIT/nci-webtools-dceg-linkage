import importlib
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock


try:
    import flask  # noqa: F401
except ModuleNotFoundError:
    FLASK_AVAILABLE = False
else:
    FLASK_AVAILABLE = True


INVALID_REFERENCES = [
    "",
    "   ",
    "not-a-uuid",
    "12345",
    "../secret",
    "..\\secret",
    "/tmp/secret",
    "abc; rm -rf /",
    "abc && whoami",
    "abc | whoami",
    "$(whoami)",
    "`whoami`",
    "00000000-0000-0000-0000-000000000000",
]

VALID_REFERENCE = "f47ac10b-58cc-4372-a567-0e02b2c3d479"


def _module(**attributes):
    module = types.ModuleType("stub")
    for name, value in attributes.items():
        setattr(module, name, value)
    return module


def _stub_function(*args, **kwargs):
    return None


@unittest.skipUnless(FLASK_AVAILABLE, "Flask is required to import the LDlink app")
class StructuralInputGuardTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.server_path = str(Path(__file__).resolve().parents[2] / "server")
        sys.path.insert(0, self.server_path)
        self.addCleanup(self._remove_server_path)

        config = {
            "tmp_dir": f"{self.temp_dir.name}/tmp/",
            "data_dir": f"{self.temp_dir.name}/data/",
            "log_level": "ERROR",
        }
        genome_build_vars = {"vars": ["grch37", "grch38", "hg19", "hg38"]}

        stubs = {
            "LDpair": _module(calculate_pair=_stub_function),
            "LDpop": _module(calculate_pop=_stub_function),
            "LDproxy": _module(calculate_proxy=_stub_function),
            "LDtrait": _module(calculate_trait=_stub_function, get_ldtrait_timestamp=_stub_function),
            "LDexpress": _module(calculate_express=_stub_function, get_ldexpress_tissues=_stub_function),
            "LDmatrix": _module(calculate_matrix=_stub_function),
            "LDhap": _module(calculate_hap=_stub_function),
            "LDassoc": _module(calculate_assoc=_stub_function),
            "LDscore": _module(calculate_ldscore=_stub_function),
            "LDutilites": _module(get_config=lambda: config, unlock_stale_tokens=_stub_function),
            "LDcommon": _module(genome_build_vars=genome_build_vars, connectMongoDBReadOnly=_stub_function),
            "SNPclip": _module(calculate_clip=_stub_function),
            "SNPchip": _module(calculate_chip=_stub_function, get_platform_request=_stub_function),
            "Cleanup": _module(schedule_tmp_cleanup=_stub_function, schedule_tmp_cleanup_ldscore=_stub_function),
            "requests": types.ModuleType("requests"),
            "ApiAccess": _module(
                register_user=_stub_function,
                checkToken=_stub_function,
                checkApiServer2Auth=_stub_function,
                checkBlocked=_stub_function,
                checkLocked=_stub_function,
                toggleLocked=_stub_function,
                logAccess=_stub_function,
                emailJustification=_stub_function,
                blockUser=_stub_function,
                unblockUser=_stub_function,
                getStats=_stub_function,
                setUserLock=_stub_function,
                setUserApi2Auth=_stub_function,
                unlockAllUsers=_stub_function,
                getLockedUsers=_stub_function,
                getBlockedUsers=_stub_function,
                lookupUser=_stub_function,
            ),
            "ldscore": types.ModuleType("ldscore"),
            "ldscore.ldsc_utils": _module(
                run_ldsc_command=_stub_function,
                run_herit_command=_stub_function,
                run_correlation_command=_stub_function,
                validBfile=_stub_function,
            ),
        }

        self.modules_patch = mock.patch.dict(sys.modules, stubs)
        self.modules_patch.start()
        self.addCleanup(self.modules_patch.stop)

        sys.modules.pop("LDlink", None)
        self.addCleanup(sys.modules.pop, "LDlink", None)
        self.ldlink = importlib.import_module("LDlink")
        self.ldlink.app.config.update(TESTING=True)
        self.client = self.ldlink.app.test_client()

    def _remove_server_path(self):
        if self.server_path in sys.path:
            sys.path.remove(self.server_path)

    def _replace_view(self, endpoint):
        calls = []

        def guarded_view(**kwargs):
            calls.append(kwargs)
            return {"ok": True}

        self.ldlink.app.view_functions[endpoint] = guarded_view
        return calls

    def test_invalid_query_reference_is_rejected_before_file_handler(self):
        for reference in INVALID_REFERENCES:
            with self.subTest(reference=reference):
                calls = self._replace_view("validate_sumstats")

                response = self.client.get(
                    "/LDlinkRestWeb/validate_sumstats",
                    query_string={"filename": "sumstats.txt", "reference": reference},
                )

                self.assertEqual(400, response.status_code)
                self.assertEqual({"error": "Invalid reference parameter."}, response.get_json())
                self.assertEqual([], calls)

    def test_invalid_json_reference_is_rejected_before_zip_file_handler(self):
        for reference in INVALID_REFERENCES:
            with self.subTest(reference=reference):
                calls = self._replace_view("zip_files")

                response = self.client.post(
                    "/LDlinkRestWeb/zip",
                    json={"files": ["sumstats.txt"], "reference": reference},
                )

                self.assertEqual(400, response.status_code)
                self.assertEqual({"error": "Invalid reference parameter."}, response.get_json())
                self.assertEqual([], calls)

    def test_invalid_ldscore_reference_is_rejected_before_command_handler(self):
        for reference in INVALID_REFERENCES:
            with self.subTest(reference=reference):
                calls = self._replace_view("ldscore")

                response = self.client.get(
                    "/LDlinkRestWeb/ldscore",
                    query_string={"filename": "sumstats.txt", "reference": reference},
                )

                self.assertEqual(400, response.status_code)
                self.assertEqual({"error": "Invalid reference parameter."}, response.get_json())
                self.assertEqual([], calls)

    def test_valid_reference_reaches_guarded_handler(self):
        calls = self._replace_view("validate_sumstats")

        response = self.client.get(
            "/LDlinkRestWeb/validate_sumstats",
            query_string={"filename": "sumstats.txt", "reference": VALID_REFERENCE},
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual({"ok": True}, response.get_json())
        self.assertEqual([{}], calls)


if __name__ == "__main__":
    unittest.main()