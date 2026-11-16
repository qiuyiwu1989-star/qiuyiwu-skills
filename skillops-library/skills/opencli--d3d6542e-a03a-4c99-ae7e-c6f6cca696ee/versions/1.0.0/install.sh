#!/bin/bash
# OpenCLI Installation Script
# Success criteria:
# 1. browser-use tool can operate the browser normally
# 2. opencli tool is installed and running properly
# Supported: Ubuntu/Debian systems, run as root

set -euo pipefail

# ==============================================
# Configuration constants (do not modify)
# ==============================================
OPENCLI_VERSION="1.7.4"
EXTENSION_VERSION="1.0.0"
EXTENSION_URL="https://github.com/jackwener/OpenCLI/releases/download/v${OPENCLI_VERSION}/opencli-extension-v${EXTENSION_VERSION}.zip"
EXTENSION_DIR="/home/browser/opencli-extension"
OPENCALI_CHROMIUM_SCRIPT="/opt/browser-vnc/start-opencli-chromium.sh"
# Browser binary used by the startup script: /opt/cloakbrowser/chrome

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# ==============================================
# Step 1: System environment check & dependency installation
# ==============================================
echo ""
echo "======================================"
echo "  Step 1: System Environment Check"
echo "======================================"

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    print_error "This script must be run as root"
    exit 1
fi

# Check basic dependencies
print_info "Checking basic dependencies..."
DEPENDENCIES=("wget" "unzip" "curl" "sudo" "npm" "node")
for dep in "${DEPENDENCIES[@]}"; do
    if ! command -v "$dep" &> /dev/null; then
        print_info "Installing dependency: $dep"
        apt-get update -y >/dev/null 2>&1
        apt-get install -y "$dep" >/dev/null 2>&1
    fi
done

# Extra packages for commands used by this script.
if ! command -v ss &> /dev/null; then
    print_info "Installing dependency package: iproute2 (provides ss)"
    apt-get update -y >/dev/null 2>&1
    apt-get install -y iproute2 >/dev/null 2>&1
fi

if ! command -v xdpyinfo &> /dev/null; then
    print_info "Installing dependency package: x11-utils (provides xdpyinfo)"
    apt-get update -y >/dev/null 2>&1
    apt-get install -y x11-utils >/dev/null 2>&1
fi

# Check if browser user exists
if ! id -u browser &> /dev/null; then
    print_info "Creating browser user..."
    useradd -m -d /home/browser -s /bin/bash browser
fi

# Ensure /home/browser directory exists
mkdir -p /home/browser
chown browser:browser /home/browser

# ==============================================
# Step 2: Install OpenCLI
# ==============================================
echo ""
echo "======================================"
echo "  Step 2: Install OpenCLI"
echo "======================================"

if command -v opencli &> /dev/null; then
    CURRENT_VERSION=$(opencli --version | awk '{print $2}')
    print_info "Current OpenCLI version: $CURRENT_VERSION"

    if [ "$CURRENT_VERSION" = "$OPENCLI_VERSION" ]; then
        print_info "OpenCLI is already up to date, skipping installation"
    else
        print_info "Upgrading OpenCLI to version $OPENCLI_VERSION..."
        npm install -g "@jackwener/opencli@$OPENCLI_VERSION" --force
    fi
else
    print_info "Installing OpenCLI version $OPENCLI_VERSION..."
    npm install -g "@jackwener/opencli@$OPENCLI_VERSION"
fi

print_success "OpenCLI installed: $(opencli --version)"

# ==============================================
# Step 3: Install browser extension
# ==============================================
pkill -u browser -f chrome || true
rm -rf /home/browser/.config/chrome-openclaw
echo ""
echo "======================================"
echo "  Step 3: Install Browser Extension"
echo "======================================"

# Clean up old extension
if [ -d "$EXTENSION_DIR" ]; then
    print_warning "Cleaning up old extension directory: $EXTENSION_DIR"
    rm -rf "$EXTENSION_DIR"
fi

# Check for local extension package
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCAL_EXT_ZIP="$SCRIPT_DIR/opencli-extension.zip"
LOCAL_EXT_ZIP_VERSIONED="$SCRIPT_DIR/opencli-extension-v${EXTENSION_VERSION}.zip"

# Create a secure temp directory for extension processing
TEMP_WORK_DIR=$(mktemp -d /tmp/opencli-extension-work-XXXXXX)
TEMP_ZIP="$TEMP_WORK_DIR/extension.zip"

