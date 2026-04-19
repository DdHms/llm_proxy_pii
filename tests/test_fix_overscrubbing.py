import pytest
import os
import sys
import asyncio

# Add the root directory to the path so we can import proxy
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from proxy import scrub_text

@pytest.mark.asyncio
async def test_word_boundary_fixed():
    import proxy
    proxy.DEFAULT_EXCLUSIONS = ["it"]
    text = "it is an iterator."
    scrubbed, mapping = await scrub_text(text)
    
    print(f"Scrubbed: {scrubbed}")
    # Should replace 'it' but NOT 'it' inside 'iterator'
    assert "sam" in scrubbed
    assert "iterator" in scrubbed
    assert "samerator" not in scrubbed

@pytest.mark.asyncio
async def test_placeholder_corruption_fixed():
    import proxy
    # 'London' contains 'ON'. If we exclude both, 'London' should be replaced but 'ON' should not corrupt the placeholder.
    proxy.DEFAULT_EXCLUSIONS = ["London", "ON"]
    text = "I am in London."
    
    scrubbed, mapping = await scrub_text(text)
    print(f"Scrubbed: {scrubbed}")
    print(f"Mapping: {mapping}")
    
    # 'London' -> sam
    # 'ON' inside 'London' is skipped because it overlaps.
    assert "sam" in scrubbed
    assert "altman" not in scrubbed
    
    # Let's add a separate 'ON'
    text = "I am in London, ON duty."
    scrubbed, mapping = await scrub_text(text)
    print(f"Scrubbed with separate ON: {scrubbed}")
    # "I am in sam, altman duty."
    assert "sam" in scrubbed
    assert "altman" in scrubbed
    # Ensure no double nesting like <EXCLUSIaltman_1>
    assert "<EXCLUSI<" not in scrubbed
    
if __name__ == "__main__":
    asyncio.run(test_word_boundary_fixed())
    asyncio.run(test_placeholder_corruption_fixed())
