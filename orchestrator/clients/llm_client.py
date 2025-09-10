import os
import yaml
import pathlib
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from ollama import AsyncClient

class LLMClient:
    def __init__(self, config_path=None):
        if config_path is None:
            config_path = pathlib.Path(__file__).parent.parent.parent / "config" / "adaptive_orchestrator.yaml"

        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f).get('llm_providers', {})

        self.provider_map = self.config.get('provider_map', {})
        self.default_provider_config = self.provider_map.get('default_agent', {})

        deepseek_config = self.config.get('deepseek_provider_config', {})
        self.clients = {
            'openai': AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY")),
            'anthropic': AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY")),
            'ollama': AsyncClient(host=os.getenv("OLLAMA_BASE_URL", self.config.get('ollama_base_url'))),
            'deepseek': AsyncOpenAI(
                api_key=os.getenv("DEEPSEEK_API_KEY"),
                base_url=deepseek_config.get('base_url')
            )
        }

    async def _call_openai_compatible(self, client_name: str, model: str, prompt: str) -> dict:
        """Generic method for OpenAI-compatible APIs."""
        client = self.clients[client_name]
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return {"text": response.choices[0].message.content, "confidence": None}

    async def _call_anthropic(self, model: str, prompt: str) -> dict:
        response = await self.clients['anthropic'].messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        return {"text": response.content[0].text, "confidence": None}

    async def _call_ollama(self, model: str, prompt: str) -> dict:
        response = await self.clients['ollama'].chat(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return {"text": response['message']['content'], "confidence": None}

    async def call_llm(self, role: str, prompt: str) -> dict:
        provider_config = self.provider_map.get(role, self.default_provider_config)

        if not provider_config:
            raise ValueError(f"No LLM provider configured for role '{role}' and no default_agent is set.")

        provider = provider_config.get('provider')
        model = provider_config.get('model')

        if provider == 'openai':
            return await self._call_openai_compatible('openai', model, prompt)
        elif provider == 'deepseek':
            return await self._call_openai_compatible('deepseek', model, prompt)
        elif provider == 'anthropic':
            return await self._call_anthropic(model, prompt)
        elif provider == 'ollama':
            return await self._call_ollama(model, prompt)
        else:
            raise NotImplementedError(f"Provider '{provider}' is not supported.")

# Singleton instance
llm_client_instance = LLMClient()

async def call_llm(role: str, prompt: str) -> dict:
    """
    Public async function to call the configured LLM provider for a given role.
    """
    return await llm_client_instance.call_llm(role, prompt)