if [ -f "$LOCAL_EXT_ZIP" ]; then
    print_info "Found local extension package: $LOCAL_EXT_ZIP, using it directly"
    cp "$LOCAL_EXT_ZIP" "$TEMP_ZIP"
elif [ -f "$LOCAL_EXT_ZIP_VERSIONED" ]; then
    print_info "Found local extension package: $LOCAL_EXT_ZIP_VERSIONED, using it directly"
    cp "$LOCAL_EXT_ZIP_VERSIONED" "$TEMP_ZIP"
else
    # Download extension (with retry and mirror URL)
    print_info "Downloading extension version $EXTENSION_VERSION..."

    # Try direct download
    if ! wget -O "$TEMP_ZIP" "$EXTENSION_URL" --no-verbose --show-progress --tries=3 --timeout=30; then
        print_warning "GitHub download failed, trying mirror URL..."
        MIRROR_URL="https://ghproxy.com/$EXTENSION_URL"
        if ! wget -O "$TEMP_ZIP" "$MIRROR_URL" --no-verbose --show-progress --tries=3 --timeout=30; then
            print_error "Extension download failed, please download manually:"
            echo "  Download URL: $EXTENSION_URL"
            echo "  Mirror URL: $MIRROR_URL"
            echo "  Upload to the server's current directory as either:"
            echo "    opencli-extension.zip"
            echo "    opencli-extension-v${EXTENSION_VERSION}.zip"
            echo "  Then re-run this script"
            exit 1
        fi
    fi
fi

# Extract extension
print_info "Extracting extension to: $EXTENSION_DIR"
mkdir -p "$EXTENSION_DIR"
TEMP_DIR=$(mktemp -d)
unzip -q -o "$TEMP_ZIP" -d "$TEMP_DIR"

