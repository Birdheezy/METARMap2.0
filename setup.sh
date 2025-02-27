#!/bin/bash
# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if script is run with sudo
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

# Function to update system
update_system() {
    echo "Updating package lists..."
    if apt update; then
        echo -e "${GREEN}Package lists updated successfully${NC}"
        echo "Upgrading packages..."
        if apt upgrade -y; then
            echo -e "${GREEN}System upgrade completed successfully${NC}"
            return 0
        else
            echo -e "${RED}Error during system upgrade${NC}"
            return 1
        fi
    else
        echo -e "${RED}Error updating package lists${NC}"
        return 1
    fi
}

# Function to create virtual environment
create_venv() {
    local venv_name=$1
    echo "Creating virtual environment: $venv_name"
    if python3 -m venv --system-site-packages "$venv_name"; then
        echo -e "${GREEN}Virtual environment created successfully${NC}"
        return 0
    else
        echo -e "${RED}Error creating virtual environment${NC}"
        return 1
    fi
}

# Main script
echo "Welcome to METARMap setup"

read -e -p "Would you like to update the system? [Y/n]: " UPDATE_CHOICE
UPDATE_CHOICE=${UPDATE_CHOICE:-y}  # Default to 'y' if empty
case ${UPDATE_CHOICE,,} in  # Convert to lowercase
    [Yy]*|"")
        update_system
        ;;
    [Nn]*)
        echo "Skipping system update"
        ;;
    *)
        echo -e "${RED}Invalid input${NC}"
        exit 1
        ;;
esac


# Virtual environment setup prompt
read -e -p "Would you like to set up a virtual environment? [Y/n]: " VENV_SETUP_CHOICE
VENV_SETUP_CHOICE=${VENV_SETUP_CHOICE:-y}
case ${VENV_SETUP_CHOICE,,} in
    [Yy]*|"")
        # Ask for virtual environment name
        read -p "Enter virtual environment name (default: metar): " VENV_NAME
        VENV_NAME=${VENV_NAME:-metar}

        # Validate venv name (only allow alphanumeric and underscores)
        if [[ ! $VENV_NAME =~ ^[a-zA-Z0-9_]+$ ]]; then
            echo -e "${RED}Invalid virtual environment name. Use only letters, numbers, and underscores.${NC}"
            exit 1
        fi

        create_venv "$VENV_NAME"
        ;;
    [Nn]*)
        echo "Skipping virtual environment setup"
        ;;
    *)
        echo -e "${RED}Invalid input${NC}"
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

    echo "Installing Python packages..."
    # Activate virtual environment
    source "${venv_name}/bin/activate"
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to activate virtual environment${NC}"
        return 1
    fi

    # Install each package
    for package in "${packages[@]}"; do
        echo "Installing $package..."
        if pip3 install "$package"; then
            echo -e "${GREEN}✓ $package installed${NC}"
        else
            echo -e "${RED}Failed to install $package${NC}"
            deactivate
            return 1
        fi
    done

    # Deactivate virtual environment
    deactivate
    echo -e "${GREEN}All packages installed successfully${NC}"
    return 0
}

# Add package installation prompt
echo -e "\n${GREEN}=== Python Package Installation ===${NC}"
echo "The following packages will be installed:"
echo "- adafruit-circuitpython-neopixel (LED control)"
echo "- flask (web interface)"
echo "- requests (API communication)"
echo "- schedule (task automation)"

read -e -p "Would you like to install the required packages? [Y/n]: " PACKAGES_CHOICE
PACKAGES_CHOICE=${PACKAGES_CHOICE:-y}
case ${PACKAGES_CHOICE,,} in
    [Yy]*|"")
        if [ $? -eq 0 ]; then
            install_packages "$VENV_NAME"
        fi
        ;;
    [Nn]*)
        echo "Skipping package installation"
        ;;
    *)
        echo -e "${RED}Invalid input${NC}"
        ;;
esac


