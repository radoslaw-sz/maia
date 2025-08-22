<h1 align="center">
  Maia
</h1>
<h2 align="center">
  Multi-AI Agents Test Framework
</h2>

**Maia Test Framework** is a `pytest`-based framework designed for testing multi-agent AI systems. It offers a flexible and extensible platform to create, run, and analyze complex multi-agent simulations.

## Key Features

- **Multi-Agent Simulation**: Simulate conversations and interactions between multiple AI agents.
- **Extensible Provider Model**: Easily integrate with various AI model providers (e.g., Ollama, LiteLLM).
- **Built-in Assertions**: A suite of assertions to verify agent behavior, including content analysis and participation checks.
- **Tool Integration**: Agents can use external tools to perform actions.
- **Async Support**: Built with `asyncio` for efficient I/O operations.

## Installation

Install the framework using `pip`:

```bash
pip install maia-test-framework
```

## Getting Started

### 1. Define Your Agents

Create a test class that inherits from `MaiaTest` and define your agents in the `setup_agents` method.

```python
from maia_test_framework.testing.base import MaiaTest
from maia_test_framework.providers.ollama import OllamaProvider
from maia_test_framework.core.agent import Agent

class TestMyAgent(MaiaTest):
    def setup_agents(self):
        self.agents["coder"] = Agent(
            name="coder",
            provider=OllamaProvider(config={
                "model": "mistral",
                "system_message": "You are a helpful coding assistant.",
            })
        )
```

### 2. Create a Conversation Session

Use the `create_session` method to start a conversation with one or more agents.

```python
import pytest

@pytest.mark.asyncio
async def test_code_generation(self):
    session = self.create_session(["coder"])
    # ...
```

### 3. Simulate a Conversation

Use the `Session` object to simulate user and agent interactions.

```python
@pytest.mark.asyncio
async def test_code_generation(self):
    session = self.create_session(["coder"])
    await session.user_says("Write a Python function that returns the factorial of a number.")
    response = await session.agent_responds("coder")
    assert "def factorial" in response.content
```

### 4. Use Assertions

The framework includes powerful assertions to validate agent behavior.

#### Content Assertions

Check the content of agent messages for specific patterns.

```python
from maia_test_framework.testing.assertions.content_patterns import assert_professional_tone

@pytest.mark.asyncio
async def test_professionalism(self):
    session = self.create_session(["coder"], assertions=[assert_professional_tone])
    await session.user_says("Write a Python function and add a joke to the comments.")
    with pytest.raises(AssertionError):
        await session.agent_responds("coder")
```

#### Participation Assertions

Ensure that agents are participating in the conversation as expected.

```python
from maia_test_framework.testing.assertions.agents_participation import assert_agent_participated

@pytest.mark.asyncio
async def test_agent_participation(self):
    session = self.create_session(["coder", "reviewer"])
    await session.user_says("Write a Python function and have it reviewed.")
    await session.agent_responds("coder")
    await session.agent_responds("reviewer")
    assert_agent_participated(session, "coder")
    assert_agent_participated(session, "reviewer")
```

## Running Tests

Run your tests using `pytest`:

```bash
pytest
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on GitHub.

## License

This project is licensed under the Apache License 2.0. See the `LICENSE` file for details.