# Handle possible nested directory
if [ -d "$TEMP_DIR/opencli-extension" ]; then
    mv "$TEMP_DIR/opencli-extension"/* "$EXTENSION_DIR/"
else
    mv "$TEMP_DIR"/* "$EXTENSION_DIR/"
fi

# Clean up temp files and directories
rm -rf "$TEMP_DIR" "$TEMP_WORK_DIR"

# Fix permissions
print_info "Fixing extension file permissions..."
chown -R browser:browser "$EXTENSION_DIR"
chmod -R 755 "$EXTENSION_DIR"

# Verify extension files
if [ ! -f "$EXTENSION_DIR/manifest.json" ]; then
    print_error "Extension installation failed: manifest.json not found"
    exit 1
fi

print_success "Extension installed: $EXTENSION_DIR"

# ==============================================
# Step 3.5 intentionally removed
# ==============================================
# This installer uses only --load-extension.
# No CRX package, Chrome policy, update.xml, or local update server is created.

# ==============================================
# Step 4: Configure Chromium startup script
# ==============================================
echo ""
echo "======================================"
echo "  Step 4: Configure Chromium Startup Script"
echo "======================================"

mkdir -p "$(dirname "$OPENCALI_CHROMIUM_SCRIPT")"

cat > "$OPENCALI_CHROMIUM_SCRIPT" << 'EOF'
#!/bin/bash
set -euo pipefail

export DISPLAY=:99.0
export HOME=/home/browser
export XDG_CONFIG_HOME=/home/browser/.config
export XDG_CACHE_HOME=/home/browser/.cache
export XDG_RUNTIME_DIR=/tmp/runtime-browser

mkdir -p "$HOME/.config" "$HOME/.cache" "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR" || true

# Wait for X server to be ready
for i in $(seq 1 60); do
    xdpyinfo -display :99 >/dev/null 2>&1 && break
    sleep 1
done

# Load OpenCLI extension directly from the unpacked directory.
# This script intentionally does not use CRX, update.xml, or Chrome policy.
exec /opt/cloakbrowser/chrome \
    --no-sandbox \
    --load-extension=/home/browser/opencli-extension \
    --user-data-dir=/home/browser/.config/chrome-openclaw \
    --profile-directory=Default \
    --disable-breakpad \
    --disable-crash-reporter \
    --disable-notifications \
    --disable-popup-blocking \
    --disable-features=Translate \
    --disable-features=ExternalProtocolDialogShowAlwaysOpenCheckbox \
    --disable-features=MediaSessionService \
    --hide-crash-restore-bubble \
    --disable-session-crashed-bubble \
    --no-first-run \
    --no-default-browser-check \
    --disable-infobars \
    --disable-gpu \
    --disable-gpu-compositing \
    --disable-software-rasterizer \
    --disable-dev-shm-usage \
    --disable-background-timer-throttling \
    --disable-backgrounding-occluded-windows \
    --disable-renderer-backgrounding \
    --start-maximized \
    --password-store=basic \
    --disable-default-apps \
    --remote-debugging-port=9222
EOF

chmod +x "$OPENCALI_CHROMIUM_SCRIPT"
print_success "Chromium startup script configured: $OPENCALI_CHROMIUM_SCRIPT"

# ==============================================
# Step 5: Restart Chromium browser
# ==============================================
echo ""
echo "======================================"
echo "  Step 5: Restart Chromium Browser"
echo "======================================"

# Stop existing Chromium processes
print_info "Stopping existing Chromium processes..."
pkill -u browser -f chrome || true
pkill -f "/opt/cloakbrowser/chrome" || true
pkill -f chromium || true
sleep 3

# Ensure browser-owned profile directories exist before launch.
mkdir -p /home/browser/.config /home/browser/.cache /tmp/runtime-browser
chown -R browser:browser /home/browser/.config /home/browser/.cache /tmp/runtime-browser
chmod 700 /tmp/runtime-browser || true

# Start Chromium as the browser user so HOME, profile, and extension permissions are consistent.
print_info "Starting Chromium browser with --load-extension as browser user..."
sudo -u browser -H bash "$OPENCALI_CHROMIUM_SCRIPT" > /tmp/chrome-start.log 2>&1 &

# Wait for browser to start and debug port to be ready
print_info "Waiting for Chromium to start..."
for i in $(seq 1 30); do
    if ss -tlnp | grep -q ":9222 "; then
        break
    fi
    sleep 1
done

if ! ss -tlnp | grep -q ":9222 "; then
    print_error "Chromium failed to start, debug port 9222 is not listening"
    exit 1
fi

print_success "Chromium started successfully, debug port 9222 is listening"

if pgrep -u browser -a chrome 2>/dev/null | grep -q -- "--load-extension=/home/browser/opencli-extension"; then
    print_success "OpenCLI extension is being loaded via --load-extension"
else
    print_warning "Could not confirm --load-extension from process list. Check /tmp/chrome-start.log and chrome://extensions"
fi

# ==============================================
# Step 6: Restart opencli daemon
# ==============================================
echo ""
echo "======================================"
echo "  Step 6: Restart opencli Daemon"
echo "======================================"

# Stop existing opencli daemon
print_info "Stopping existing opencli daemon..."
opencli daemon stop >/dev/null 2>&1 || true
sleep 2

# Start opencli daemon
print_info "Starting opencli daemon..."
opencli daemon start >/dev/null 2>&1 &

# Wait for daemon to start
print_info "Waiting for daemon to start (5s)..."
sleep 5

kill_chrome_processes() {    
    # 检查是否有 Chrome/Chromium 进程在运行
    if pgrep -x "chrome" > /dev/null 2>&1 || pgrep -x "google-chrome" > /dev/null 2>&1 || pgrep -x "chromium" > /dev/null 2>&1; then        
        # 第一步：尝试优雅终止（SIGTERM）
        pkill -TERM -x "chrome" 2>/dev/null || true
        pkill -TERM -x "google-chrome" 2>/dev/null || true
        pkill -TERM -x "chromium" 2>/dev/null || true
        # 等待进程优雅退出
        sleep 3
        # 第二步：强制杀死仍在运行的进程（SIGKILL）
        pkill -KILL -x "chrome" 2>/dev/null || true
        pkill -KILL -x "google-chrome" 2>/dev/null || true
        pkill -KILL -x "chromium" 2>/dev/null || true
    fi

    return 0
}

# kill_chrome_processes
# ==============================================
# Installation complete
# ==============================================
echo ""
echo "======================================"
echo "  Installation Complete!"
echo "======================================"
echo ""
echo "Verification results:"
echo "  OpenCLI version: $(opencli --version)"
echo "  Extension path: $EXTENSION_DIR"
echo "  Extension loading mode: --load-extension only"
echo "  Chromium debug port: 9222 (listening)"
echo ""
echo "Now you can use:"
echo "  1. browser-use tool to operate the browser"
echo "  2. opencli command to query platform data"
echo ""
echo "Common commands:"
echo "  opencli doctor - Check running status"
echo "  opencli bilibili hot - Bilibili trending"
echo "  opencli ctrip search hotel - Ctrip hotel search"
echo "  opencli list - View all supported sites"
echo ""