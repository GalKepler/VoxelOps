from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pytest
from voxelops.validation.context import ValidationContext


@dataclass
class MockInputs:
    bids_dir: Optional[Path] = None
    dicom_dir: Optional[Path] = None
    qsiprep_dir: Optional[Path] = None
    output_dir: Optional[Path] = None


@dataclass
class MockConfig:
    some_setting: str = "default_value"
    another_path: Optional[Path] = None


class TestValidationContext:
    def test_init(self):
        context = ValidationContext(
            procedure_name="test_proc", participant="01", session="01"
        )
        assert context.procedure_name == "test_proc"
        assert context.participant == "01"
        assert context.session == "01"
        assert context.inputs is None
        assert context.config is None
        assert context.execution_result is None
        assert context.brain_bank_config is None

    def test_participant_label(self):
        context = ValidationContext(procedure_name="test_proc", participant="01")
        assert context.participant_label == "sub-01"

    def test_session_label(self):
        context_with_session = ValidationContext(
            procedure_name="test_proc", participant="01", session="01"
        )
        assert context_with_session.session_label == "ses-01"

        context_no_session = ValidationContext(
            procedure_name="test_proc", participant="01"
        )
        assert context_no_session.session_label is None

    @pytest.mark.parametrize(
        "inputs_attr, expected_path",
        [
            ("bids_dir", "/data/bids"),
            ("dicom_dir", "/data/dicom"),
            ("qsiprep_dir", "/data/qsiprep"),
            ("non_existent_dir", None),
        ],
    )
    def test_input_dir(self, inputs_attr, expected_path):
        mock_inputs_dict = {inputs_attr: Path(expected_path)} if expected_path else {}
        mock_inputs = MockInputs(**mock_inputs_dict)

        context = ValidationContext(
            procedure_name="test_proc",
            participant="01",
            inputs=mock_inputs,
        )
        if expected_path:
            assert context.input_dir == Path(expected_path)
        else:
            assert context.input_dir is None

    def test_input_dir_precedence(self):
        # Test precedence: bids_dir should be preferred if multiple exist
        mock_inputs = MockInputs(
            dicom_dir=Path("/data/dicom"), bids_dir=Path("/data/bids")
        )
        context = ValidationContext(
            procedure_name="test_proc", participant="01", inputs=mock_inputs
        )
        assert context.input_dir == Path("/data/bids")

    def test_output_dir(self):
        mock_inputs = MockInputs(output_dir=Path("/output"))
        context = ValidationContext(
            procedure_name="test_proc", participant="01", inputs=mock_inputs
        )
        assert context.output_dir == Path("/output")

        context_no_output_attr = ValidationContext(
            procedure_name="test_proc", participant="01", inputs=MockInputs()
        )
        assert context_no_output_attr.output_dir is None

        context_no_inputs = ValidationContext(
            procedure_name="test_proc", participant="01"
        )
        assert context_no_inputs.output_dir is None

    def test_participant_dir(self):
        mock_inputs = MockInputs(bids_dir=Path("/data"))
        context = ValidationContext(
            procedure_name="test_proc", participant="01", inputs=mock_inputs
        )
        assert context.participant_dir == Path("/data/sub-01")

        context_with_session = ValidationContext(
            procedure_name="test_proc",
            participant="01",
            session="01",
            inputs=mock_inputs,
        )
        assert context_with_session.participant_dir == Path("/data/sub-01/ses-01")

        context_no_input_dir = ValidationContext(
            procedure_name="test_proc", participant="01"
        )
        assert context_no_input_dir.participant_dir is None

    def test_get_config_value_from_brain_bank_proc_config(self):
        brain_bank_config = {
            "test_proc": {"timeout": 120},
            "global_setting": "global_val",
        }
        mock_config = MockConfig(some_setting="local_val")
        context = ValidationContext(
            procedure_name="test_proc",
            participant="01",
            config=mock_config,
            brain_bank_config=brain_bank_config,
        )
        assert context.get_config_value("timeout") == 120

    def test_get_config_value_from_brain_bank_global_config(self):
        brain_bank_config = {
            "test_proc_other": {"timeout": 120},  # Different procedure
            "global_setting": "global_val",
        }
        mock_config = MockConfig(some_setting="local_val")
        context = ValidationContext(
            procedure_name="test_proc",
            participant="01",
            config=mock_config,
            brain_bank_config=brain_bank_config,
        )
        assert context.get_config_value("global_setting") == "global_val"

    def test_get_config_value_from_procedure_config(self):
        brain_bank_config = {
            "other_proc": {"timeout": 120},
        }
        mock_config = MockConfig(some_setting="local_val")
        context = ValidationContext(
            procedure_name="test_proc",
            participant="01",
            config=mock_config,
            brain_bank_config=brain_bank_config,
        )
        assert context.get_config_value("some_setting") == "local_val"

    def test_get_config_value_default(self):
        context = ValidationContext(procedure_name="test_proc", participant="01")
        assert context.get_config_value("non_existent", "default") == "default"
        assert context.get_config_value("non_existent") is None
