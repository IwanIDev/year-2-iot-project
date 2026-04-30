.PHONY: install uninstall copy-files enable-service disable-service start-service stop-service status-service clean

# Configuration
INSTALL_DIR ?= /opt/modes
SERVICE_NAME := modes.service
SERVICE_DIR := /etc/systemd/system
SERVICE_FILE := modes/$(SERVICE_NAME)
MODES_USER := modes
MODES_GROUP := modes

# Color output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help:
	@echo "$(GREEN)Modes System Installation and Management$(NC)"
	@echo ""
	@echo "$(YELLOW)Installation targets:$(NC)"
	@echo "  make install              - Copy code and install the systemd service"
	@echo "  make copy-files           - Copy the modes system to the installation directory"
	@echo ""
	@echo "$(YELLOW)Service management:$(NC)"
	@echo "  make enable-service       - Enable systemd service (auto-start)"
	@echo "  make disable-service      - Disable systemd service"
	@echo "  make start-service        - Start the modes service"
	@echo "  make stop-service         - Stop the modes service"
	@echo "  make restart-service      - Restart the modes service"
	@echo "  make status-service       - Show service status"
	@echo ""
	@echo "$(YELLOW)Maintenance:$(NC)"
	@echo "  make uninstall            - Remove the installation and service"
	@echo "  make clean                - Clean temporary files"
	@echo ""
	@echo "$(YELLOW)Options:$(NC)"
	@echo "  INSTALL_DIR=<path>        - Installation directory (default: $(INSTALL_DIR))"

install: check-root copy-files enable-service
	@echo "$(GREEN)✓ Installation complete!$(NC)"
	@echo "Service is configured and enabled. Start with: make start-service"

check-root:
	@if [ "$$(id -u)" != "0" ]; then \
		echo "$(RED)✗ This target must be run as root$(NC)"; \
		exit 1; \
	fi

copy-files: check-root
	@echo "$(YELLOW)Copying modes system to $(INSTALL_DIR)...$(NC)"
	mkdir -p $(INSTALL_DIR)
	rm -rf $(INSTALL_DIR)/modes
	cp -r modes $(INSTALL_DIR)/
	mkdir -p $(INSTALL_DIR)/web-app/bin_lookup
	cp -r web-app/bin_lookup/* $(INSTALL_DIR)/web-app/bin_lookup/
	mkdir -p $(INSTALL_DIR)/classifier
	cp -r classifier/* $(INSTALL_DIR)/classifier/
	@echo "$(YELLOW)Creating system user and group...$(NC)"
	if ! id "$(MODES_USER)" &>/dev/null; then \
		groupadd -f $(MODES_GROUP); \
		useradd -r -g $(MODES_GROUP) -d $(INSTALL_DIR) -s /usr/sbin/nologin $(MODES_USER); \
	fi
	chown -R $(MODES_USER):$(MODES_GROUP) $(INSTALL_DIR)
	chmod 750 $(INSTALL_DIR)
	chmod 755 $(INSTALL_DIR)/modes
	@echo "$(GREEN)✓ Files copied and permissions set$(NC)"

enable-service: check-root
	@echo "$(YELLOW)Installing systemd service...$(NC)"
	cp $(SERVICE_FILE) $(SERVICE_DIR)/
	systemctl daemon-reload
	systemctl enable $(SERVICE_NAME)
	@echo "$(GREEN)✓ Service enabled$(NC)"

disable-service: check-root
	@echo "$(YELLOW)Disabling systemd service...$(NC)"
	systemctl disable $(SERVICE_NAME) 2>/dev/null || true
	rm -f $(SERVICE_DIR)/$(SERVICE_NAME)
	systemctl daemon-reload
	@echo "$(GREEN)✓ Service disabled$(NC)"

start-service: check-root
	@echo "$(YELLOW)Starting modes service...$(NC)"
	systemctl start $(SERVICE_NAME)
	@sleep 1
	systemctl status $(SERVICE_NAME)

stop-service: check-root
	@echo "$(YELLOW)Stopping modes service...$(NC)"
	systemctl stop $(SERVICE_NAME)
	@sleep 1
	systemctl status $(SERVICE_NAME) || echo "Service stopped"

restart-service: check-root
	@echo "$(YELLOW)Restarting modes service...$(NC)"
	systemctl restart $(SERVICE_NAME)
	@sleep 1
	systemctl status $(SERVICE_NAME)

status-service:
	@echo "$(YELLOW)Modes service status:$(NC)"
	systemctl status $(SERVICE_NAME) --no-pager || echo "Service not running"

logs-service:
	@echo "$(YELLOW)Displaying service logs (press Ctrl+C to exit):$(NC)"
	journalctl -u $(SERVICE_NAME) -f

uninstall: check-root disable-service
	@echo "$(RED)Uninstalling modes system...$(NC)"
	systemctl stop $(SERVICE_NAME) 2>/dev/null || true
	rm -rf $(INSTALL_DIR)
	userdel -f $(MODES_USER) 2>/dev/null || true
	groupdel -f $(MODES_GROUP) 2>/dev/null || true
	@echo "$(RED)✓ System uninstalled$(NC)"

clean:
	@echo "$(YELLOW)Cleaning temporary files...$(NC)"
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

.PHONY: $(MAKECMDGOALS)
