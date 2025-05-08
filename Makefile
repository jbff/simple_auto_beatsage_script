# Makefile for building bsdl executables using pyinstaller

USING_WINDOWS := false
EXT :=
ICON :=
COPY_CMD := cp -fv

# Detect OS and set executable extension
ifeq ($(OS),Windows_NT)
USING_WINDOWS := true
EXT := .exe
ICON := --icon=bsdl.ico
COPY_CMD := copy /Y
else ifneq (,$(findstring MINGW,$(shell uname -s)))
EXT := .exe
ICON := --icon=bsdl.ico
else ifneq (,$(findstring CYGWIN,$(shell uname -s)))
EXT := .exe
ICON := --icon=bsdl.ico
endif

.PHONY: all clean check-pyinstaller

# Default target: builds bsdl or bsdl.exe depending on your OS
all: bsdl$(EXT)

bsdl$(EXT): dist/bsdl$(EXT)
	$(COPY_CMD) dist/bsdl$(EXT) bsdl$(EXT)

check-pyinstaller:
	@pyinstaller --version || (echo "Error: pyinstaller not found. Please install it with: pip install pyinstaller" && exit 1)

# Build the one-file console executable
dist/bsdl$(EXT): check-pyinstaller
	pyinstaller -F -y --console --name bsdl $(ICON) bsdl.py

# Clean up all build artifacts
clean:
ifeq ($(USING_WINDOWS),true)
	if exist build rmdir /S /Q build
	if exist dist rmdir /S /Q dist
	if exist __pycache__ rmdir /S /Q __pycache__
	if exist *.spec del /Q *.spec
	if exist bsdl$(EXT) del /Q bsdl$(EXT)
else
	rm -rf build dist __pycache__ *.spec bsdl$(EXT)
endif
