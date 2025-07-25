from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Callable

import pytest
from flow.record import GroupedRecord

from dissect.target.plugins.os.windows.tasks._plugin import TaskRecord, TasksPlugin
from tests._utils import absolute_path

if TYPE_CHECKING:
    from dissect.target.filesystem import Filesystem
    from dissect.target.target import Target


@pytest.fixture
def setup_tasks_test(target_win: Target, fs_win: Filesystem) -> None:
    xml_task_file = absolute_path("_data/plugins/os/windows/tasks/MapsToastTask")
    atjob_task_file = absolute_path("_data/plugins/os/windows/tasks/AtTask.job")

    fs_win.map_file("windows/system32/tasks/Microsoft/Windows/Maps/MapsToastTask", xml_task_file)
    fs_win.map_file(
        "windows/system32/GroupPolicy/DataStore/ANY_SID/Machine/Preferences/ScheduledTasks/test_xml.xml", xml_task_file
    )
    fs_win.map_file("windows/tasks/AtTask.job", atjob_task_file)

    target_win.add_plugin(TasksPlugin)


@pytest.fixture
def setup_invalid_tasks_test(target_win: Target, fs_win: Filesystem, setup_tasks_test: None) -> None:
    xml_task_file_invalid = absolute_path("_data/plugins/os/windows/tasks/InvalidTask")

    fs_win.map_file("windows/system32/tasks/Microsoft/Windows/Maps/InvalidTask", xml_task_file_invalid)
    fs_win.map_file(
        "windows/system32/GroupPolicy/DataStore/ANY_SID/Machine/Preferences/ScheduledTasks/invalid_xml.xml",
        xml_task_file_invalid,
    )

    target_win.add_plugin(TasksPlugin)


def assert_xml_task_properties(xml_task: TaskRecord) -> None:
    assert str(xml_task.uri) == "\\Microsoft\\Windows\\Maps\\MapsToastTask"
    assert (
        xml_task.security_descriptor
        == "D:(A;;0x111FFFFF;;;SY)(A;;0x111FFFFF;;;BA)(A;;0x111FFFFF;;;S-1-5-80-3028837079-3186095147-955107200-3701964851-1150726376)(A;;FRFX;;;AU)"  # noqa: E501
    )
    assert xml_task.source is None
    assert xml_task.date == datetime(2014, 11, 5, 0, 0, 0, tzinfo=timezone.utc)
    assert xml_task.last_run_date is None
    assert xml_task.author == "$(@%SystemRoot%\\system32\\mapstoasttask.dll,-600)"
    assert xml_task.version is None
    assert xml_task.description == "$(@%SystemRoot%\\system32\\mapstoasttask.dll,-602)"
    assert xml_task.documentation is None
    assert xml_task.principal_id == "Users"
    assert xml_task.user_id is None
    assert xml_task.logon_type is None
    assert xml_task.group_id == "S-1-5-4"
    assert xml_task.display_name == "test_xml.xml"
    assert xml_task.run_level is None
    assert xml_task.process_token_sid_type is None
    assert xml_task.required_privileges is None
    assert xml_task.allow_start_on_demand is None
    assert xml_task.restart_on_failure_interval is None
    assert xml_task.restart_on_failure_count is None
    assert xml_task.mutiple_instances_policy == "Queue"
    assert not xml_task.disallow_start_on_batteries
    assert not xml_task.stop_going_on_batteries
    assert xml_task.start_when_available
    assert xml_task.network_profile_name is None
    assert xml_task.run_only_network_available is None
    assert xml_task.wake_to_run is None
    assert xml_task.enabled
    assert xml_task.hidden
    assert xml_task.delete_expired_task_after is None
    assert xml_task.idle_duration is None
    assert xml_task.idle_wait_timeout is None
    assert not xml_task.idle_stop_on_idle_end
    assert not xml_task.idle_restart_on_idle
    assert xml_task.network_settings_name is None
    assert xml_task.network_settings_id is None
    assert xml_task.execution_time_limit == "PT5S"
    assert xml_task.priority is None
    assert xml_task.run_only_idle is None
    assert xml_task.unified_scheduling_engine
    assert xml_task.disallow_start_on_remote_app_session is None
    assert xml_task.data is None


