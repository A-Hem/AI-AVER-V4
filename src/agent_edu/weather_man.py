import httpx
import redis.asyncio as redis

OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3"

from tamper_tools import check_metadata, analyze_prnu

# Note the new 'redis_client' parameter
async def metadata_agent(http_client, redis_client, file_path):
    """An agent specializing in metadata interpretation."""
    
    # --- NEW: Consult the subconscious ---
    memory_key = f"file_context:{file_path}"
    retrieved_memory = await redis_client.get(memory_key)
    if not retrieved_memory:
        retrieved_memory = "No prior context found."
    
    # --- NEW: Inject context into the prompt ---
    prompt = f"""
    Here is the prior context for '{file_path}': "{retrieved_memory}"

    Based on this context, what metadata fields are most critical for tamper detection?
    Think step-by-step.
    """
    
    response = await http_client.post(OLLAMA_API_URL, json={"model": MODEL_NAME, "prompt": prompt, "stream": False})
    
    print(f"METADATA AGENT THOUGHT (with injected context): {response.json()['response']}")
    
    tool_result = check_metadata(file_path)
    return tool_result

# Note the new 'redis_client' parameter
async def prnu_agent(http_client, redis_client, file_path):
    """An agent specializing in PRNU analysis."""
    
    # --- NEW: Consult the subconscious ---
    memory_key = f"file_context:{file_path}"
    retrieved_memory = await redis_client.get(memory_key)
    if not retrieved_memory:
        retrieved_memory = "No prior context found."

    # --- NEW: Inject context into the prompt ---
    prompt = f"""
    Given this prior knowledge about '{file_path}': "{retrieved_memory}"

    How should this knowledge affect my PRNU analysis strategy? For example, should I be more suspicious of certain artifacts?
    """

    response = await http_client.post(OLLAMA_API_URL, json={"model": MODEL_NAME, "prompt": prompt, "stream": False})
    
    print(f"PRNU AGENT THOUGHT (with injected context): {response.json()['response']}")
    
    tool_result = analyze_prnu(file_path, region="full")
    return tool_result