# Function to setup WiFi broadcasting
setup_wifi_broadcast() {
    echo -e "\n${GREEN}=== Auto WiFi Broadcasting Setup ===${NC}"
    echo "This will launch an interactive installer."
    echo "You will need to:"
    echo "1. Select option 1 to install"
    echo "2. Set SSID to: METAR Pi"
    echo "3. Set Password to: METAR-Pi-Password"
    echo "4. Set IP address to: 192.168.8.1"

    read -p "Ready to proceed? (y/n): " PROCEED

    if [[ $PROCEED =~ ^[Yy]$ ]]; then
        # Download and extract
        if curl "https://www.raspberryconnect.com/images/scripts/AccessPopup.tar.gz" -o AccessPopup.tar.gz; then
            tar -xvf ./AccessPopup.tar.gz
            cd AccessPopup

            echo -e "\n${GREEN}Starting interactive installer...${NC}"
            echo "After completion, this script will resume."

            # Launch interactive installer
            sudo ./installconfig.sh

            # Return to original directory
            cd ..

            # Cleanup
            rm -rf AccessPopup.tar.gz

            echo -e "\n${GREEN}WiFi broadcast setup completed${NC}"
            return 0
        else
            echo -e "${RED}Failed to download WiFi broadcast package${NC}"
            return 1
        fi
    else
        echo "Skipping WiFi broadcast setup"
        return 0
    fi
}

# Add to main script after package installation:
echo -e "\n${GREEN}=== Would you like to install Auto WiFi Broadcasting Capabilities? ===${NC}"
read -e -p "This will launch an interactive installer [Y/n]: " WIFI_CHOICE
WIFI_CHOICE=${WIFI_CHOICE:-y}
case ${WIFI_CHOICE,,} in
    [Yy]*|"")
        setup_wifi_broadcast
        ;;
    [Nn]*)
        echo "Skipping WiFi broadcast setup"
        ;;
    *)
        echo -e "${RED}Invalid input${NC}"
        ;;
esac

# Function to install a service
install_service() {
    local service_name=$1
    local service_content=$2

    echo "Creating ${service_name}..."
    echo "$service_content" | sudo tee "/etc/systemd/system/${service_name}" > /dev/null

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Created ${service_name}${NC}"
        sudo systemctl daemon-reload
        sudo systemctl enable "${service_name}"
        echo -e "${GREEN}Enabled ${service_name}${NC}"
        return 0
    else
        echo -e "${RED}Failed to create ${service_name}${NC}"
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

    echo "Creating ${service_name}..."
    echo "$service_content" > "$service_path"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Created ${service_name}${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed to create ${service_name}${NC}"
        return 1
    fi
}

# Function to enable services
enable_services() {
    echo "Reloading systemd daemon..."
    if sudo systemctl daemon-reload; then
        echo -e "${GREEN}✓ Daemon reloaded${NC}"

        local services=("metar.service" "settings.service" "scheduler.service")
        for service in "${services[@]}"; do
            echo "Enabling ${service}..."
            if sudo systemctl enable "$service"; then
                echo -e "${GREEN}✓ Enabled ${service}${NC}"
            else
                echo -e "${RED}✗ Failed to enable ${service}${NC}"
            fi
        done
    else
        echo -e "${RED}✗ Failed to reload daemon${NC}"
        return 1
    fi
}

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
alias schedulerstatus='sudo systemctl status scheduler.service'"

    # Write aliases to the pi user's .bash_aliases file
    echo "$ALIASES" | sudo -u pi tee /home/pi/.bash_aliases > /dev/null

    echo -e "${GREEN}✓ Aliases installed${NC}"
    echo -e "${GREEN}To use the aliases in your current session, run:${NC}"
    echo -e "    source /home/pi/.bash_aliases"
    echo -e "Or log out and log back in for aliases to take effect automatically."
    return 0
}

# Add to main script:
echo -e "\n${GREEN}=== Service Installation ===${NC}"
echo "This will install the following services:"
echo "- METAR service (LED control)"
echo "- Settings service (web interface)"
echo "- Scheduler service (automation)"

read -e -p "Would you like to install all services? [Y/n]: " SERVICES_CHOICE
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
        echo "Skipping service installation and enabling"
        ;;
    *)
        echo -e "${RED}Invalid input${NC}"
        ;;
esac



# Add after service installation section:
echo -e "\n${GREEN}=== Alias Setup ===${NC}"
read -e -p "Would you like to install command aliases? [Y/n]: " ALIAS_CHOICE
ALIAS_CHOICE=${ALIAS_CHOICE:-y}
case ${ALIAS_CHOICE,,} in
    [Yy]*|"")
        setup_aliases
        ;;
    [Nn]*)
        echo "Skipping alias setup"
        ;;
    *)
        echo -e "${RED}Invalid input${NC}"
        ;;
