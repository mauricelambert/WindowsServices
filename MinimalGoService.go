/*
    This file implements a minimal service on Windows written in Go
    Copyright (C) 2025  Maurice Lambert

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
*/

// go build -o MinimalGoService.exe MinimalGoService.go
// sc create MinimalGoService binPath= "C:\path\to\MinimalGoService.exe"
// sc start MinimalGoService
// sc stop MinimalGoService
// sc delete MinimalGoService

package main

import (
    "syscall"
    "unsafe"
    "time"
    "fmt"
)

const (
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
)

var (
    kernel32                  = syscall.NewLazyDLL("kernel32.dll")
    createEvent               = kernel32.NewProc("CreateEventW")
    setEvent                  = kernel32.NewProc("SetEvent")
    waitForSingleObject       = kernel32.NewProc("WaitForSingleObject")

    modAdvapi32               = syscall.NewLazyDLL("advapi32.dll")
    procRegisterServiceCtrl   = modAdvapi32.NewProc("RegisterServiceCtrlHandlerW")
    procSetServiceStatus      = modAdvapi32.NewProc("SetServiceStatus")
    procStartServiceCtrlDisp  = modAdvapi32.NewProc("StartServiceCtrlDispatcherW")

    serviceStopEvent          syscall.Handle
    serviceStatusHandle       uintptr
    serviceCurrentStatus      SERVICE_STATUS
)

type SERVICE_STATUS struct {
    dwServiceType             uint32
    dwCurrentState            uint32
    dwControlsAccepted        uint32
    dwWin32ExitCode           uint32
    dwServiceSpecificExitCode uint32
    dwCheckPoint              uint32
    dwWaitHint                uint32
}

type SERVICE_TABLE_ENTRY struct {
    lpServiceName *uint16
    lpServiceProc uintptr
}

func main() {
    serviceName := syscall.StringToUTF16Ptr("MinimalGoService")

    serviceTable := []SERVICE_TABLE_ENTRY{
        {lpServiceName: serviceName, lpServiceProc: syscall.NewCallback(serviceMain)},
        {lpServiceName: nil, lpServiceProc: 0},
    }

    ret, _, err := procStartServiceCtrlDisp.Call(uintptr(unsafe.Pointer(&serviceTable[0])))
    if ret == 0 {
        fmt.Printf("Failed to start service control dispatcher: %v\n", err)
    }
}

func serviceMain(argc uint32, argv **uint16) uintptr {
    serviceStatusHandle, _, _ = procRegisterServiceCtrl.Call(
        uintptr(unsafe.Pointer(syscall.StringToUTF16Ptr("MinimalGoService"))),
        syscall.NewCallback(serviceControlHandler),
    )

    serviceStopEvent, _, err := createEvent.Call(0, 1, 0, 0)

    if err != nil {
        fmt.Printf("Failed to start service control dispatcher: %v\n", err)
    }

    serviceCurrentStatus.dwServiceType = SERVICE_WIN32_OWN_PROCESS
    serviceCurrentStatus.dwCurrentState = SERVICE_START_PENDING
    serviceCurrentStatus.dwControlsAccepted = 0
    serviceCurrentStatus.dwWin32ExitCode = 0
    serviceCurrentStatus.dwCheckPoint = 1

    setServiceStatus(SERVICE_START_PENDING)

    go run()

    setServiceStatus(SERVICE_RUNNING)

    waitForSingleObject.Call(uintptr(serviceStopEvent), INFINITE)

    setServiceStatus(SERVICE_STOPPED)
    return uintptr(0)
}

func serviceControlHandler(controlCode uint32) uintptr {
    switch controlCode {
    case SERVICE_CONTROL_STOP:
        setServiceStatus(SERVICE_STOP_PENDING)
        setEvent.Call(uintptr(serviceStopEvent))
    case SERVICE_CONTROL_SHUTDOWN:
        setServiceStatus(SERVICE_STOP_PENDING)
        setEvent.Call(uintptr(serviceStopEvent))
    default:
        return uintptr(1)
    }
    return uintptr(0)
}

func setServiceStatus(state uint32) {
    serviceCurrentStatus.dwCurrentState = state

    if state == SERVICE_RUNNING {
        serviceCurrentStatus.dwControlsAccepted = SERVICE_ACCEPT_STOP | SERVICE_ACCEPT_SHUTDOWN
    } else {
        serviceCurrentStatus.dwControlsAccepted = 0
    }

    procSetServiceStatus.Call(serviceStatusHandle, uintptr(unsafe.Pointer(&serviceCurrentStatus)))
}

func run(duration time.Duration, callback func()) {
    for {
        start := time.Now()
        callback()
        time.Sleep(duration - time.Since(start))
    }
}
