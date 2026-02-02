"""Tests for voxelops.exceptions -- exception hierarchy and messages."""

import pytest

from voxelops.exceptions import (
    YALabProcedureError,
    ProcedureExecutionError,
    ProcedureConfigurationError,
    InputValidationError,
    OutputCollectionError,
    DockerExecutionError,
    FreeSurferLicenseError,
    BIDSValidationError,
    DependencyError,
    ProcedureError,
)


# -- Hierarchy / instantiation -----------------------------------------------


class TestYALabProcedureError:
    def test_instantiation(self):
        e = YALabProcedureError("boom")
        assert str(e) == "boom"
        assert isinstance(e, Exception)

    def test_is_base_of_all(self):
        assert issubclass(ProcedureExecutionError, YALabProcedureError)
        assert issubclass(ProcedureConfigurationError, YALabProcedureError)
        assert issubclass(InputValidationError, YALabProcedureError)
        assert issubclass(OutputCollectionError, YALabProcedureError)
        assert issubclass(BIDSValidationError, YALabProcedureError)
        assert issubclass(DependencyError, YALabProcedureError)


class TestProcedureError:
    def test_alias(self):
        assert ProcedureError is YALabProcedureError


class TestProcedureExecutionError:
    def test_basic(self):
        e = ProcedureExecutionError("qsiprep", "something broke")
        assert e.procedure_name == "qsiprep"
        assert e.original_error is None
        assert "qsiprep failed: something broke" in str(e)

    def test_with_original_error(self):
        orig = RuntimeError("disk full")
        e = ProcedureExecutionError("heudiconv", "fail", original_error=orig)
        assert e.original_error is orig


class TestProcedureConfigurationError:
    def test_instantiation(self):
        e = ProcedureConfigurationError("bad config")
        assert str(e) == "bad config"
        assert isinstance(e, YALabProcedureError)


class TestInputValidationError:
    def test_instantiation(self):
        e = InputValidationError("missing dir")
        assert str(e) == "missing dir"
        assert isinstance(e, YALabProcedureError)


class TestOutputCollectionError:
    def test_instantiation(self):
        e = OutputCollectionError("no output")
        assert str(e) == "no output"
        assert isinstance(e, YALabProcedureError)


class TestBIDSValidationError:
    def test_instantiation(self):
        e = BIDSValidationError("bad bids")
        assert str(e) == "bad bids"
        assert isinstance(e, YALabProcedureError)


# -- DockerExecutionError -----------------------------------------------------


class TestDockerExecutionError:
    def test_empty_stderr(self):
        e = DockerExecutionError("qsiprep", "nipy/heudiconv:1.0", 1, "")
        assert e.container == "nipy/heudiconv:1.0"
        assert e.exit_code == 1
        assert e.stderr == ""
        assert "exited with code 1" in str(e)
        # no stderr snippet when empty
        assert ": " not in str(e).split("code 1")[1]

    def test_short_stderr(self):
        e = DockerExecutionError("qsiprep", "img", 2, "oops")
        assert "oops" in str(e)

    def test_long_stderr_truncated(self):
        long_err = "x" * 600
        e = DockerExecutionError("qsiprep", "img", 3, long_err)
        assert "..." in str(e)
        # first 500 chars present
        assert "x" * 500 in str(e)

    def test_inheritance(self):
        e = DockerExecutionError("p", "c", 1, "err")
        assert isinstance(e, ProcedureExecutionError)
        assert isinstance(e, YALabProcedureError)


# -- FreeSurferLicenseError ---------------------------------------------------


class TestFreeSurferLicenseError:
    def test_default_message(self):
        e = FreeSurferLicenseError()
        assert "FreeSurfer license not found" in str(e)

    def test_custom_message(self):
        e = FreeSurferLicenseError("custom msg")
        assert str(e) == "custom msg"

    def test_inheritance(self):
        assert issubclass(FreeSurferLicenseError, ProcedureConfigurationError)


# -- DependencyError ----------------------------------------------------------


class TestDependencyError:
    def test_default_message(self):
        e = DependencyError("docker")
        assert e.dependency == "docker"
        assert "docker" in str(e)
        assert "not available" in str(e)

    def test_custom_message(self):
        e = DependencyError("parcellate", message="install parcellate first")
        assert str(e) == "install parcellate first"
        assert e.dependency == "parcellate"

    def test_inheritance(self):
        assert issubclass(DependencyError, YALabProcedureError)
