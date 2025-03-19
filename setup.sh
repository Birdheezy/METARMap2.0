#!/bin/bash
# ======================================================
# METARMap 2.0 Installation Script
# ======================================================
# This script guides you through the installation process
# of the METARMap Airport Weather Display system.
# ======================================================

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Check if script is run with sudo
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}╔════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  Error: Please run this script with sudo   ║${NC}"
    echo -e "${RED}║                                            ║${NC}"
    echo -e "${RED}║  Try running:                              ║${NC}"
    echo -e "${RED}║  ${YELLOW}sudo ./setup.sh            ${RED}║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════╝${NC}"
    exit 1
fi

# Function to print section headers
print_section_header() {
    local title="$1"
    echo ""
    echo -e "${BLUE}${BOLD}=== ${YELLOW}${title} ${BLUE}===${NC}"
    echo ""
}

# Function to update system
update_system() {
    print_section_header "System Update"
    echo -e "${CYAN}Updating package lists...${NC}"
    if apt update; then
        echo -e "${GREEN}✓ Package lists updated successfully${NC}"
        echo -e "${CYAN}Upgrading packages...${NC}"
        if apt upgrade -y; then
            echo -e "${GREEN}✓ System upgrade completed successfully${NC}"
            return 0
        else
            echo -e "${RED}✗ Error during system upgrade${NC}"
            return 1
        fi
    else
        echo -e "${RED}✗ Error updating package lists${NC}"
        return 1
    fi
}

# Function to create virtual environment
create_venv() {
    local venv_name=$1
    echo -e "${CYAN}Creating virtual environment: ${YELLOW}$venv_name${NC}"
    if python3 -m venv --system-site-packages "$venv_name"; then
        echo -e "${GREEN}✓ Virtual environment created successfully${NC}"
        return 0
    else
        echo -e "${RED}✗ Error creating virtual environment${NC}"
        return 1
    fi
}

# Function to print welcome banner
print_welcome_banner() {
    clear
    echo ""
    echo -e "${GREEN}  __  __ _____ _____  _    ____  __  __                ${NC}"
    echo -e "${GREEN} |  \/  | ____|_   _|/ \  |  _ \|  \/  | __ _ _ __     ${NC}"
    echo -e "${GREEN} | |\/| |  _|   | | / _ \ | |_) | |\/| |/ _\` | '_ \    ${NC}"
    echo -e "${GREEN} | |  | | |___  | |/ ___ \|  _ <| |  | | (_| | |_) |   ${NC}"
    echo -e "${GREEN} |_|  |_|_____| |_/_/   \_\_| \_\_|  |_|\__,_| .__/    ${NC}"
    echo -e "${GREEN}                                             |_|       ${NC}"
    echo ""
    echo -e "${YELLOW}           Airport Weather Map Installation            ${NC}"
    echo -e "${CYAN}                     Version 2.0                      ${NC}"
    echo ""
    echo -e "${CYAN}Welcome to METARMap setup${NC}"
    echo -e "${YELLOW}This script will guide you through the installation process.${NC}"
    echo -e "${YELLOW}You'll be asked a series of questions to customize your installation.${NC}"
    echo -e "${YELLOW}User CTRL+C to cancel at any time.${NC}"
}

# Main script
print_welcome_banner

read -e -p "$(echo -e "${CYAN}Would you like to update the system? [Y/n]: ${NC}")" UPDATE_CHOICE
UPDATE_CHOICE=${UPDATE_CHOICE:-y}  # Default to 'y' if empty
case ${UPDATE_CHOICE,,} in  # Convert to lowercase
    [Yy]*|"")
        update_system
        ;;
    [Nn]*)
        echo -e "${YELLOW}⚠ Skipping system update${NC}"
        ;;
    *)
        echo -e "${RED}✗ Invalid input${NC}"
        exit 1
        ;;
esac

# Virtual environment setup prompt
print_section_header "Virtual Environment Setup"
echo -e "${YELLOW}A virtual environment isolates Python packages for this project.${NC}"

read -e -p "$(echo -e "${CYAN}Would you like to set up a virtual environment? [Y/n]: ${NC}")" VENV_SETUP_CHOICE
VENV_SETUP_CHOICE=${VENV_SETUP_CHOICE:-y}
case ${VENV_SETUP_CHOICE,,} in
    [Yy]*|"")
        # Ask for virtual environment name
        read -p "$(echo -e "${CYAN}Enter virtual environment name (default: ${GREEN}metar${CYAN}): ${NC}")" VENV_NAME
        VENV_NAME=${VENV_NAME:-metar}

        # Validate venv name (only allow alphanumeric and underscores)
        if [[ ! $VENV_NAME =~ ^[a-zA-Z0-9_]+$ ]]; then
            echo -e "${RED}╔════════════════════════════════════════════════════╗${NC}"
            echo -e "${RED}║  Error: Invalid virtual environment name           ║${NC}"
            echo -e "${RED}║                                                    ║${NC}"
            echo -e "${RED}║  Use only letters, numbers, and underscores        ║${NC}"
            echo -e "${RED}╚════════════════════════════════════════════════════╝${NC}"
            exit 1
        fi

        create_venv "$VENV_NAME"
        ;;
    [Nn]*)
        echo -e "${YELLOW}⚠ Skipping virtual environment setup${NC}"
        ;;
    *)
        echo -e "${RED}✗ Invalid input${NC}"
        exit 1
        ;;
esac

