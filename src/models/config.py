"""Bot configuration model for storing settings."""

from enum import Enum
from typing import Any, Dict, Optional

from sqlalchemy import Boolean, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ConfigCategory(str, Enum):
    """Configuration categories."""
    
    GENERAL = "general"
    DISCORD = "discord"
    GITHUB = "github"
    NOTION = "notion"
    CALENDAR = "calendar"
    NOTIFICATIONS = "notifications"
    SECURITY = "security"
    FEATURES = "features"
    INTEGRATIONS = "integrations"
    STANDUP = "standup"
    TIME_TRACKING = "time_tracking"
    MENTORSHIP = "mentorship"
    ONBOARDING = "onboarding"


class ConfigValueType(str, Enum):
    """Configuration value types."""
    
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"
    LIST = "list"
    DICT = "dict"


class BotConfig(Base):
    """Bot configuration settings."""

    __tablename__ = "bot_config"

    # Configuration identification
    key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    category: Mapped[ConfigCategory] = mapped_column(String(30), nullable=False, index=True)
    
    # Configuration details
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Value storage
    value_type: Mapped[ConfigValueType] = mapped_column(String(20), nullable=False)
    string_value: Mapped[Optional[str]] = mapped_column(Text)
    json_value: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Default value
    default_value: Mapped[Optional[str]] = mapped_column(Text)
    
    # Validation and constraints
    validation_regex: Mapped[Optional[str]] = mapped_column(String(500))
    min_value: Mapped[Optional[float]] = mapped_column()
    max_value: Mapped[Optional[float]] = mapped_column()
    allowed_values: Mapped[Optional[list]] = mapped_column(JSON)  # List of allowed values
    
    # Configuration metadata
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
    is_secret: Mapped[bool] = mapped_column(Boolean, default=False)  # Hide value in UI
    is_readonly: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Environment and deployment
    environment_specific: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_restart: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # UI presentation
    display_order: Mapped[int] = mapped_column(default=0)
    help_text: Mapped[Optional[str]] = mapped_column(Text)
    placeholder: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Change tracking
    last_modified_by: Mapped[Optional[str]] = mapped_column(String(100))
    change_reason: Mapped[Optional[str]] = mapped_column(Text)

    __table_args__ = (
        UniqueConstraint('key', name='uq_bot_config_key'),
    )

    def __repr__(self) -> str:
        return f"<BotConfig(key={self.key}, category={self.category}, type={self.value_type})>"

    @property
    def value(self) -> Any:
        """Get the configuration value with proper type casting."""
        if self.value_type == ConfigValueType.STRING:
            return self.string_value
        elif self.value_type == ConfigValueType.INTEGER:
            return int(self.string_value) if self.string_value else None
        elif self.value_type == ConfigValueType.FLOAT:
            return float(self.string_value) if self.string_value else None
        elif self.value_type == ConfigValueType.BOOLEAN:
            return self.string_value.lower() == 'true' if self.string_value else None
        elif self.value_type in [ConfigValueType.JSON, ConfigValueType.LIST, ConfigValueType.DICT]:
            return self.json_value
        return self.string_value

    @value.setter
    def value(self, new_value: Any) -> None:
        """Set the configuration value with proper type handling."""
        if self.value_type == ConfigValueType.STRING:
            self.string_value = str(new_value) if new_value is not None else None
        elif self.value_type == ConfigValueType.INTEGER:
            self.string_value = str(int(new_value)) if new_value is not None else None
        elif self.value_type == ConfigValueType.FLOAT:
            self.string_value = str(float(new_value)) if new_value is not None else None
        elif self.value_type == ConfigValueType.BOOLEAN:
            self.string_value = str(bool(new_value)).lower() if new_value is not None else None
        elif self.value_type in [ConfigValueType.JSON, ConfigValueType.LIST, ConfigValueType.DICT]:
            self.json_value = new_value
        else:
            self.string_value = str(new_value) if new_value is not None else None

    def validate_value(self, value: Any) -> bool:
        """Validate a value against the configuration constraints."""
        # Type validation
        if self.value_type == ConfigValueType.INTEGER:
            try:
                int_val = int(value)
                if self.min_value is not None and int_val < self.min_value:
                    return False
                if self.max_value is not None and int_val > self.max_value:
                    return False
            except (ValueError, TypeError):
                return False
                
        elif self.value_type == ConfigValueType.FLOAT:
            try:
                float_val = float(value)
                if self.min_value is not None and float_val < self.min_value:
                    return False
                if self.max_value is not None and float_val > self.max_value:
                    return False
            except (ValueError, TypeError):
                return False
                
        elif self.value_type == ConfigValueType.BOOLEAN:
            if not isinstance(value, bool) and str(value).lower() not in ['true', 'false']:
                return False

        # Allowed values validation
        if self.allowed_values and value not in self.allowed_values:
            return False

        # Regex validation
        if self.validation_regex and isinstance(value, str):
            import re
            if not re.match(self.validation_regex, value):
                return False

        return True

    def reset_to_default(self) -> None:
        """Reset configuration to default value."""
        if self.default_value is not None:
            if self.value_type in [ConfigValueType.JSON, ConfigValueType.LIST, ConfigValueType.DICT]:
                import json
                try:
                    self.json_value = json.loads(self.default_value)
                except json.JSONDecodeError:
                    self.json_value = None
            else:
                self.string_value = self.default_value
        else:
            self.string_value = None
            self.json_value = None

    @classmethod
    def get_by_key(cls, key: str) -> Optional["BotConfig"]:
        """Get configuration by key."""
        # This would be implemented in the service layer
        pass

    @classmethod
    def get_by_category(cls, category: ConfigCategory) -> list["BotConfig"]:
        """Get all configurations in a category."""
        # This would be implemented in the service layer
        pass

    @classmethod
    def create_default_configs(cls) -> list["BotConfig"]:
        """Create default configuration entries."""
        default_configs = [
            # General settings
            {
                "key": "bot_name",
                "category": ConfigCategory.GENERAL,
                "name": "Bot Name",
                "description": "Display name for the bot",
                "value_type": ConfigValueType.STRING,
                "default_value": "IRA Bot",
                "is_required": True,
            },
            {
                "key": "timezone",
                "category": ConfigCategory.GENERAL,
                "name": "Default Timezone",
                "description": "Default timezone for the bot",
                "value_type": ConfigValueType.STRING,
                "default_value": "UTC",
                "is_required": True,
            },
            
            # Standup settings
            {
                "key": "standup_time",
                "category": ConfigCategory.STANDUP,
                "name": "Daily Standup Time",
                "description": "Time to send daily standup reminders (HH:MM format)",
                "value_type": ConfigValueType.STRING,
                "default_value": "09:00",
                "validation_regex": r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$",
            },
            {
                "key": "standup_enabled",
                "category": ConfigCategory.STANDUP,
                "name": "Enable Daily Standups",
                "description": "Enable automatic daily standup reminders",
                "value_type": ConfigValueType.BOOLEAN,
                "default_value": "true",
            },
            
            # Time tracking settings
            {
                "key": "time_tracking_enabled",
                "category": ConfigCategory.TIME_TRACKING,
                "name": "Enable Time Tracking",
                "description": "Enable check-in/check-out time tracking",
                "value_type": ConfigValueType.BOOLEAN,
                "default_value": "true",
            },
            {
                "key": "max_work_hours_per_day",
                "category": ConfigCategory.TIME_TRACKING,
                "name": "Maximum Work Hours Per Day",
                "description": "Maximum allowed work hours per day",
                "value_type": ConfigValueType.INTEGER,
                "default_value": "12",
                "min_value": 1,
                "max_value": 24,
            },
            
            # Notification settings
            {
                "key": "notification_channel",
                "category": ConfigCategory.NOTIFICATIONS,
                "name": "Default Notification Channel",
                "description": "Default Discord channel for bot notifications",
                "value_type": ConfigValueType.STRING,
            },
            
            # GitHub integration
            {
                "key": "github_notifications_enabled",
                "category": ConfigCategory.GITHUB,
                "name": "Enable GitHub Notifications",
                "description": "Enable GitHub webhook notifications",
                "value_type": ConfigValueType.BOOLEAN,
                "default_value": "true",
            },
            
            # Notion integration
            {
                "key": "notion_sync_enabled",
                "category": ConfigCategory.NOTION,
                "name": "Enable Notion Sync",
                "description": "Enable Notion task synchronization",
                "value_type": ConfigValueType.BOOLEAN,
                "default_value": "true",
            },
            {
                "key": "notion_sync_interval",
                "category": ConfigCategory.NOTION,
                "name": "Notion Sync Interval",
                "description": "Notion sync interval in minutes",
                "value_type": ConfigValueType.INTEGER,
                "default_value": "15",
                "min_value": 5,
                "max_value": 1440,
            },
        ]
        
        return [cls(**config) for config in default_configs] 