def assert_at_task_properties(at_task: TaskRecord) -> None:
    assert at_task.uri is None
    assert at_task.security_descriptor is None
    assert str(at_task.task_path) == "sysvol\\windows\\tasks\\AtTask.job"
    assert at_task.date is None
    assert at_task.last_run_date == datetime(2023, 5, 21, 10, 44, 25, 794000, tzinfo=timezone.utc)
    assert at_task.author == "user1"
    assert at_task.version == "1"
    assert at_task.description == "At job task for testing purposes"
    assert at_task.documentation is None
    assert at_task.principal_id is None
    assert at_task.user_id is None
    assert at_task.logon_type is None
    assert at_task.group_id is None
    assert at_task.display_name is None
    assert at_task.run_level is None
    assert at_task.process_token_sid_type is None
    assert at_task.required_privileges is None
    assert at_task.allow_start_on_demand is None
    assert at_task.restart_on_failure_interval is None
    assert at_task.restart_on_failure_count == "0"
    assert at_task.mutiple_instances_policy is None
    assert at_task.disallow_start_on_batteries
    assert at_task.stop_going_on_batteries
    assert at_task.start_when_available is None
    assert at_task.network_profile_name is None
    assert not at_task.run_only_network_available
    assert at_task.wake_to_run
    assert at_task.enabled
    assert not at_task.hidden
    assert at_task.delete_expired_task_after is None
    assert at_task.idle_duration == "PT15M"
    assert at_task.idle_wait_timeout == "PT1H"
    assert at_task.idle_stop_on_idle_end
    assert not at_task.idle_restart_on_idle
    assert at_task.network_settings_name is None
    assert at_task.network_settings_id is None
    assert at_task.execution_time_limit == "P3D"
    assert at_task.priority == "normal"
    assert at_task.run_only_idle
    assert at_task.unified_scheduling_engine is None
    assert at_task.disallow_start_on_remote_app_session is None
    assert at_task.data == "[]"


def assert_xml_task_grouped_properties(xml_task_grouped: GroupedRecord) -> None:
    assert xml_task_grouped.action_type == "ComHandler"
    assert xml_task_grouped.class_id == "{9885AEF2-BD9F-41E0-B15E-B3141395E803}"
    assert xml_task_grouped.com_data == "<Data>$(Arg0);$(Arg1);$(Arg2);$(Arg3);$(Arg4);$(Arg5);$(Arg6);$(Arg7)</Data>"
    assert xml_task_grouped.data is None


def assert_at_task_grouped_exec(at_task_grouped: GroupedRecord) -> None:
    assert at_task_grouped.action_type == "Exec"
    assert at_task_grouped.arguments == ""
    assert at_task_grouped.command == "C:\\WINDOWS\\NOTEPAD.EXE"
    assert at_task_grouped.working_directory == "C:\\Documents and Settings\\John"


def assert_at_task_grouped_daily(at_task_grouped: GroupedRecord) -> None:
    assert at_task_grouped.days_between_triggers == 3
    assert at_task_grouped.end_boundary == datetime.fromisoformat("2023-05-12 00:00:00+00:00")
    assert at_task_grouped.execution_time_limit == "P3D"
    assert at_task_grouped.repetition_duration == "PT13H15M"
    assert at_task_grouped.repetition_interval == "PT12M"
    assert at_task_grouped.repetition_stop_duration_end
    assert at_task_grouped.start_boundary == datetime.fromisoformat("2023-05-11 00:00:00+00:00")
    assert_at_task_grouped_padding(at_task_grouped)


def assert_at_task_grouped_padding(at_task_grouped: GroupedRecord) -> None:
    assert at_task_grouped.padding == 0
    assert at_task_grouped.reserved2 == 0
    assert at_task_grouped.reserved3 == 0


def assert_at_task_grouped_monthlydow(at_task_grouped: GroupedRecord) -> None:
    assert at_task_grouped.records[0].enabled
    assert at_task_grouped.records[1].trigger_enabled
    assert at_task_grouped.start_boundary == datetime.fromisoformat("2023-05-11 00:00:00+00:00")
    assert at_task_grouped.end_boundary == datetime.fromisoformat("2023-05-20 00:00:00+00:00")
    assert at_task_grouped.repetition_interval == "PT1M"
    assert at_task_grouped.repetition_duration == "PT12H13M"
    assert at_task_grouped.repetition_stop_duration_end
    assert at_task_grouped.execution_time_limit == "P3D"
    assert at_task_grouped.which_week == [2]
    assert at_task_grouped.days_of_week == ["Wednesday"]
    assert at_task_grouped.months_of_year == ["June", "September"]
    assert_at_task_grouped_padding(at_task_grouped)


