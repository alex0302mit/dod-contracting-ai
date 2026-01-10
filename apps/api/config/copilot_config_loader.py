"""
Copilot Configuration Loader

Loads and processes copilot configuration from JSON file.
Allows editing prompts and settings without code changes.

Usage:
    from config.copilot_config_loader import CopilotConfig

    config = CopilotConfig()
    system_prompt = config.get_system_prompt()
    action_prompt = config.get_action_prompt("rewrite", selected_text, context, section)
"""

import json
import os
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path


class CopilotConfig:
    """
    Manages copilot configuration loaded from JSON file.

    Features:
    - Load prompts from external config file
    - Dynamic variable substitution (dates, etc.)
    - Hot-reload capability (call reload() to refresh)
    """

    _instance = None
    _config: Dict = {}
    _last_loaded: datetime = None

    def __new__(cls):
        """Singleton pattern - only one config instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _get_config_path(self) -> Path:
        """Get path to config file"""
        # Config file is in same directory as this module
        return Path(__file__).parent / "copilot_config.json"

    def _load_config(self) -> None:
        """Load configuration from JSON file"""
        config_path = self._get_config_path()

        if not config_path.exists():
            raise FileNotFoundError(f"Copilot config not found: {config_path}")

        with open(config_path, 'r') as f:
            self._config = json.load(f)

        self._last_loaded = datetime.now()
        print(f"[CopilotConfig] Loaded config from {config_path}")

    def reload(self) -> None:
        """Reload configuration from file (for hot-reload)"""
        self._load_config()

    def _resolve_dynamic_variables(self) -> Dict[str, str]:
        """
        Resolve dynamic variables defined in config.

        Supports:
        - date: Current date with custom format
        - (extensible for future variable types)
        """
        resolved = {}

        dynamic_vars = self._config.get("dynamic_variables", {})

        for var_name, var_config in dynamic_vars.items():
            var_type = var_config.get("type")

            if var_type == "date":
                date_format = var_config.get("format", "%Y-%m-%d")
                resolved[var_name] = datetime.now().strftime(date_format)

            # Add more variable types here as needed
            # elif var_type == "env":
            #     resolved[var_name] = os.environ.get(var_config.get("env_var", ""), "")

        return resolved

    def get_model(self) -> str:
        """Get configured model name"""
        return self._config.get("model", "claude-sonnet-4-20250514")

    def get_max_tokens(self) -> int:
        """Get configured max tokens"""
        return self._config.get("max_tokens", 2000)

    def get_temperature(self) -> float:
        """Get configured temperature"""
        return self._config.get("temperature", 0.7)

    def get_system_prompt(self) -> str:
        """
        Get system prompt with dynamic variables resolved.

        Returns:
            Formatted system prompt string
        """
        template = self._config.get("system_prompt_template", "")

        # Resolve dynamic variables
        variables = self._resolve_dynamic_variables()

        # Substitute variables in template
        return template.format(**variables)

    def get_action_config(self, action: str) -> Optional[Dict]:
        """Get configuration for a specific action"""
        return self._config.get("actions", {}).get(action)

    def get_available_actions(self) -> list:
        """Get list of available action names"""
        return list(self._config.get("actions", {}).keys())

    def can_apply_to_editor(self, action: str) -> bool:
        """Check if action result can be applied to editor"""
        action_config = self.get_action_config(action)
        if action_config:
            return action_config.get("can_apply_to_editor", False)
        return False

    def get_action_prompt(
        self,
        action: str,
        selected_text: str,
        context: Optional[str] = None,
        section: str = "Document",
        custom_prompt: Optional[str] = None
    ) -> str:
        """
        Build the user prompt for a specific action.

        Args:
            action: The action type (rewrite, expand, etc.)
            selected_text: The text user selected
            context: Optional surrounding context
            section: Document section name
            custom_prompt: Custom user instruction (for 'custom' action)

        Returns:
            Formatted prompt string ready for Claude
        """
        action_config = self.get_action_config(action)

        if not action_config:
            raise ValueError(f"Unknown action: {action}")

        template = action_config.get("prompt_template", "")

        # Build context block if context provided
        context_block = ""
        if context:
            context_template = self._config.get(
                "context_block_template",
                "SURROUNDING CONTEXT: {context}"
            )
            context_block = context_template.format(context=context)

        # Substitute variables
        prompt = template.format(
            selected_text=selected_text,
            context_block=context_block,
            section=section,
            custom_prompt=custom_prompt or ""
        )

        return prompt


# Convenience function for quick access
def get_copilot_config() -> CopilotConfig:
    """Get the singleton CopilotConfig instance"""
    return CopilotConfig()