# Function to install Python packages
install_packages() {
    local venv_name=$1
    local packages=(
        "adafruit-circuitpython-neopixel"
        "flask"
        "requests"
        "schedule"
    )

    print_section_header "Installing Python Packages"
    echo -e "${CYAN}Installing Python packages in ${YELLOW}${venv_name}${CYAN} environment...${NC}"
    
    # Activate virtual environment
    source "${venv_name}/bin/activate"
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Failed to activate virtual environment${NC}"
        return 1
    fi

    # Install each package
    for package in "${packages[@]}"; do
        echo -ne "${CYAN}Installing ${YELLOW}$package${CYAN}... ${NC}"
        if pip3 install "$package" > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${RED}✗ Failed${NC}"
            deactivate
            return 1
        fi
    done

    # Deactivate virtual environment
    deactivate
    echo -e "\n${GREEN}✓ All packages installed successfully${NC}"
    return 0
}

# Add package installation prompt
print_section_header "Python Package Installation"
echo -e "${YELLOW}The following packages are required for METARMap:${NC}"
echo -e "  ${CYAN}• adafruit-circuitpython-neopixel${NC} - LED control"
echo -e "  ${CYAN}• flask${NC} - web interface"
echo -e "  ${CYAN}• requests${NC} - API communication"
echo -e "  ${CYAN}• schedule${NC} - task automation"
echo ""

read -e -p "$(echo -e "${CYAN}Would you like to install the required packages? [Y/n]: ${NC}")" PACKAGES_CHOICE
PACKAGES_CHOICE=${PACKAGES_CHOICE:-y}
case ${PACKAGES_CHOICE,,} in
    [Yy]*|"")
        if [ -n "$VENV_NAME" ]; then
            install_packages "$VENV_NAME"
        else
            echo -e "${RED}✗ Virtual environment name not set${NC}"
        fi
        ;;
    [Nn]*)
        echo -e "${YELLOW}⚠ Skipping package installation${NC}"
        ;;
    *)
        echo -e "${RED}✗ Invalid input${NC}"
        ;;
esac

# Function to setup WiFi broadcasting
setup_wifi_broadcast() {
    print_section_header "WiFi Broadcasting Setup"
    echo -e "${YELLOW}This will configure your Raspberry Pi to create its own WiFi network${NC}"
    echo -e "${YELLOW}when no other WiFi networks are available.${NC}"
    echo ""
    
    # Present options for WiFi broadcasting
    echo -e "${CYAN}Choose a WiFi broadcasting solution:${NC}"
    echo -e "  ${MAGENTA}1)${NC} ${GREEN}AccessPopup${NC} (RaspberryConnect solution)"
    echo -e "  ${MAGENTA}2)${NC} ${GREEN}WiPi${NC} (METARMap's custom solution)"
    echo -e "  ${MAGENTA}3)${NC} ${YELLOW}Skip${NC} WiFi broadcasting setup"
    echo ""
    
    read -p "$(echo -e "${CYAN}Enter choice (1, 2, or 3): ${NC}")" WIFI_SOLUTION
    
    case $WIFI_SOLUTION in
        1)
            setup_accesspopup
            ;;
        2)
            setup_wipi
            ;;
        3)
            echo -e "${YELLOW}⚠ Skipping WiFi broadcast setup${NC}"
            return 0
            ;;
        *)
            echo -e "${RED}✗ Invalid choice${NC}"
            return 1
            ;;
    esac
}

# Function to setup AccessPopup (original solution)
setup_accesspopup() {
    echo -e "${CYAN}Setting up AccessPopup WiFi broadcasting...${NC}"
    echo -e "${YELLOW}You will need to:${NC}"
    echo -e "  ${MAGENTA}1.${NC} Select option ${GREEN}1${NC} to install"
    echo -e "  ${MAGENTA}2.${NC} Set SSID to: ${GREEN}METAR Pi${NC}"
    echo -e "  ${MAGENTA}3.${NC} Set Password to: ${GREEN}METAR-Pi-Password${NC}"
    echo -e "  ${MAGENTA}4.${NC} Set IP address to: ${GREEN}192.168.8.1${NC}"
    echo ""

    read -p "$(echo -e "${CYAN}Ready to proceed? (y/n): ${NC}")" PROCEED

    if [[ $PROCEED =~ ^[Yy]$ ]]; then
        # Download and extract
        echo -ne "${CYAN}Downloading WiFi broadcast package... ${NC}"
        if curl "https://www.raspberryconnect.com/images/scripts/AccessPopup.tar.gz" -o AccessPopup.tar.gz > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC}"
            
            echo -ne "${CYAN}Extracting package... ${NC}"
            tar -xf ./AccessPopup.tar.gz > /dev/null 2>&1
            echo -e "${GREEN}✓${NC}"
            
            cd AccessPopup

            echo -e "\n${GREEN}Starting interactive installer...${NC}"
            echo -e "${YELLOW}After completion, this script will resume.${NC}"
            echo ""

            # Launch interactive installer
            sudo ./installconfig.sh

            # Return to original directory
            cd ..

            # Cleanup
            echo -ne "${CYAN}Cleaning up temporary files... ${NC}"
            rm -rf AccessPopup.tar.gz > /dev/null 2>&1
            echo -e "${GREEN}✓${NC}"

            echo -e "\n${GREEN}✓ AccessPopup WiFi broadcast setup completed${NC}"
            return 0
        else
            echo -e "${RED}✗ Failed to download WiFi broadcast package${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠ Skipping AccessPopup setup${NC}"
        return 0
    fi
}

