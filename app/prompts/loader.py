import os
from app.prompts.versions import (
    ACTIONABILITY_PROMPT_VERSION,
    CONDENSER_PROMPT_VERSION,
    CRITIC_PROMPT_VERSION,
    REFLECTION_PROMPT_VERSION
)

class PromptLoader:
    @staticmethod
    def get_prompt_path(prompt_filename: str) -> str:
        """Get the absolute path to a prompt file in the prompts/ directory."""
        # Find project root (3 levels up from this file)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(project_root, "prompts", prompt_filename)

    @classmethod
    def load_prompt(cls, prompt_filename: str) -> str:
        """Load prompt contents from disk."""
        path = cls.get_prompt_path(prompt_filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Prompt file not found at: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    @classmethod
    def load_actionability_prompt(cls) -> str:
        return cls.load_prompt(f"{ACTIONABILITY_PROMPT_VERSION}.md")

    @classmethod
    def load_condenser_prompt(cls) -> str:
        return cls.load_prompt(f"{CONDENSER_PROMPT_VERSION}.md")

    @classmethod
    def load_critic_prompt(cls) -> str:
        return cls.load_prompt(f"{CRITIC_PROMPT_VERSION}.md")

    @classmethod
    def load_reflection_prompt(cls) -> str:
        return cls.load_prompt(f"{REFLECTION_PROMPT_VERSION}.md")