esac

# Function to install Tailscale
install_tailscale() {
    echo -e "\n${GREEN}=== Installing Tailscale ===${NC}"

    # Install https transport
    echo "Installing HTTPS transport..."
    if ! sudo apt-get install -y apt-transport-https; then
        echo -e "${RED}Failed to install HTTPS transport${NC}"
        return 1
    fi

    # Add Tailscale GPG key
    echo "Adding Tailscale GPG key..."
    if ! curl -fsSL https://pkgs.tailscale.com/stable/debian/bookworm.noarmor.gpg | sudo tee /usr/share/keyrings/tailscale-archive-keyring.gpg > /dev/null; then
        echo -e "${RED}Failed to add Tailscale GPG key${NC}"
        return 1
    fi

    # Add Tailscale repository
    echo "Adding Tailscale repository..."
    if ! curl -fsSL https://pkgs.tailscale.com/stable/debian/bookworm.tailscale-keyring.list | sudo tee /etc/apt/sources.list.d/tailscale.list; then
        echo -e "${RED}Failed to add Tailscale repository${NC}"
        return 1
    fi

    # Update package lists
    echo "Updating package lists..."
    if ! sudo apt update; then
        echo -e "${RED}Failed to update package lists${NC}"
        return 1
    fi

    # Install Tailscale
    echo "Installing Tailscale..."
    if ! sudo apt install tailscale -y; then
        echo -e "${RED}Failed to install Tailscale${NC}"
        return 1
    fi

    # Enable auto-updates
    echo "Enabling auto-updates..."
    if ! sudo tailscale set --auto-update; then
        echo -e "${RED}Failed to enable auto-updates${NC}"
        return 1
    fi

    # Start Tailscale
    echo -e "\n${GREEN}Starting Tailscale...${NC}"
    echo "A URL will be displayed. Copy and paste it into your web browser to complete setup."
    echo -e "Press ${GREEN}Enter${NC} when ready..."
    read

    if ! sudo tailscale up --ssh; then
        echo -e "${RED}Failed to start Tailscale${NC}"
        return 1
    fi

    echo -e "\n${GREEN}Tailscale installation completed${NC}"
    echo "Please make sure to disable key expiry in the Tailscale admin console"
    return 0
}

# Add Tailscale installation prompt
echo -e "\n${GREEN}=== Tailscale Setup ===${NC}"
read -e -p "Would you like to install Tailscale? [N/y]: " TAILSCALE_CHOICE
TAILSCALE_CHOICE=${TAILSCALE_CHOICE:-n}
case ${TAILSCALE_CHOICE,,} in
    [Yy]*)
        install_tailscale
        ;;
    [Nn]*)
        echo "Skipping Tailscale installation"
        ;;
    *)
        echo -e "${RED}Invalid input${NC}"
        ;;
esac

setup_git() {
    echo -e "\n${GREEN}=== Installing Git and Cloning Repository ===${NC}"

    # Install Git
    echo "Installing Git..."
    if ! sudo apt install git -y; then
        echo -e "${RED}Failed to install Git${NC}"
        return 1
    fi

    cd /home/pi || return 1

    # Let user choose branch
    echo -e "\n${GREEN}Choose which branch to install:${NC}"
    echo "1) main (beta/development branch)"
    echo "2) production (stable branch)"
    read -p "Enter choice (1 or 2): " BRANCH_CHOICE

    case $BRANCH_CHOICE in
        1) BRANCH="main" ;;
        2) BRANCH="production" ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            return 1
            ;;
    esac

    # Initialize git repo
    echo "Initializing Git repository with $BRANCH branch..."
    if ! git init -b "$BRANCH"; then
        echo -e "${RED}Failed to initialize repository${NC}"
        return 1
    fi

    # Add remote origin
    echo "Adding remote repository..."
    if ! git remote add origin https://github.com/Birdheezy/METARMap2.0; then
        echo -e "${RED}Failed to add remote${NC}"
        return 1
    fi

    # Fetch branches
    echo "Fetching repository branches..."
    if ! git fetch origin; then
        echo -e "${RED}Failed to fetch branches${NC}"
        return 1
    fi

    # Checkout selected branch with force
    echo "Setting up $BRANCH branch..."
    if ! git checkout -f -b "$BRANCH" "origin/$BRANCH"; then
        echo -e "${RED}Failed to checkout $BRANCH branch${NC}"
        return 1
    fi

    # Pull latest changes with force
    echo "Pulling latest changes..."
    if ! git pull -f origin "$BRANCH"; then
        echo -e "${RED}Failed to pull latest changes${NC}"
        return 1
    fi

    # Set ownership
    sudo chown -R pi:pi /home/pi

    echo -e "${GREEN}✓ Git repository setup completed successfully${NC}"
    echo -e "Installed branch: ${GREEN}$BRANCH${NC}"
    return 0
}
# Add Git installation prompt
echo -e "\n${GREEN}=== Git Repository Setup ===${NC}"
read -e -p "Would you like to install Git and clone the required files? [Y/n]: " GIT_CHOICE
GIT_CHOICE=${GIT_CHOICE:-y}
case ${GIT_CHOICE,,} in
    [Yy]*|"")
        # Modify setup_git function to default to production branch
        BRANCH="production"  # Set default branch
        setup_git
        ;;
    [Nn]*)
        echo "Skipping Git installation"
        ;;
    *)
        echo -e "${RED}Invalid input${NC}"
        ;;
