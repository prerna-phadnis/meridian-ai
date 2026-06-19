# meridian-ai/test_gemini.py
# Run this to verify Gemini is working
# python test_gemini.py

from src.lib.gemini import generate_text, generate_text_with_system

# Test 1: Basic generation
print("Testing basic generation...")

result = generate_text("Say hello in one sentence")

print(f"✅ Basic: {result}")

# Test 2: JSON mode
print("\nTesting JSON mode...")

result = generate_text(
    'Return JSON: {"status": "ok", "message": "working"}',
    json_mode=True
)

print(f"✅ JSON: {result}")

# Test 3: System prompt
print("\nTesting system prompt...")

result = generate_text_with_system(
    system_prompt="You are a helpful assistant. Be very brief.",
    user_prompt="What is machine learning?"
)

print(f"✅ System: {result}")

print("\n✅ All Gemini tests passed!")