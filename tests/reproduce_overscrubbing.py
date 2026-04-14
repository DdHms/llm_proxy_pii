import pytest
import os
import sys
import asyncio

# Add the root directory to the path so we can import proxy
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from proxy import scrub_text

@pytest.mark.asyncio
async def test_placeholder_corruption():
    # Setup: 'ON' is a common substring in many labels like 'LOCATION' or 'PERSON'
    import proxy
    proxy.DEFAULT_EXCLUSIONS = ["ON"]
    # We need a label that contains 'ON'
    # Presidio might return 'LOCATION' for 'London'
    
    text = "I am in London."
    
    # Mocking Presidio response is hard, so let's just use the current implementation's weakness.
    # If we replace 'London' with '<LOCATION_1>', then 'ON' is replaced inside it.
    
    # Actually, let's just test the word boundary issue first.
    proxy.DEFAULT_EXCLUSIONS = ["it"]
    text = "it is an iterator."
    scrubbed, mapping = await scrub_text(text)
    
    print(f"Scrubbed: {scrubbed}")
    # Current behavior: "sam is an samerator."
    assert "iterator" not in scrubbed, "Current behavior replaces it inside iterator"
    assert "samerator" in scrubbed

@pytest.mark.asyncio
async def test_sequential_corruption_repro():
    import proxy
    # 'London' -> <LOCATION_1> (if Presidio identifies it)
    # But we can force a label by using semantic mode and a name
    proxy.DEFAULT_EXCLUSIONS = ["ON"]
    proxy.SCRUBBING_MODE = "semantic"
    
    # We'll mock the mapping and counts to simulate a previous replacement
    # Or just use a text that will trigger a label containing 'ON'
    # 'LOCATION' or 'PERSON'
    
    text = "PERSON_NAME is in London."
    # If we can't easily trigger Presidio, let's just use a custom exclusion that contains 'ON'
    proxy.DEFAULT_EXCLUSIONS = ["London", "ON"]
    # 1. 'London' -> sam
    # 2. 'ON' -> altman
    # If 'ON' replaces inside 'sam', it becomes '<EXCLUSIaltman_1>'
    
    scrubbed, mapping = await scrub_text(text)
    print(f"Scrubbed overlap: {scrubbed}")
    print(f"Mapping: {mapping}")
    
    assert "<EXCLUSIaltman_1>" in scrubbed

if __name__ == "__main__":
    asyncio.run(test_placeholder_corruption())
    try:
        asyncio.run(test_sequential_corruption_repro())
    except AssertionError as e:
        print(f"Caught expected failure: {e}")