# Function to setup WiPi (METARMap's custom solution)
setup_wipi() {
    echo -e "${CYAN}Setting up WiPi Auto WiFi Broadcasting...${NC}"
    echo -e "${YELLOW}This is METARMap's custom WiFi broadcasting solution that:${NC}"
    echo -e "  ${CYAN}• Automatically creates an access point when no WiFi is available${NC}"
    echo -e "  ${CYAN}• Seamlessly switches between client and AP modes${NC}"
    echo -e "  ${CYAN}• Provides easy configuration and management${NC}"
    echo ""

    # Check if metar venv exists
    if [ ! -d "/home/pi/metar" ]; then
        echo -e "${RED}Error: The 'metar' virtual environment does not exist.${NC}"
        echo -e "${YELLOW}Please ensure you've set up the virtual environment earlier in the script.${NC}"
        return 1
    fi

    # Install required packages in metar venv directly
    echo -e "${CYAN}Installing required Python packages in metar virtual environment...${NC}"
    source /home/pi/metar/bin/activate
    pip install setuptools wheel
    deactivate
    
    # Create temporary directory
    local TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"

    # Clone WiPi repository
    echo -ne "${CYAN}Downloading WiPi... ${NC}"
    if git clone https://github.com/Birdheezy/WiPi-Auto-Wifi-Broadcasting.git > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        
        cd WiPi-Auto-Wifi-Broadcasting
        
        # Create a completely new installer script that skips the problematic parts
        echo -ne "${CYAN}Creating custom installer for WiPi... ${NC}"
        
        cat > custom_install.sh << 'EOF'
#!/bin/bash

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Function to print section headers
print_section_header() {
    local title="$1"
    echo ""
    echo -e "${BLUE}${BOLD}=== ${YELLOW}${title} ${BLUE}===${NC}"
    echo ""
}

# Function to print status messages
print_status() {
    echo -e "${CYAN}$1${NC}"
}

# Function to print success messages
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print error messages
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to print warning messages
print_warning() {
    echo -e "${YELLOW}! $1${NC}"
}

# Function to check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "This script must be run as root"
        echo -e "Please run with: ${BOLD}sudo bash $0${NC}"
        exit 1
    fi
}

# Function to check if NetworkManager is installed
check_network_manager() {
    if ! command -v nmcli &> /dev/null; then
        print_error "NetworkManager is not installed"
        print_status "WiPi requires NetworkManager to function properly"
        
        read -p "Would you like to install NetworkManager now? [Y/n] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
            print_status "Installing NetworkManager..."
            apt-get update
            apt-get install -y network-manager
            
            if [ $? -eq 0 ]; then
                print_success "NetworkManager installed successfully"
            else
                print_error "Failed to install NetworkManager"
                exit 1
            fi
        else
            print_warning "NetworkManager is required for WiPi to function"
            print_warning "Installation aborted"
            exit 1
        fi
    else
        print_success "NetworkManager is installed"
    fi
}

# Function to install WiPi files
install_wipi_files() {
    print_status "Installing WiPi files..."
    
    # Create directory structure
    mkdir -p /home/pi/wipi
    
    # Get the directory of the install script
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
    
    # Copy files
    cp "$SCRIPT_DIR/wipi.py" /home/pi/wipi/wipi.py
    cp "$SCRIPT_DIR/wipi_service.py" /home/pi/wipi/wipi_service.py
    
    # Make executable
    chmod +x /home/pi/wipi/wipi.py
    chmod +x /home/pi/wipi/wipi_service.py
    
    # Copy config file if it doesn't exist
    if [ ! -f /home/pi/wipi/config.json ]; then
        cp "$SCRIPT_DIR/config.json" /home/pi/wipi/config.json
    else
        print_warning "Config file already exists at /home/pi/wipi/config.json"
        print_warning "Your existing configuration will not be modified"
    fi
    
    # Set ownership
    chown -R pi:pi /home/pi/wipi
    
    print_success "WiPi files installed successfully"
}

# Function to configure WiPi
configure_wipi() {
    print_section_header "WiPi Configuration"
    
    # Ask for AP SSID
    read -p "Enter the Access Point SSID [METAR-Pi]: " ap_ssid
    ap_ssid=${ap_ssid:-METAR-Pi}
    
    # Ask for AP password
    read -p "Enter the Access Point password [METAR-Pi]: " ap_password
    ap_password=${ap_password:-METAR-Pi}
    
    # Ask for AP IP address
    read -p "Enter the Access Point IP address [192.168.8.1]: " ap_ip
    ap_ip=${ap_ip:-192.168.8.1}
    
    # Ask for check interval (shorter for faster response)
    read -p "Enter the check interval in seconds [30]: " check_interval
    check_interval=${check_interval:-30}
    
    # Update config file
    cat > /home/pi/wipi/config.json << EOL
{
    "ap_ssid": "$ap_ssid",
    "ap_password": "$ap_password",
    "ap_ip_address": "$ap_ip",
    "check_interval": $check_interval,
    "force_ap_mode": false,
    "debug_mode": true,
    "ap_channel": 1,
    "ap_band": "bg",
    "ap_hidden": false,
    "reconnect_attempts": 3,
    "reconnect_delay": 5,
    "preferred_networks": [],
    "ap_open": false
}
EOL
    
    print_success "WiPi configured successfully"
}