esac

# Function to setup SSL certificate
setup_ssl() {
    echo -e "\n${GREEN}=== Setting up Self-Signed SSL Certificate ===${NC}"
    echo "You will be prompted to enter certificate information."
    echo "Important: When asked for 'Common Name', enter your Pi's local IP address"
    echo "For other fields, you can press '.' to leave them blank"
    echo -e "Press ${GREEN}Enter${NC} when ready..."
    read

    # Generate SSL certificate
    if ! sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/ssl/private/flask-selfsigned.key \
        -out /etc/ssl/certs/flask-selfsigned.crt; then
        echo -e "${RED}Failed to generate SSL certificate${NC}"
        return 1
    fi

    # Update config.py to enable HTTPS
    local CONFIG_FILE="/home/pi/config.py"
    if [ -f "$CONFIG_FILE" ]; then
        echo "Updating config.py to enable HTTPS..."

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
            echo -e "${GREEN}✓ Successfully enabled HTTPS in config.py${NC}"
        else
            echo -e "${RED}Warning: Failed to update ENABLE_HTTPS in config.py${NC}"
        fi
    else
        echo -e "${RED}Error: config.py not found at $CONFIG_FILE${NC}"
        return 1
    fi

    return 0
}

# Function to disable HTTPS in config
disable_https() {
    local CONFIG_FILE="/home/pi/config.py"
    if [ -f "$CONFIG_FILE" ]; then
        echo "Updating config.py to disable HTTPS..."

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
            echo -e "${GREEN}✓ Successfully disabled HTTPS in config.py${NC}"
        else
            echo -e "${RED}Warning: Failed to update ENABLE_HTTPS in config.py${NC}"
        fi
    else
        echo -e "${RED}Error: config.py not found at $CONFIG_FILE${NC}"
        return 1
    fi
}

# Add SSL setup prompt
echo -e "\n${GREEN}=== SSL Certificate Setup ===${NC}"
echo "Setting up HTTPS will:"
echo "1. Generate a self-signed SSL certificate"
echo "2. Enable HTTPS in config.py"
echo "3. Configure the web interface to use HTTPS (port 443)"
read -e -p "Would you like to setup HTTPS with a self-signed certificate? [N/y]: " SSL_CHOICE
SSL_CHOICE=${SSL_CHOICE:-n}
case ${SSL_CHOICE,,} in
    [Yy]*)
        setup_ssl
        ;;
    [Nn]*|"")
        echo "Disabling HTTPS..."
        disable_https
        echo -e "${GREEN}HTTPS disabled${NC}"
        ;;
    *)
        echo -e "${RED}Invalid input${NC}"
        ;;
esac

# Add reboot prompt at the end
echo -e "\n${GREEN}=== Setup Complete ===${NC}"
read -e -p "Would you like to reboot now? [Y/n]: " REBOOT_CHOICE
REBOOT_CHOICE=${REBOOT_CHOICE:-y}
case ${REBOOT_CHOICE,,} in
    [Yy]*|"")
        echo "Rebooting system..."
        sudo reboot
        ;;
    [Nn]*)
        echo "Please remember to reboot your system to apply all changes"
        ;;
    *)
        echo -e "${RED}Invalid input. Please reboot manually when ready${NC}"
        ;;
esac
