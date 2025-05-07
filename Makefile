# Makefile for building bsdl executables using PyInstaller

# Detect OS and set executable extension
ifeq ($(OS),Windows_NT)
EXT := .exe
ICON := --icon=bsdl.ico
else ifneq (,$(findstring MINGW,$(shell uname -s)))
EXT := .exe
ICON := --icon=bsdl.ico
else ifneq (,$(findstring CYGWIN,$(shell uname -s)))
EXT := .exe
ICON := --icon=bsdl.ico
else
EXT :=
ICON :=
endif

.PHONY: all clean check-pyinstaller

# Default target: builds bsdl or bsdl.exe depending on your OS
all: bsdl$(EXT)

bsdl$(EXT): dist/bsdl$(EXT)
	cp -fv dist/bsdl$(EXT) bsdl$(EXT)

# Build the one-file console executable
dist/bsdl$(EXT): check-pyinstaller
	pyinstaller -F -y --console --name bsdl $(ICON) bsdl.py

# Check that pyinstaller is available
check-pyinstaller:
	@command -v pyinstaller >/dev/null 2>&1 || { \
		echo "Error: pyinstaller executable not found. Please run 'pip install pyinstaller' to build standalone executables."; \
		exit 1; \
	}

# Clean up all build artifacts
clean:
	rm -rf build dist __pycache__ *.spec bsdl$(EXT)
