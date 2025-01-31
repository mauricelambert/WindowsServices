// This file implements a minimal service on Windows written in C

/*
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

// gcc -o MinimalService.exe MinimalServiceC.c -lAdvapi32
// sc create "MinimalService" binPath= "C:\Full\Path\MinimalService.exe"
// sc start "MinimalService"
// sc stop "MinimalService"
// sc delete "MinimalService"

#include <windows.h>
#include <tchar.h>
#include <strsafe.h>

#define SERVICE_NAME _T("MinimalService")

SERVICE_STATUS gServiceStatus = {0};
SERVICE_STATUS_HANDLE gStatusHandle = NULL;
HANDLE gServiceStopEvent = INVALID_HANDLE_VALUE;

VOID WINAPI ServiceMain(DWORD argc, LPTSTR *argv);
VOID WINAPI ServiceCtrlHandler(DWORD);
DWORD WINAPI ServiceWorkerThread(LPVOID lpParam);

int _tmain(int argc, TCHAR *argv[])
{
    SERVICE_TABLE_ENTRY ServiceTable[] = 
    {
        {SERVICE_NAME, (LPSERVICE_MAIN_FUNCTION) ServiceMain},
        {NULL, NULL}
    };

    if (StartServiceCtrlDispatcher(ServiceTable) == FALSE)
    {
        return GetLastError();
    }

    return 0;
}

VOID WINAPI ServiceMain(DWORD argc, LPTSTR *argv)
{
    DWORD Status = E_FAIL;

    gStatusHandle = RegisterServiceCtrlHandler(SERVICE_NAME, ServiceCtrlHandler);

    if (gStatusHandle == NULL) 
    {
        goto EXIT;
    }

    ZeroMemory(&gServiceStatus, sizeof(gServiceStatus));
    gServiceStatus.dwServiceType = SERVICE_WIN32_OWN_PROCESS;
    gServiceStatus.dwControlsAccepted = SERVICE_ACCEPT_STOP | SERVICE_ACCEPT_SHUTDOWN;
    gServiceStatus.dwCurrentState = SERVICE_START_PENDING;
    gServiceStatus.dwWin32ExitCode = 0;
    gServiceStatus.dwServiceSpecificExitCode = 0;
    gServiceStatus.dwCheckPoint = 0;

    if (SetServiceStatus(gStatusHandle, &gServiceStatus) == FALSE)
    {
        OutputDebugString(_T("My Service: ServiceMain: SetServiceStatus returned error"));
    }

    gServiceStopEvent = CreateEvent(NULL, TRUE, FALSE, NULL);
    if (gServiceStopEvent == NULL)
    {
        gServiceStatus.dwControlsAccepted = 0;
        gServiceStatus.dwCurrentState = SERVICE_STOPPED;
        gServiceStatus.dwWin32ExitCode = GetLastError();
        gServiceStatus.dwCheckPoint = 1;

        if (SetServiceStatus(gStatusHandle, &gServiceStatus) == FALSE)
        {
            OutputDebugString(_T("My Service: ServiceMain: SetServiceStatus returned error"));
        }
        goto EXIT;
    }

    gServiceStatus.dwCurrentState = SERVICE_RUNNING;
    gServiceStatus.dwCheckPoint = 0;
    gServiceStatus.dwWaitHint = 0;

    if (SetServiceStatus(gStatusHandle, &gServiceStatus) == FALSE)
    {
        OutputDebugString(_T("My Service: ServiceMain: SetServiceStatus returned error"));
    }

    HANDLE hThread = CreateThread(NULL, 0, ServiceWorkerThread, NULL, 0, NULL);

    WaitForSingleObject(gServiceStopEvent, INFINITE);

    CloseHandle(gServiceStopEvent);

    gServiceStatus.dwCurrentState = SERVICE_STOPPED;
    gServiceStatus.dwCheckPoint = 3;

    if (SetServiceStatus(gStatusHandle, &gServiceStatus) == FALSE)
    {
        OutputDebugString(_T("My Service: ServiceMain: SetServiceStatus returned error"));
    }
    
EXIT:
    return;
}

VOID WINAPI ServiceCtrlHandler(DWORD CtrlCode)
{
    switch(CtrlCode)
    {
        case SERVICE_CONTROL_STOP:
        case SERVICE_CONTROL_SHUTDOWN:
            if (gServiceStatus.dwCurrentState != SERVICE_RUNNING)
                break;

            gServiceStatus.dwControlsAccepted = 0;
            gServiceStatus.dwCurrentState = SERVICE_STOP_PENDING;
            gServiceStatus.dwWin32ExitCode = 0;
            gServiceStatus.dwCheckPoint = 4;

            if (SetServiceStatus(gStatusHandle, &gServiceStatus) == FALSE)
            {
                OutputDebugString(_T("My Service: ServiceCtrlHandler: SetServiceStatus returned error"));
            }

            SetEvent(gServiceStopEvent);
            break;

        default:
            break;
    }
}

DWORD WINAPI ServiceWorkerThread(LPVOID lpParam)
{
    while(WaitForSingleObject(gServiceStopEvent, 0) != WAIT_OBJECT_0)
    {
        // Perform service tasks here
        Sleep(3000);
    }

    return ERROR_SUCCESS;
}
