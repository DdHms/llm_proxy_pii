import pytest
import os
import sys
from fastapi.testclient import TestClient

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import proxy
from proxy import app

client = TestClient(app)

def test_get_config():
    response = client.get("/api/config")
    assert response.status_code == 200
    data = response.json()
    assert "exclusions" in data
    assert isinstance(data["exclusions"], list)

def test_add_and_remove_exclusion():
    # 1. Add exclusion
    phrase = "LiveExclusionTestPhrase"
    response = client.post("/api/exclusions", json={"phrase": phrase})
    assert response.status_code == 200
    assert response.json()["phrase"] == phrase
    
    # Verify it's in config
    response = client.get("/api/config")
    assert phrase in response.json()["exclusions"]
    
    # 2. Test scrubbing with the new exclusion
    import asyncio
    async def check_scrub():
        scrubbed, mapping = await proxy.scrub_text(f"Hello {phrase}")
        return scrubbed
    
    # Since scrub_text is async, we run it
    loop = asyncio.get_event_loop()
    scrubbed = loop.run_until_complete(check_scrub())
    assert "LiveExclusionTestPhrase" not in scrubbed
    assert "<EXCLUSION_1>" in scrubbed

    # 3. Remove exclusion
    response = client.delete(f"/api/exclusions/{phrase}")
    assert response.status_code == 200
    
    # Verify it's gone from config
    response = client.get("/api/config")
    assert phrase not in response.json()["exclusions"]
    
    # 4. Verify no longer scrubbed
    scrubbed = loop.run_until_complete(check_scrub())
    assert phrase in scrubbed