# Function to install systemd service
install_service() {
    print_status "Installing WiPi service..."
    
    # Create a systemd service file that uses the metar venv python
    cat > /etc/systemd/system/wipi.service << EOL
[Unit]
Description=WiPi Auto WiFi Broadcasting
After=network.target NetworkManager.service
Wants=NetworkManager.service

[Service]
Type=simple
WorkingDirectory=/home/pi/wipi
ExecStart=/home/pi/metar/bin/python3 /home/pi/wipi/wipi_service.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOL

    # Reload systemd and enable the service
    systemctl daemon-reload
    systemctl enable wipi.service
    systemctl start wipi.service
    
    if [ $? -eq 0 ]; then
        print_success "WiPi service installed successfully"
    else
        print_error "Failed to install WiPi service"
        exit 1
    fi
}

# Function to create aliases
create_aliases() {
    local ALIASES="alias blank='sudo /home/pi/metar/bin/python3 blank.py'
alias metar='sudo /home/pi/metar/bin/python3 '
alias startmetar='sudo systemctl start metar.service'
alias startscheduler='sudo systemctl start scheduler.service'
alias startsettings='sudo systemctl start settings.service'
alias stopmetar='sudo systemctl stop metar.service'
alias stopsettings='sudo systemctl stop settings.service'
alias stopscheduler='sudo systemctl stop scheduler.service'
alias restartmetar='sudo systemctl restart metar.service'
alias restartsettings='sudo systemctl restart settings.service'
alias restartscheduler='sudo systemctl restart scheduler.service'
alias metarstatus='sudo systemctl status metar.service'
alias settingsstatus='sudo systemctl status settings.service'
alias schedulerstatus='sudo systemctl status scheduler.service'

# WiPi commands
alias wipi-status='sudo systemctl status wipi.service'
alias wipi-start='sudo systemctl start wipi.service'
alias wipi-stop='sudo systemctl stop wipi.service'
alias wipi-restart='sudo systemctl restart wipi.service'
alias wipi-log='sudo journalctl -u wipi.service'
alias wipi-config='sudo nano /home/pi/wipi/config.json'
alias wipi='sudo /home/pi/metar/bin/python3 /home/pi/wipi/wipi.py'
alias wipi-edit='cd /home/pi/wipi && sudo ls -la'
alias wipi-uninstall='sudo systemctl stop wipi.service && sudo systemctl disable wipi.service && sudo rm -rf /home/pi/wipi /etc/systemd/system/wipi.service /etc/profile.d/wipi-aliases.sh && echo -e "\033[0;32m✓ WiPi has been uninstalled\033[0m'"

    echo -ne "${CYAN}Installing command aliases... ${NC}"
    # Write aliases to the pi user's .bash_aliases file
    echo "$ALIASES" | sudo -u pi tee /home/pi/.bash_aliases > /dev/null

    echo -e "${GREEN}✓${NC}"
    echo -e "${YELLOW}To use the aliases in your current session, run:${NC}"
    echo -e "    ${CYAN}source /home/pi/.bash_aliases${NC}"
    echo -e "${YELLOW}Or log out and log back in for aliases to take effect automatically.${NC}"
    return 0
}

# Function to display completion message
display_completion() {
    print_section_header "Installation Complete"
    
    echo -e "${GREEN}WiPi has been successfully installed!${NC}"
    echo ""
    echo -e "Access Point SSID: ${BOLD}${YELLOW}$ap_ssid${NC}"
    echo -e "Access Point Password: ${BOLD}${YELLOW}$ap_password${NC}"
    echo -e "Access Point IP: ${BOLD}${YELLOW}$ap_ip${NC}"
    echo -e "Check Interval: ${BOLD}${YELLOW}$check_interval seconds${NC}"
    echo ""
    echo -e "${CYAN}Available commands:${NC}"
    echo -e "  ${BOLD}wipi-status${NC} - Check service status"
    echo -e "  ${BOLD}wipi-start${NC} - Start the service"
    echo -e "  ${BOLD}wipi-stop${NC} - Stop the service"
    echo -e "  ${BOLD}wipi-restart${NC} - Restart the service"
    echo -e "  ${BOLD}wipi-log${NC} - View service logs"
    echo -e "  ${BOLD}wipi-config${NC} - Edit configuration"
    echo -e "  ${BOLD}wipi-uninstall${NC} - Completely remove WiPi"
    echo ""
    echo -e "${YELLOW}Note:${NC} When the Raspberry Pi cannot connect to a known WiFi network,"
    echo -e "it will automatically create an access point with the configured settings."
    echo -e "You can then connect to this access point to access your Pi."
    echo ""
    echo -e "To manually force AP mode: ${BOLD}sudo /home/pi/metar/bin/python3 /home/pi/wipi/wipi.py --force-ap${NC}"
    echo -e "To check current status: ${BOLD}sudo /home/pi/metar/bin/python3 /home/pi/wipi/wipi.py --status${NC}"
    echo ""
    echo -e "All WiPi files are located in: ${BOLD}/home/pi/wipi/${NC}"
    echo -e "You can edit these files directly to customize WiPi."
    echo ""
    echo -e "To uninstall WiPi, run: ${BOLD}wipi-uninstall${NC}"
    echo ""
}

# Main installation
print_section_header "WiPi - Auto WiFi Broadcasting Installation"

# Check if running as root
check_root

# Check for NetworkManager
check_network_manager