def assert_at_task_grouped_weekly(at_task_grouped: GroupedRecord) -> None:
    assert at_task_grouped.records[0].enabled
    assert at_task_grouped.records[1].trigger_enabled
    assert at_task_grouped.end_boundary == datetime.fromisoformat("2023-05-27 00:00:00+00:00")
    assert at_task_grouped.execution_time_limit == "P3D"
    assert at_task_grouped.repetition_duration == "PT1H"
    assert at_task_grouped.repetition_interval == "PT10M"
    assert at_task_grouped.repetition_stop_duration_end
    assert at_task_grouped.start_boundary == datetime.fromisoformat("2023-05-23 00:00:00+00:00")
    assert at_task_grouped.days_of_week == ["Monday", "Wednesday", "Friday"]
    assert at_task_grouped.unused == [0]
    assert at_task_grouped.weeks_between_triggers == 1
    assert_at_task_grouped_padding(at_task_grouped)


def assert_at_task_grouped_monthly_date(at_task_grouped: GroupedRecord) -> None:
    assert at_task_grouped.records[0].enabled
    assert at_task_grouped.records[1].trigger_enabled
    assert at_task_grouped.day_of_month == [15]
    assert at_task_grouped.months_of_year == ["March", "May", "June", "July", "August", "October"]
    assert at_task_grouped.end_boundary == datetime.fromisoformat("2023-05-29 00:00:00+00:00")
    assert at_task_grouped.execution_time_limit == "P3D"
    assert at_task_grouped.repetition_duration == "PT4H44M"
    assert at_task_grouped.repetition_interval == "PT17M"
    assert at_task_grouped.repetition_stop_duration_end
    assert at_task_grouped.start_boundary == datetime.fromisoformat("2023-05-23 00:00:00+00:00")


def assert_xml_task_trigger_properties(xml_task: GroupedRecord) -> None:
    assert xml_task.records[0].enabled
    assert xml_task.records[1].trigger_enabled
    assert xml_task.days_between_triggers == 1
    assert xml_task.start_boundary == datetime.fromisoformat("2023-05-12 00:00:00+00:00")


@pytest.mark.parametrize(
    ("assert_func", "marker"),
    [
        (assert_xml_task_properties, "test_xml.xml.*ComHandler"),
        (assert_xml_task_properties, "MapsToastTask.*toast"),
        (assert_at_task_properties, "AtTask"),
    ],
)
def test_single_record_properties(
    target_win: Target, setup_tasks_test: None, assert_func: Callable, marker: str
) -> None:
    records = list(target_win.tasks(group=True))
    assert len(records) == 18
    pat = re.compile(rf"{marker}")
    records = filter(lambda x: re.findall(pat, str(x)), records)
    assert_func(next(iter(records)))


@pytest.mark.parametrize(
    ("assert_func", "marker"),
    [
        (assert_xml_task_grouped_properties, "test_xml.xml.*ComHandler"),
        (assert_xml_task_grouped_properties, "MapsToastTask.*ComHandler"),
        (assert_xml_task_trigger_properties, "MapsToastTask.*trigger_enabled"),
        (assert_at_task_grouped_exec, "NOTEPAD.EXE"),
        (assert_at_task_grouped_daily, "PT13H15M"),
        (assert_at_task_grouped_monthlydow, "June"),
        (assert_at_task_grouped_weekly, "Friday"),
        (assert_at_task_grouped_monthly_date, "2023-05-29"),
    ],
)
def test_grouped_record_properties(
    target_win: Target, setup_invalid_tasks_test: pytest.fixture, assert_func: Callable, marker: str
) -> None:
    records = list(target_win.tasks(group=True))
    assert len(records) == 18
    pat = re.compile(rf"{marker}")
    grouped_records = filter(lambda x: re.findall(pat, str(x)) and isinstance(x, GroupedRecord), records)
    assert_func(next(iter(grouped_records)))


def test_xml_task_invalid(
    target_win: Target, setup_invalid_tasks_test: pytest.fixture, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.clear()
    with caplog.at_level(logging.WARNING, target_win.log.name):
        assert len(list(target_win.tasks(group=True))) == 18
        assert "Invalid task file encountered:" in caplog.text
