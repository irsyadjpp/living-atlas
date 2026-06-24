"""Quick test of Cloud LLM client with Claude API."""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai_shared.llm.cloud_llm_client import (
    CloudLLMClient,
    LLMProvider,
    LLMRequest,
)


async def test_claude():
    """Test Claude API with Indonesian text."""
    
    # Read API key from environment variable (secure)
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        print("   Run: export ANTHROPIC_API_KEY='your-key-here'")
        return
    
    # Create client with Claude as primary
    client = CloudLLMClient(
        primary_provider=LLMProvider.CLAUDE,
        fallback_providers=[LLMProvider.OPENAI],
    )
    
    try:
        # Test with Indonesian text
        request = LLMRequest(
            prompt="Apa ibukota Indonesia? Jawab dalam satu kata saja.",
            temperature=0.3,
            max_tokens=10,
        )
        
        print("Calling Claude API...")
        response = await client.generate(request)
        
        print(f"\n✅ Success!")
        print(f"Provider: {response.provider.value}")
        print(f"Model: {response.model}")
        print(f"Response: {response.text}")
        print(f"Input tokens: {response.input_tokens}")
        print(f"Output tokens: {response.output_tokens}")
        print(f"Cost: ${response.cost_usd:.6f}")
        print(f"Latency: {response.latency_seconds:.2f}s")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_claude())