# Skip Python package installation (already done in metar venv)
print_success "Using existing metar virtual environment for Python packages"

# Install WiPi files
install_wipi_files

# Configure WiPi
configure_wipi

# Install systemd service
install_service

# Create command aliases
create_aliases

# Display completion message
display_completion
EOF
        chmod +x custom_install.sh
        echo -e "${GREEN}✓${NC}"
        
        echo -e "\n${GREEN}Starting WiPi installer with 'metar' virtual environment...${NC}"
        echo -e "${YELLOW}You will be prompted to configure your access point settings.${NC}"
        echo -e "${YELLOW}Recommended settings:${NC}"
        echo -e "  ${CYAN}• SSID: ${GREEN}METAR-Pi${NC}"
        echo -e "  ${CYAN}• Password: ${GREEN}METAR-Pi${NC}"
        echo -e "  ${CYAN}• IP Address: ${GREEN}192.168.8.1${NC}"
        echo -e "  ${CYAN}• Check Interval: ${GREEN}30${NC} (seconds)"
        echo ""
        
        # Run the custom installer
        sudo bash custom_install.sh
        
        # Return to original directory
        cd /home/pi
        
        # Cleanup
        echo -ne "${CYAN}Cleaning up temporary files... ${NC}"
        rm -rf "$TEMP_DIR"
        echo -e "${GREEN}✓${NC}"
        
        echo -e "\n${GREEN}✓ WiPi Auto WiFi Broadcasting setup completed using 'metar' virtual environment${NC}"
        echo -e "${YELLOW}To use WiPi commands, run:${NC}"
        echo -e "  ${CYAN}• Check status: ${GREEN}sudo /home/pi/metar/bin/python3 /home/pi/wipi/wipi.py --status${NC}"
        echo -e "  ${CYAN}• Force AP mode: ${GREEN}sudo /home/pi/metar/bin/python3 /home/pi/wipi/wipi.py --force-ap${NC}"
        echo -e "  ${CYAN}• Edit files: ${GREEN}wipi-edit${NC}"
        echo -e "  ${CYAN}• Or use the aliases after reboot: ${GREEN}wipi --status${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed to download WiPi${NC}"
        cd /home/pi
        rm -rf "$TEMP_DIR"
        return 1
    fi
}

# Add to main script after package installation:
print_section_header "WiFi Broadcasting Setup"
echo -e "${YELLOW}This feature allows your METARMap to create its own WiFi network${NC}"
echo -e "${YELLOW}when no other networks are available, making it easier to configure.${NC}"
echo ""

read -e -p "$(echo -e "${CYAN}Would you like to set up WiFi Broadcasting? [Y/n]: ${NC}")" WIFI_CHOICE
WIFI_CHOICE=${WIFI_CHOICE:-y}
case ${WIFI_CHOICE,,} in
    [Yy]*|"")
        setup_wifi_broadcast
        ;;
    [Nn]*)
        echo -e "${YELLOW}⚠ Skipping WiFi broadcast setup${NC}"
        ;;
    *)
        echo -e "${RED}✗ Invalid input${NC}"
        ;;
esac

# Function to install a service
install_service() {
    local service_name=$1
    local service_content=$2

    echo -ne "${CYAN}Creating ${service_name}... ${NC}"
    echo "$service_content" | sudo tee "/etc/systemd/system/${service_name}" > /dev/null

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC}"
        echo -ne "${CYAN}Enabling ${service_name}... ${NC}"
        sudo systemctl daemon-reload > /dev/null 2>&1
        sudo systemctl enable "${service_name}" > /dev/null 2>&1
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed${NC}"
        return 1
    fi
}

# Service definitions
METAR_SERVICE="[Unit]
Description=Run Metar Service
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/pi
ExecStart=/home/pi/metar/bin/python3 /home/pi/metar.py
Restart=always
User=root
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target"

SETTINGS_SERVICE="[Unit]
Description=Run Flask App for Settings
After=network.target

[Service]
WorkingDirectory=/home/pi/
ExecStart=sudo /home/pi/metar/bin/python3 /home/pi/settings.py
Restart=on-failure
User=pi
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target"

SCHEDULER_SERVICE="[Unit]
Description=Scheduler Service
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/pi
ExecStart=sudo /home/pi/metar/bin/python3 /home/pi/scheduler.py
Restart=always
User=pi
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target"

# Function to create service file
create_service_file() {
    local service_name=$1
    local service_content=$2
    local service_path="/etc/systemd/system/${service_name}"

    echo -ne "${CYAN}Creating ${service_name}... ${NC}"
    echo "$service_content" > "$service_path"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed${NC}"
        return 1
    fi
}

# Function to enable services
enable_services() {
    echo -ne "${CYAN}Reloading systemd daemon... ${NC}"
    if sudo systemctl daemon-reload > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"

        local services=("metar.service" "settings.service" "scheduler.service")
        for service in "${services[@]}"; do
            echo -ne "${CYAN}Enabling ${service}... ${NC}"
            if sudo systemctl enable "$service" > /dev/null 2>&1; then
                echo -e "${GREEN}✓${NC}"
            else
                echo -e "${RED}✗ Failed${NC}"
            fi
        done
    else
        echo -e "${RED}✗ Failed${NC}"
        return 1
    fi
}

