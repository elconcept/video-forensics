# Windows tool bootstrap

Before invoking the h265nal Python bootstrap, the Windows launcher now verifies and, when absent, installs:

- Python 3.12 through `Python.Python.3.12`
- CMake through `Kitware.CMake`
- LLVM/Clang through `LLVM.LLVM`

The PowerShell bootstrap refreshes the current process PATH from machine and user environment values and checks common installation directories, so the same launcher process can continue after Winget completes.

Existing `clang++`, `cl.exe`, or `g++` installations are accepted. No package named `compiler` is requested.
