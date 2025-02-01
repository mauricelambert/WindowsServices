#!/usr/bin/env python3
# -*- coding: utf-8 -*-

###################
#    This file implements a Windows service in python.
#    Copyright (C) 2025  Maurice Lambert

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
###################

"""
This file implements a Windows service in python.
"""

__version__ = "0.0.1"
__author__ = "Maurice Lambert"
__author_email__ = "mauricelambert434@gmail.com"
__maintainer__ = "Maurice Lambert"
__maintainer_email__ = "mauricelambert434@gmail.com"
__description__ = """
This file implements a Windows service in python.
"""
__url__ = "https://github.com/mauricelambert/WindowsServices"

# __all__ = []

__license__ = "GPL-3.0 License"
__copyright__ = """
WindowsServices  Copyright (C) 2025  Maurice Lambert
This program comes with ABSOLUTELY NO WARRANTY.
This is free software, and you are welcome to redistribute it
under certain conditions.
"""
copyright = __copyright__
license = __license__

print(copyright)

from ctypes import (
    c_wchar_p,
    windll,
    Structure,
    c_uint32,
    c_void_p,
    CFUNCTYPE,
    POINTER,
    c_uint16,
    cast,
    pointer,
)
from ctypes.wintypes import HANDLE
from threading import Thread
from sys import exit, stderr

SERVICE_WIN32_OWN_PROCESS = 0x00000010
SERVICE_START_PENDING     = 0x00000002
SERVICE_RUNNING           = 0x00000004
SERVICE_STOP_PENDING      = 0x00000003
SERVICE_STOPPED           = 0x00000001

SERVICE_ACCEPT_STOP       = 0x00000001
SERVICE_ACCEPT_SHUTDOWN   = 0x00000004

SERVICE_CONTROL_STOP      = 0x00000001
SERVICE_CONTROL_SHUTDOWN  = 0x00000005

INFINITE                  = 0xFFFFFFFF

kernel32 = windll.LoadLibrary("kernel32.dll")
advapi32 = windll.LoadLibrary("advapi32.dll")

CreateEventW                = kernel32.CreateEventW
SetEvent                    = kernel32.SetEvent
WaitForSingleObject         = kernel32.WaitForSingleObject

RegisterServiceCtrlHandlerW = advapi32.RegisterServiceCtrlHandlerW
SetServiceStatus            = advapi32.SetServiceStatus
StartServiceCtrlDispatcherW = advapi32.StartServiceCtrlDispatcherW


class SERVICE_STATUS(Structure):
    _fields_ = [
        ("dwServiceType", c_uint32),
        ("dwCurrentState", c_uint32),
        ("dwControlsAccepted", c_uint32),
        ("dwWin32ExitCode", c_uint32),
        ("dwServiceSpecificExitCode", c_uint32),
        ("dwCheckPoint", c_uint32),
        ("dwWaitHint", c_uint32)
    ]


class SERVICE_TABLE_ENTRY(Structure):
    _fields_ = [
        ("lpServiceName", c_wchar_p),
        ("lpServiceProc", c_void_p)
    ]


stop_event = HANDLE()
service_handle = HANDLE()
current_status = SERVICE_STATUS()


def main() -> int:
    """
    The main function to start the script from the command line.
    """

    service_table = (SERVICE_TABLE_ENTRY * 2)()
    service_table[0].lpServiceName = c_wchar_p("MinimalPythonService")
    service_table[0].lpServiceProc = cast(service_main, c_void_p)

    return StartServiceCtrlDispatcherW(pointer(service_table))


@CFUNCTYPE(c_void_p, c_uint32, POINTER(POINTER(c_uint16)))
def service_main(argc, argv):
    """
    The service main function for the service interface.
    """

    global stop_event, service_handle
    service_handle = RegisterServiceCtrlHandlerW(
        c_wchar_p("MinimalPythonService"),
        service_control_handler
    )
    if not service_handle:
        print("error register service control", file=stderr)
        return c_void_p(1)

    stop_event = CreateEventW(None, 1, 0, None)
    if not stop_event:
        print("error creating event", file=stderr)
        return c_void_p(2)

    current_status.dwServiceType = SERVICE_WIN32_OWN_PROCESS
    current_status.dwCurrentState = SERVICE_START_PENDING
    current_status.dwControlsAccepted = 0
    current_status.dwWin32ExitCode = 0
    current_status.dwCheckPoint = 1

    set_service_status(SERVICE_START_PENDING)

    Thread(target=run).start()

    set_service_status(SERVICE_RUNNING)
    WaitForSingleObject(stop_event, INFINITE)
    set_service_status(SERVICE_STOPPED)

    return c_void_p(0)


@CFUNCTYPE(c_void_p, c_uint32)
def service_control_handler(control_code):
    """
    The service control function for the service interface.
    """

    if (
        control_code == SERVICE_CONTROL_STOP or
        control_code == SERVICE_CONTROL_SHUTDOWN
    ):
        set_service_status(SERVICE_STOP_PENDING)
        SetEvent(stop_event)
    else:
        return c_void_p(1)
    return c_void_p(0)


def set_service_status(state):
    """
    This function sets the service state using service interface.
    """

    current_status.dwCurrentState = state

    if state == SERVICE_RUNNING:
        current_status.dwControlsAccepted = SERVICE_ACCEPT_STOP | SERVICE_ACCEPT_SHUTDOWN
    else:
        current_status.dwControlsAccepted = 0

    SetServiceStatus(service_handle, pointer(current_status))

def run():
    with open(r"C:\Windows\Temp\PyWinService.txt", "a") as file:
        print("running", file=file)


if __name__ == "__main__":
    exit(main())