# Add to main script:
print_section_header "Service Installation"
echo -e "${YELLOW}This will install the following services:${NC}"
echo -e "  ${CYAN}• METAR service${NC} - Controls the LED display"
echo -e "  ${CYAN}• Settings service${NC} - Provides the web interface"
echo -e "  ${CYAN}• Scheduler service${NC} - Handles automated tasks"
echo ""

read -e -p "$(echo -e "${CYAN}Would you like to install all services? [Y/n]: ${NC}")" SERVICES_CHOICE
SERVICES_CHOICE=${SERVICES_CHOICE:-y}
case ${SERVICES_CHOICE,,} in
    [Yy]*|"")
        # Create service files
        create_service_file "metar.service" "$METAR_SERVICE"
        create_service_file "settings.service" "$SETTINGS_SERVICE"
        create_service_file "scheduler.service" "$SCHEDULER_SERVICE"

        # Enable required services
        enable_services

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ All services installed and enabled successfully${NC}"
        else
            echo -e "${RED}✗ Error installing services${NC}"
        fi
        ;;
    [Nn]*)
        echo -e "${YELLOW}⚠ Skipping service installation and enabling${NC}"
        ;;
    *)
        echo -e "${RED}✗ Invalid input${NC}"
        ;;
esac

# Add Command Aliases Setup right after Service Installation
print_section_header "Command Aliases Setup"
echo -e "${YELLOW}Command aliases make it easier to control your METARMap${NC}"
echo -e "${YELLOW}by providing simple commands like:${NC}"
echo -e "  ${CYAN}• startmetar${NC} - Start the LED display"
echo -e "  ${CYAN}• stopmetar${NC} - Stop the LED display"
echo -e "  ${CYAN}• blank${NC} - Turn off all LEDs"
echo ""

read -e -p "$(echo -e "${CYAN}Would you like to install command aliases? [Y/n]: ${NC}")" ALIAS_CHOICE
ALIAS_CHOICE=${ALIAS_CHOICE:-y}
case ${ALIAS_CHOICE,,} in
    [Yy]*|"")
        setup_aliases
        ;;
    [Nn]*)
        echo -e "${YELLOW}⚠ Skipping alias setup${NC}"
        ;;
    *)
        echo -e "${RED}✗ Invalid input${NC}"
        ;;
esac

# Function to setup SSL certificate
setup_ssl() {
    print_section_header "SSL Certificate Setup"
    echo -e "${YELLOW}You will be prompted to enter certificate information.${NC}"
    echo -e "${CYAN}Important: When asked for 'Common Name', enter your Pi's local IP address${NC}"
    echo -e "${CYAN}For other fields, you can press '.' to leave them blank${NC}"
    echo -e "Press ${GREEN}Enter${NC} when ready..."
    read

    # Generate SSL certificate
    echo -e "${CYAN}Generating SSL certificate...${NC}"
    if ! sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/ssl/private/flask-selfsigned.key \
        -out /etc/ssl/certs/flask-selfsigned.crt; then
        echo -e "${RED}✗ Failed to generate SSL certificate${NC}"
        return 1
    fi

    # Update config.py to enable HTTPS
    local CONFIG_FILE="/home/pi/config.py"
    if [ -f "$CONFIG_FILE" ]; then
        echo -ne "${CYAN}Updating config.py to enable HTTPS... ${NC}"

        # Create backup
        sudo cp "$CONFIG_FILE" "${CONFIG_FILE}.bak"

        # Replace ENABLE_HTTPS value or add it if it doesn't exist
        if grep -q "ENABLE_HTTPS" "$CONFIG_FILE"; then
            sudo sed -i 's/ENABLE_HTTPS *= *False/ENABLE_HTTPS = True/' "$CONFIG_FILE"
            sudo sed -i 's/ENABLE_HTTPS *= *True/ENABLE_HTTPS = True/' "$CONFIG_FILE"
        else
            echo "ENABLE_HTTPS = True" | sudo tee -a "$CONFIG_FILE" > /dev/null
        fi

        # Verify the change
        if grep -q "ENABLE_HTTPS = True" "$CONFIG_FILE"; then
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${RED}⚠ Warning: Failed to update ENABLE_HTTPS in config.py${NC}"
        fi
    else
        echo -e "${RED}✗ Error: config.py not found at $CONFIG_FILE${NC}"
        return 1
    fi

    return 0
}

# Function to disable HTTPS in config
disable_https() {
    local CONFIG_FILE="/home/pi/config.py"
    if [ -f "$CONFIG_FILE" ]; then
        echo -ne "${CYAN}Updating config.py to disable HTTPS... ${NC}"

        # Create backup
        sudo cp "$CONFIG_FILE" "${CONFIG_FILE}.bak"

        # Replace ENABLE_HTTPS value or add it if it doesn't exist
        if grep -q "ENABLE_HTTPS" "$CONFIG_FILE"; then
            sudo sed -i 's/ENABLE_HTTPS *= *True/ENABLE_HTTPS = False/' "$CONFIG_FILE"
            sudo sed -i 's/ENABLE_HTTPS *= *False/ENABLE_HTTPS = False/' "$CONFIG_FILE"
        else
            echo "ENABLE_HTTPS = False" | sudo tee -a "$CONFIG_FILE" > /dev/null
        fi

        # Verify the change
        if grep -q "ENABLE_HTTPS = False" "$CONFIG_FILE"; then
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${RED}⚠ Warning: Failed to update ENABLE_HTTPS in config.py${NC}"
        fi
    else
        echo -e "${RED}✗ Error: config.py not found at $CONFIG_FILE${NC}"
        return 1
    fi
}

