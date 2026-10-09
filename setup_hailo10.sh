#!/bin/bash
# Remove Hailo-8 packages
echo "Removing Hailo-8 packages..."
echo "123456" | sudo -S apt-get remove --purge -y hailo-all hailort hailort-pcie-driver python3-hailort

# Install Hailo-10 packages
echo "Installing Hailo-10 packages..."
echo "123456" | sudo -S apt-get update
echo "123456" | sudo -S apt-get install -y hailo-h10-all h10-hailort-pcie-driver python3-h10-hailort

# Add UART to config.txt if not present
echo "Configuring UART..."
if ! grep -q "enable_uart=1" /boot/firmware/config.txt; then
    echo "enable_uart=1" | sudo tee -a /boot/firmware/config.txt
fi
if ! grep -q "dtoverlay=uart0" /boot/firmware/config.txt; then
    echo "dtoverlay=uart0" | sudo tee -a /boot/firmware/config.txt
fi

echo "Done! Please reboot your Raspberry Pi."

