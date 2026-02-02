"""Tests for voxelops.__init__ -- package exports and version."""

import voxelops


class TestPackageExports:
    def test_version(self):
        assert voxelops.__version__ == "2.0.0"

    def test_all_completeness(self):
        for name in voxelops.__all__:
            assert hasattr(voxelops, name), f"{name} listed in __all__ but not importable"

    def test_runner_imports(self):
        assert callable(voxelops.run_heudiconv)
        assert callable(voxelops.run_qsiprep)
        assert callable(voxelops.run_qsirecon)
        assert callable(voxelops.run_qsiparc)

    def test_schema_imports(self):
        for cls_name in [
            "HeudiconvInputs",
            "HeudiconvOutputs",
            "HeudiconvDefaults",
            "QSIPrepInputs",
            "QSIPrepOutputs",
            "QSIPrepDefaults",
            "QSIReconInputs",
            "QSIReconOutputs",
            "QSIReconDefaults",
            "QSIParcInputs",
            "QSIParcOutputs",
            "QSIParcDefaults",
        ]:
            assert hasattr(voxelops, cls_name)

    def test_exception_imports(self):
        assert hasattr(voxelops, "ProcedureError")
        assert hasattr(voxelops, "InputValidationError")
        assert hasattr(voxelops, "ProcedureExecutionError")