# Add SSL setup prompt
print_section_header "SSL Certificate Setup"
echo -e "${YELLOW}Setting up HTTPS will:${NC}"
echo -e "  ${CYAN}1. Generate a self-signed SSL certificate${NC}"
echo -e "  ${CYAN}2. Enable HTTPS in config.py${NC}"
echo -e "  ${CYAN}3. Configure the web interface to use HTTPS (port 443)${NC}"
echo ""

read -e -p "$(echo -e "${CYAN}Would you like to setup HTTPS with a self-signed certificate? [N/y]: ${NC}")" SSL_CHOICE
SSL_CHOICE=${SSL_CHOICE:-n}
case ${SSL_CHOICE,,} in
    [Yy]*)
        setup_ssl
        ;;
    [Nn]*|"")
        echo -e "${CYAN}Disabling HTTPS...${NC}"
        disable_https
        echo -e "${GREEN}✓ HTTPS disabled${NC}"
        ;;
    *)
        echo -e "${RED}✗ Invalid input${NC}"
        ;;
esac

# Function to setup aliases
setup_aliases() {
    local ALIASES="alias blank='sudo /home/pi/metar/bin/python3 blank.py'
alias metar='sudo /home/pi/metar/bin/python3 '
alias startmetar='sudo systemctl start metar.service'
alias startscheduler='sudo systemctl start scheduler.service'
alias startsettings='sudo systemctl start settings.service'
alias stopmetar='sudo systemctl stop metar.service'
alias stopsettings='sudo systemctl stop settings.service'
alias stopscheduler='sudo systemctl stop scheduler.service'
alias restartmetar='sudo systemctl restart metar.service'
alias restartsettings='sudo systemctl restart settings.service'
alias restartscheduler='sudo systemctl restart scheduler.service'
alias metarstatus='sudo systemctl status metar.service'
alias settingsstatus='sudo systemctl status settings.service'
alias schedulerstatus='sudo systemctl status scheduler.service'

# WiPi commands
alias wipi-status='sudo systemctl status wipi.service'
alias wipi-start='sudo systemctl start wipi.service'
alias wipi-stop='sudo systemctl stop wipi.service'
alias wipi-restart='sudo systemctl restart wipi.service'
alias wipi-log='sudo journalctl -u wipi.service'
alias wipi-config='sudo nano /home/pi/wipi/config.json'
alias wipi='sudo /home/pi/metar/bin/python3 /home/pi/wipi/wipi.py'
alias wipi-edit='cd /home/pi/wipi && sudo ls -la'
alias wipi-uninstall='sudo systemctl stop wipi.service && sudo systemctl disable wipi.service && sudo rm -rf /home/pi/wipi /etc/systemd/system/wipi.service /etc/profile.d/wipi-aliases.sh && echo -e "\033[0;32m✓ WiPi has been uninstalled\033[0m"'

    echo -ne "${CYAN}Installing command aliases... ${NC}"
    # Write aliases to the pi user's .bash_aliases file
    echo "$ALIASES" | sudo -u pi tee /home/pi/.bash_aliases > /dev/null

    echo -e "${GREEN}✓${NC}"
    echo -e "${YELLOW}To use the aliases in your current session, run:${NC}"
    echo -e "    ${CYAN}source /home/pi/.bash_aliases${NC}"
    echo -e "${YELLOW}Or log out and log back in for aliases to take effect automatically.${NC}"
    return 0
}

# Function to install Tailscale
install_tailscale() {
    print_section_header "Tailscale Installation"
    echo -e "${YELLOW}Tailscale provides secure remote access to your METARMap${NC}"
    echo -e "${YELLOW}from anywhere in the world.${NC}"
    echo ""

    # Install https transport
    echo -ne "${CYAN}Installing HTTPS transport... ${NC}"
    if sudo apt-get install -y apt-transport-https > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗ Failed${NC}"
        return 1
    fi

    # Add Tailscale GPG key
    echo -ne "${CYAN}Adding Tailscale GPG key... ${NC}"
    if curl -fsSL https://pkgs.tailscale.com/stable/debian/bookworm.noarmor.gpg | sudo tee /usr/share/keyrings/tailscale-archive-keyring.gpg > /dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗ Failed${NC}"
        return 1
    fi

    # Add Tailscale repository
    echo -ne "${CYAN}Adding Tailscale repository... ${NC}"
    if curl -fsSL https://pkgs.tailscale.com/stable/debian/bookworm.tailscale-keyring.list | sudo tee /etc/apt/sources.list.d/tailscale.list > /dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗ Failed${NC}"
        return 1
    fi

    # Update package lists
    echo -ne "${CYAN}Updating package lists... ${NC}"
    if sudo apt update > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗ Failed${NC}"
        return 1
    fi

    # Install Tailscale
    echo -ne "${CYAN}Installing Tailscale... ${NC}"
    if sudo apt install tailscale -y > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗ Failed${NC}"
        return 1
    fi

    # Enable auto-updates
    echo -ne "${CYAN}Enabling auto-updates... ${NC}"
    if sudo tailscale set --auto-update > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗ Failed${NC}"
        return 1
    fi

    # Start Tailscale
    echo -e "\n${GREEN}Starting Tailscale...${NC}"
    echo -e "${YELLOW}A URL will be displayed. Copy and paste it into your web browser to complete setup.${NC}"
    echo -e "Press ${GREEN}Enter${NC} when ready..."
    read

    if ! sudo tailscale up --ssh; then
        echo -e "${RED}✗ Failed to start Tailscale${NC}"
        return 1
    fi

    echo -e "\n${GREEN}✓ Tailscale installation completed${NC}"
    echo -e "${YELLOW}Please make sure to disable key expiry in the Tailscale admin console${NC}"
    return 0
}

