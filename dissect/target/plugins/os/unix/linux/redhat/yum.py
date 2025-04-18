from __future__ import annotations

import re
from typing import TYPE_CHECKING

from dissect.target.exceptions import UnsupportedPluginError
from dissect.target.helpers.utils import year_rollover_helper
from dissect.target.plugin import export
from dissect.target.plugins.os.unix.packagemanager import (
    OperationTypes,
    PackageManagerLogRecord,
    PackageManagerPlugin,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

YUM_LOG_KEYWORDS = ["Installed", "Updated", "Erased", "Obsoleted"]
RE_TS = re.compile(r"(\w+\s{1,2}\d+\s\d{2}:\d{2}:\d{2})")


class YumPlugin(PackageManagerPlugin):
    """Yum package manager plugin."""

    __namespace__ = "yum"

    LOG_DIR_PATH = "/var/log"
    LOG_FILES_GLOB = "yum.*"

    def check_compatible(self) -> None:
        if not next(self.target.fs.path(self.LOG_DIR_PATH).glob(self.LOG_FILES_GLOB), None):
            raise UnsupportedPluginError("No Yum files found")

    @export(record=PackageManagerLogRecord)
    def logs(self) -> Iterator[PackageManagerLogRecord]:
        """Package manager log parser for CentOS' Yellowdog Updater (Yum).

        Example log format::

            Dec 16 04:41:22 Installed: unzip-6.0-24.el7_9.x86_64
            Dec 16 04:41:25 Installed: unzip-6.0-22.el7_9.x86_64
            Dec 16 04:41:28 Updated: unzip-6.0-24.el7_9.x86_64
            Dec 16 04:41:30 Erased: unzip-6.0-24.el7_9.x86_64
            Dec 16 04:41:34 Installed: unzip-6.0-24.el7_9.x86_64
        """
        target_tz = self.target.datetime.tzinfo

        for path in self.target.fs.path(self.LOG_DIR_PATH).glob(self.LOG_FILES_GLOB):
            for ts, line in year_rollover_helper(path, RE_TS, "%b %d %H:%M:%S", target_tz):
                # Only parse lines that are about installation/erasions/updates, not empty lines or debug statements.
                if not any(keyword in line for keyword in YUM_LOG_KEYWORDS):
                    return

                operation, package_name = line[16:].split(": ")
                yield PackageManagerLogRecord(
                    ts=ts,
                    package_manager="yum",
                    operation=OperationTypes.infer(operation.strip()).value,
                    package_name=package_name,
                    _target=self.target,
                )
