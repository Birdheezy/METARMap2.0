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
        if apt-get -o Dpkg::Options::="--force-confold" upgrade -y; then
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

# Function to setup Git repository
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
    echo -e "  ${MAGENTA}1)${NC} ${GREEN}production${NC} (stable branch)"
    echo -e "  ${MAGENTA}2)${NC} ${GREEN}main${NC} (beta/development branch)"

    read -p "$(echo -e "${CYAN}Enter choice (1 or 2): ${NC}")" BRANCH_CHOICE

    case $BRANCH_CHOICE in
        1|"") BRANCH="production" ;;
        2) BRANCH="main" ;;
        *)
            echo -e "${RED}✗ Invalid choice${NC}"
            return 1
            ;;
    esac

    # Remove any existing git repository
    if [ -d ".git" ]; then
        echo -ne "${CYAN}Removing existing git repository... ${NC}"
        rm -rf .git > /dev/null 2>&1
        echo -e "${GREEN}✓${NC}"
    fi

    # Clone the repository with the selected branch
    echo -ne "${CYAN}Cloning repository with ${YELLOW}$BRANCH${CYAN} branch... ${NC}"
    if git clone -b "$BRANCH" https://github.com/Birdheezy/METARMap2.0.git temp_repo > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗ Failed to clone repository${NC}"
        return 1
    fi

    # Move all files from temp directory to /home/pi
    echo -ne "${CYAN}Moving files to /home/pi... ${NC}"
    if cp -r temp_repo/* . > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗ Failed to move files${NC}"
        rm -rf temp_repo
        return 1
    fi

    # Copy hidden files (like .git)
    echo -ne "${CYAN}Copying hidden files... ${NC}"
    if cp -r temp_repo/.* . > /dev/null 2>&1 2>/dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${YELLOW}⚠ Some hidden files may not have been copied${NC}"
    fi

    # Clean up temporary directory
    echo -ne "${CYAN}Cleaning up... ${NC}"
    rm -rf temp_repo > /dev/null 2>&1
        echo -e "${GREEN}✓${NC}"

    # Set ownership
    echo -ne "${CYAN}Setting file ownership... ${NC}"
    sudo chown -R pi:pi /home/pi > /dev/null 2>&1
    echo -e "${GREEN}✓${NC}"

    # Add /home/pi to Git's safe.directory for the root user (as services run as root)
    echo -ne "${CYAN}Configuring Git safe directory for root... ${NC}"
    git config --global --add safe.directory /home/pi > /dev/null 2>&1
    echo -e "${GREEN}✓${NC}"

    echo -e "\n${GREEN}✓ Git repository setup completed successfully${NC}"
    echo -e "Installed branch: ${GREEN}$BRANCH${NC}"
    return 0
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

# Function to install Python packages
install_packages() {
    local venv_name=$1
    echo -e "${CYAN}Installing Python packages in ${YELLOW}${venv_name}${CYAN} environment...${NC}"
    
    # Activate virtual environment
    source "${venv_name}/bin/activate"
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Failed to activate virtual environment${NC}"
        return 1
    fi

    # Install required Python packages (minimal, explicit)
    echo -e "${CYAN}Installing required Python libraries...${NC}"
    if pip install --no-cache-dir \
        adafruit-blinka \
        rpi_ws281x \
        adafruit-circuitpython-neopixel \
        RPi.GPIO \
        flask \
        requests \
        pytz \
        astral \
        schedule; then

        # Deactivate virtual environment
        deactivate
        echo -e "\n${GREEN}✓ All packages installed successfully${NC}"
        return 0
    else
        deactivate
        echo -e "${RED}✗ Failed to install Python packages${NC}"
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

# Function for express install
express_install() {
    echo -e "${GREEN}Starting Express Install...${NC}"
    echo -e "${YELLOW}This will install METARMap with recommended defaults.${NC}"
    echo ""
    
    # Set defaults for express install
    VENV_NAME="metar"
    BRANCH="production"
    
    # System update
    echo -e "${CYAN}Updating system...${NC}"
    update_system
    
    # Virtual environment
    echo -e "${CYAN}Creating virtual environment...${NC}"
    create_venv "$VENV_NAME"
    
    # Git setup
    echo -e "${CYAN}Setting up Git repository...${NC}"
    setup_git
    
    # Package installation
    echo -e "${CYAN}Installing Python packages...${NC}"
    install_packages "$VENV_NAME"
    
    # Skip WiFi broadcasting for express install
    echo -e "${YELLOW}Skipping WiFi broadcasting setup (can be configured later)${NC}"
    
    # Services
    echo -e "${CYAN}Installing system services...${NC}"
    setup_services "$VENV_NAME"
    
    # Aliases
    echo -e "${CYAN}Setting up command aliases...${NC}"
    setup_aliases "$VENV_NAME"
    
    # Disable HTTPS for express install
    echo -e "${CYAN}Configuring HTTPS settings...${NC}"
    disable_https
    
    # Skip Tailscale for express install
    echo -e "${YELLOW}Skipping Tailscale setup (can be configured later)${NC}"
    
    # Final setup
    echo -ne "${CYAN}Finalizing file permissions... ${NC}"
    sudo chown -R pi:pi /home/pi > /dev/null 2>&1
    echo -e "${GREEN}✓${NC}"
    
    echo -e "\n${GREEN}✓ Express install completed successfully!${NC}"
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
}

# Function for advanced install
advanced_install() {
    echo -e "${YELLOW}Starting Advanced Install...${NC}"
    echo -e "${YELLOW}You will be prompted for each installation step.${NC}"
    echo ""
    
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

    # Add Git installation prompt
    print_section_header "Software Installation"
    echo -e "${YELLOW}This step will download all the necessary files for METARMap${NC}"
    echo -e "${YELLOW}from the GitHub repository.${NC}"
    echo ""

    read -e -p "$(echo -e "${CYAN}Would you like to install Git and clone the required files? [Y/n]: ${NC}")" GIT_CHOICE
    GIT_CHOICE=${GIT_CHOICE:-y}
    case ${GIT_CHOICE,,} in
        [Yy]*|"")
            # Set default branch to production
            BRANCH="production"
            setup_git
            ;;
        [Nn]*)
            echo -e "${YELLOW}⚠ Skipping Git installation${NC}"
            ;;
        *)
            echo -e "${RED}✗ Invalid input${NC}"
            ;;
    esac

    # Add package installation prompt
    print_section_header "Python Package Installation"
    echo -e "${YELLOW}The following packages are required for METARMap:${NC}"
    echo -e "  ${CYAN}• adafruit-circuitpython-neopixel${NC} - LED control"
    echo -e "  ${CYAN}• flask${NC} - web interface"
    echo -e "  ${CYAN}• requests${NC} - API communication"
    echo -e "  ${CYAN}• schedule${NC} - task automation"
    echo -e "  ${CYAN}• astral${NC} - sunrise/sunset calculations"
    echo -e "  ${CYAN}• pytz${NC} - time zone calculations"
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

    # Add WiFi broadcasting setup prompt
    setup_wifi_broadcast

    # Add to main script:
    print_section_header "Service Installation"
    echo -e "${YELLOW}This will install the following services:${NC}"
    echo -e "  ${CYAN}• METAR service${NC} - Controls the LED display"
    echo -e "  ${CYAN}• Settings service${NC} - Provides the web interface"
    echo -e "  ${CYAN}• Scheduler service${NC} - Handles automated tasks"
    echo -e "  ${CYAN}• LED Test service${NC} - Provides LED testing functionality"
    echo ""

    read -e -p "$(echo -e "${CYAN}Would you like to install all services? [Y/n]: ${NC}")" SERVICES_CHOICE
    SERVICES_CHOICE=${SERVICES_CHOICE:-y}
    case ${SERVICES_CHOICE,,} in
        [Yy]*|"")
            if [ -z "$VENV_NAME" ]; then
                echo -e "${RED}✗ Cannot install services without a virtual environment. Please re-run and create a venv.${NC}"
            else
                setup_services "$VENV_NAME"
            fi

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
            if [ -z "$VENV_NAME" ]; then
                echo -e "${RED}✗ Cannot install aliases without a virtual environment. Please re-run and create a venv.${NC}"
            else
                setup_aliases "$VENV_NAME"
            fi
            ;;
        [Nn]*)
            echo -e "${YELLOW}⚠ Skipping alias setup${NC}"
            ;;
        *)
            echo -e "${RED}✗ Invalid input${NC}"
            ;;
    esac

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

    # Add reboot prompt at the end
    print_section_header "Setup Complete"
    echo -e "${GREEN}✓ METARMap installation has been completed successfully!${NC}"
    echo -e "${YELLOW}A system reboot is recommended to apply all changes.${NC}"
    echo ""

    # Final ownership check
    echo -ne "${CYAN}Finalizing file permissions for /home/pi... ${NC}"
    sudo chown -R pi:pi /home/pi > /dev/null 2>&1
    echo -e "${GREEN}✓${NC}"

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
}

# Function to setup WiFi broadcasting
setup_wifi_broadcast() {
    print_section_header "WiFi Broadcasting Setup"
    echo -e "${YELLOW}This will configure your Raspberry Pi to create its own WiFi network${NC}"
    echo -e "${YELLOW}when no other WiFi networks are available.${NC}"
    echo ""
    
    # Present options for WiFi broadcasting
    echo -e "  ${MAGENTA}1)${NC} ${GREEN}AccessPopup${NC} (RaspberryConnect solution)"
    echo -e "  ${MAGENTA}2)${NC} ${YELLOW}Skip${NC} WiFi broadcasting setup"
    echo ""
    
    read -p "$(echo -e "${CYAN}Enter choice (1 or 2): ${NC}")" WIFI_SOLUTION
    
    case $WIFI_SOLUTION in
        1)
            setup_accesspopup
            ;;
        2)
            echo -e "${YELLOW}Skipping WiFi broadcasting setup...${NC}"
            return
            ;;
        *)
            echo -e "${RED}Invalid choice. Skipping WiFi broadcasting setup...${NC}"
            return
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
            rm -f AccessPopup.tar.gz > /dev/null 2>&1
            rm -rf AccessPopup > /dev/null 2>&1
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

# Function to create service file
create_service_file() {
    local service_name=$1
    local service_content=$2
    local service_path="/etc/systemd/system/${service_name}"

    echo -ne "${CYAN}Creating ${service_name}... ${NC}"
    echo -e "$service_content" | sudo tee "$service_path" > /dev/null

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed${NC}"
        return 1
    fi
}

# Function to setup services
setup_services() {
    local venv_name=$1

    if [ -z "$venv_name" ]; then
        echo -e "${RED}✗ Virtual environment name not provided. Cannot create services.${NC}"
        return 1
    fi

    # Service definitions using the provided venv_name
    # Note: All services run as root to handle GPIO and service control without sudo issues.
    METAR_SERVICE="[Unit]
Description=Run Metar Service
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/pi
ExecStart=/home/pi/${venv_name}/bin/python3 /home/pi/metar.py
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
ExecStart=/home/pi/${venv_name}/bin/python3 /home/pi/settings.py
Restart=on-failure
User=root
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
ExecStart=/home/pi/${venv_name}/bin/python3 /home/pi/scheduler.py
Restart=always
User=root
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target"

    LED_TEST_SERVICE="[Unit]
Description=LED Test Service
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/pi
ExecStart=/home/pi/${venv_name}/bin/python3 /home/pi/led_test.py
Restart=always
User=root
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target"

    echo -ne "${CYAN}Reloading systemd daemon... ${NC}"
    if sudo systemctl daemon-reload > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"

        # Create and enable services
        create_service_file "metar.service" "$METAR_SERVICE"
        create_service_file "settings.service" "$SETTINGS_SERVICE"
        create_service_file "scheduler.service" "$SCHEDULER_SERVICE"
        create_service_file "ledtest.service" "$LED_TEST_SERVICE"

        local services=("metar.service" "settings.service" "scheduler.service") # ledtest is on-demand
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

    return 0
}

# Function to setup aliases
setup_aliases() {
    local venv_name=$1
    if [ -z "$venv_name" ]; then
        echo -e "${RED}✗ Virtual environment name not provided. Cannot create aliases.${NC}"
        return 1
    fi

    local ALIASES="alias blank='sudo /home/pi/${venv_name}/bin/python3 /home/pi/blank.py'
alias metar='sudo /home/pi/${venv_name}/bin/python3 '
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
alias schedulerstatus='sudo systemctl status scheduler.service'"

    echo -ne "${CYAN}Installing command aliases... ${NC}"
    # Write aliases to the pi user's .bash_aliases file
    echo "$ALIASES" | sudo -u pi tee /home/pi/.bash_aliases > /dev/null

    echo -e "${GREEN}✓${NC}"
    echo -e "${YELLOW}To use the aliases in your current session, run:${NC}"
    echo -e "    ${CYAN}source /home/pi/.bash_aliases${NC}"
    echo -e "${YELLOW}Or log out and log back in for aliases to take effect automatically.${NC}"
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

# Function to setup SSL certificate
setup_ssl() {
    print_section_header "SSL Certificate Setup"
    echo -e "${YELLOW}Generating self-signed SSL certificate...${NC}"

    # Create directory for certificates if it doesn't exist
    sudo mkdir -p /etc/ssl/certs /etc/ssl/private

    # Generate SSL certificate
    echo -ne "${CYAN}Generating SSL certificate... ${NC}"
    if sudo openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
        -keyout /etc/ssl/private/flask-selfsigned.key \
        -out /etc/ssl/certs/flask-selfsigned.crt \
        -subj "/C=US/ST=State/L=City/O=METARMap/CN=metar.local" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗ Failed to generate SSL certificate${NC}"
        return 1
    fi

    # Set proper permissions
    echo -ne "${CYAN}Setting certificate permissions... ${NC}"
    if sudo chmod 644 /etc/ssl/certs/flask-selfsigned.crt && \
       sudo chmod 600 /etc/ssl/private/flask-selfsigned.key; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗ Failed to set permissions${NC}"
        return 1
    fi

    # Update config.py to enable HTTPS
    local CONFIG_FILE="/home/pi/config.py"
    if [ -f "$CONFIG_FILE" ]; then
        echo -ne "${CYAN}Updating config.py to enable HTTPS... ${NC}"

        # Create backup
        sudo cp "$CONFIG_FILE" "${CONFIG_FILE}.bak"

        # Update or add SSL configuration
        if grep -q "ENABLE_HTTPS" "$CONFIG_FILE"; then
            sudo sed -i 's/ENABLE_HTTPS *= *False/ENABLE_HTTPS = True/' "$CONFIG_FILE"
            sudo sed -i 's/ENABLE_HTTPS *= *True/ENABLE_HTTPS = True/' "$CONFIG_FILE"
        else
            echo "ENABLE_HTTPS = True" | sudo tee -a "$CONFIG_FILE" > /dev/null
        fi

        # Verify the changes
        if grep -q "ENABLE_HTTPS = True" "$CONFIG_FILE"; then
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${RED}⚠ Warning: Failed to update ENABLE_HTTPS in config.py${NC}"
        fi
    else
        echo -e "${RED}✗ Error: config.py not found at $CONFIG_FILE${NC}"
        return 1
    fi

    echo -e "\n${GREEN}✓ SSL setup completed successfully${NC}"
    echo -e "${YELLOW}Note: Since this is a self-signed certificate, browsers will show a security warning.${NC}"
    echo -e "${YELLOW}This is normal for self-signed certificates.${NC}"
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

# Main script
print_welcome_banner

# Choose installation type
echo -e "${CYAN}Choose installation type:${NC}"
echo -e "  ${MAGENTA}1)${NC} ${GREEN}Express Install${NC} (automated, recommended)"
echo -e "  ${MAGENTA}2)${NC} ${YELLOW}Advanced Install${NC} (step-by-step, customizable)"
echo ""

read -p "$(echo -e "${CYAN}Enter choice (1 or 2): ${NC}")" INSTALL_CHOICE

case $INSTALL_CHOICE in
    1|"")
        express_install
        ;;
    2)
        advanced_install
        ;;
    *)
        echo -e "${RED}✗ Invalid choice${NC}"
        exit 1
        ;;
esac