# Add Tailscale installation prompt
print_section_header "Tailscale Remote Access"
echo -e "${YELLOW}Tailscale provides secure remote access to your METARMap${NC}"
echo -e "${YELLOW}from anywhere in the world, without port forwarding.${NC}"
echo ""

read -e -p "$(echo -e "${CYAN}Would you like to install Tailscale? [N/y]: ${NC}")" TAILSCALE_CHOICE
TAILSCALE_CHOICE=${TAILSCALE_CHOICE:-n}
case ${TAILSCALE_CHOICE,,} in
    [Yy]*)
        install_tailscale
        ;;
    [Nn]*|"")
        echo -e "${YELLOW}⚠ Skipping Tailscale installation${NC}"
        ;;
    *)
        echo -e "${RED}✗ Invalid input${NC}"
        ;;
esac

setup_git() {
    print_section_header "Git Repository Setup"
    echo -e "${YELLOW}This will download all the necessary files for METARMap${NC}"
    echo ""

    # Install Git
    echo -ne "${CYAN}Installing Git... ${NC}"
    if sudo apt install git -y > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗ Failed${NC}"
        return 1
    fi

    cd /home/pi || return 1

    # Let user choose branch
    echo -e "\n${CYAN}Choose which branch to install:${NC}"
    echo -e "  ${MAGENTA}1)${NC} ${GREEN}main${NC} (beta/development branch)"
    echo -e "  ${MAGENTA}2)${NC} ${GREEN}production${NC} (stable branch)"
    
    read -p "$(echo -e "${CYAN}Enter choice (1 or 2): ${NC}")" BRANCH_CHOICE

    case $BRANCH_CHOICE in
        1) BRANCH="main" ;;
        2) BRANCH="production" ;;
        *)
            echo -e "${RED}✗ Invalid choice${NC}"
            return 1
            ;;
    esac

    # Initialize git repo
    echo -ne "${CYAN}Initializing Git repository with ${YELLOW}$BRANCH${CYAN} branch... ${NC}"
    if git init -b "$BRANCH" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗ Failed${NC}"
        return 1
    fi

    # Add remote origin
    echo -ne "${CYAN}Adding remote repository... ${NC}"
    if git remote add origin https://github.com/Birdheezy/METARMap2.0 > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗ Failed${NC}"
        return 1
    fi

    # Fetch branches
    echo -ne "${CYAN}Fetching repository branches... ${NC}"
    if git fetch origin > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗ Failed${NC}"
        return 1
    fi

    # Checkout selected branch with force
    echo -ne "${CYAN}Setting up ${YELLOW}$BRANCH${CYAN} branch... ${NC}"
    if git checkout -f -b "$BRANCH" "origin/$BRANCH" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗ Failed${NC}"
        return 1
    fi

    # Pull latest changes with force
    echo -ne "${CYAN}Pulling latest changes... ${NC}"
    if git pull -f origin "$BRANCH" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗ Failed${NC}"
        return 1
    fi

    # Set ownership
    echo -ne "${CYAN}Setting file ownership... ${NC}"
    sudo chown -R pi:pi /home/pi > /dev/null 2>&1
    echo -e "${GREEN}✓${NC}"

    echo -e "\n${GREEN}✓ Git repository setup completed successfully${NC}"
    echo -e "Installed branch: ${GREEN}$BRANCH${NC}"
    return 0
}

# Add Git installation prompt
print_section_header "Software Installation"
echo -e "${YELLOW}This step will download all the necessary files for METARMap${NC}"
echo -e "${YELLOW}from the GitHub repository.${NC}"
echo ""

read -e -p "$(echo -e "${CYAN}Would you like to install Git and clone the required files? [Y/n]: ${NC}")" GIT_CHOICE
GIT_CHOICE=${GIT_CHOICE:-y}
case ${GIT_CHOICE,,} in
    [Yy]*|"")
        # Modify setup_git function to default to production branch
        BRANCH="production"  # Set default branch
        setup_git
        ;;
    [Nn]*)
        echo -e "${YELLOW}⚠ Skipping Git installation${NC}"
        ;;
    *)
        echo -e "${RED}✗ Invalid input${NC}"
        ;;
esac

# Add reboot prompt at the end
print_section_header "Setup Complete"
echo -e "${GREEN}✓ METARMap installation has been completed successfully!${NC}"
echo -e "${YELLOW}A system reboot is recommended to apply all changes.${NC}"
echo ""

read -e -p "$(echo -e "${CYAN}Would you like to reboot now? [Y/n]: ${NC}")" REBOOT_CHOICE
REBOOT_CHOICE=${REBOOT_CHOICE:-y}
case ${REBOOT_CHOICE,,} in
    [Yy]*|"")
        echo -e "${CYAN}Rebooting system...${NC}"
        sudo reboot
        ;;
    [Nn]*)
        echo -e "${YELLOW}Please remember to reboot your system to apply all changes${NC}"
        ;;
    *)
        echo -e "${RED}✗ Invalid input. Please reboot manually when ready${NC}"
        ;;
esac