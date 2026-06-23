"""
Groq API & OCR Diagnostic Test
Run: python test_groq_ocr.py
"""
import asyncio
import base64
import os
import sys

if sys.stdout.encoding != "utf-8":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
SEP = "=" * 60


async def test_api_key():
    """Test 1: Is the Groq API key valid?"""
    import httpx

    print(f"\n{'─'*60}")
    print("TEST 1: Groq API Key Check")
    print(f"{'─'*60}")

    if not GROQ_API_KEY:
        print("[FAIL] GROQ_API_KEY is empty in .env!")
        print("       OCR will use MOCK data instead of real parsing.")
        return False

    print(f"[OK]   Key present: {GROQ_API_KEY[:12]}...")

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": VISION_MODEL,
        "messages": [{"role": "user", "content": [{"type": "text", "text": "Reply with just: OK"}]}],
        "max_tokens": 10,
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
            )
        if r.status_code == 200:
            reply = r.json()["choices"][0]["message"]["content"]
            print(f"[OK]   API reachable. Model reply: {reply.strip()}")
            return True
        elif r.status_code == 401:
            print(f"[FAIL] API key is INVALID or expired (401 Unauthorized)")
            print(f"       Response: {r.text[:200]}")
            return False
        elif r.status_code == 429:
            print(f"[WARN] Rate limit hit (429). Key is valid but quota exceeded.")
            return True  # Key is valid, just rate limited
        else:
            print(f"[FAIL] Unexpected status: {r.status_code}")
            print(f"       Response: {r.text[:300]}")
            return False
    except Exception as e:
        print(f"[FAIL] Network error: {e}")
        return False


async def test_vision_model():
    """Test 2: Does the vision model accept image input?"""
    import httpx

    print(f"\n{'─'*60}")
    print("TEST 2: Vision Model (Image Parsing)")
    print(f"{'─'*60}")

    # Create a tiny 1x1 white PNG in memory (valid image, minimal size)
    tiny_png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
        b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18"
        b"\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    img_b64 = base64.standard_b64encode(tiny_png).decode()

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": VISION_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{img_b64}"},
                    },
                    {"type": "text", "text": "What color is this image? Reply in 5 words max."},
                ],
            }
        ],
        "max_tokens": 20,
        "temperature": 0.1,
    }

    try:
        print(f"[INFO] Sending tiny test image to {VISION_MODEL}...")
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
            )
        if r.status_code == 200:
            reply = r.json()["choices"][0]["message"]["content"]
            print(f"[OK]   Vision model working! Reply: {reply.strip()}")
            return True
        elif r.status_code == 400:
            data = r.json()
            print(f"[FAIL] Vision model rejected request (400)")
            print(f"       Error: {data.get('error', {}).get('message', r.text[:200])}")
            return False
        elif r.status_code == 429:
            print(f"[WARN] Rate limited (429) - model is available but quota hit")
            return True
        else:
            print(f"[FAIL] Status {r.status_code}: {r.text[:300]}")
            return False
    except Exception as e:
        print(f"[FAIL] Error calling vision model: {e}")
        return False


async def test_ocr_service_import():
    """Test 3: Can the OCR service module be imported cleanly?"""
    print(f"\n{'─'*60}")
    print("TEST 3: OCR Service Module Import")
    print(f"{'─'*60}")
    try:
        # Add backend to path
        sys.path.insert(0, os.path.dirname(__file__))
        from app.services.ocr import parse_timetable_image, _VISION_MODEL, _OCR_TIMEOUT
        print(f"[OK]   Module imported successfully")
        print(f"[INFO] Vision model : {_VISION_MODEL}")
        print(f"[INFO] OCR timeout  : {_OCR_TIMEOUT}s")
        return True
    except Exception as e:
        print(f"[FAIL] Import error: {e}")
        return False


def check_test_image():
    """Test 4: Check if there is a test image to try."""
    print(f"\n{'─'*60}")
    print("TEST 4: Test Image Available?")
    print(f"{'─'*60}")

    candidates = [
        os.path.join(os.path.dirname(__file__), "test.jpg"),
        os.path.join(os.path.dirname(__file__), "..", "test-timetable.jpg"),
    ]
    for path in candidates:
        if os.path.exists(path) and os.path.getsize(path) > 100:
            print(f"[OK]   Found: {path}  ({os.path.getsize(path)} bytes)")
            return path

    print("[INFO] No test image found (test.jpg is only 5 bytes / placeholder).")
    print("       To test real OCR: place a real timetable JPEG at backend/test.jpg")
    return None


async def test_real_ocr(image_path: str):
    """Test 5: Run full OCR pipeline on real image."""
    print(f"\n{'─'*60}")
    print("TEST 5: Full OCR Pipeline")
    print(f"{'─'*60}")
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        from app.services.ocr import parse_timetable_image
        with open(image_path, "rb") as f:
            data = f.read()
        print(f"[INFO] Running OCR on {image_path} ({len(data)} bytes)...")
        result = await parse_timetable_image(data)
        if result["success"]:
            print(f"[OK]   OCR succeeded!")
            print(f"[INFO] Entries extracted : {len(result['entries'])}")
            print(f"[INFO] Text length       : {len(result['extracted_text'])} chars")
            if result["entries"]:
                print(f"[INFO] First entry       : {result['entries'][0]}")
        else:
            print(f"[FAIL] OCR returned success=False")
            print(f"       Errors: {result['errors']}")
    except Exception as e:
        print(f"[FAIL] OCR pipeline error: {e}")


async def main():
    print(SEP)
    print("  GROQ API & OCR DIAGNOSTIC")
    print(SEP)

    key_ok = await test_api_key()

    if key_ok:
        await test_vision_model()
    else:
        print("\n[SKIP] Skipping vision model test — API key issue")

    await test_ocr_service_import()

    img = check_test_image()
    if img and key_ok:
        await test_real_ocr(img)
    elif not key_ok:
        print(f"\n{'─'*60}")
        print("TEST 5: Full OCR Pipeline")
        print(f"{'─'*60}")
        print("[SKIP] No valid API key — OCR will return MOCK data")

    print(f"\n{SEP}")
    print("  DIAGNOSIS COMPLETE")
    print(SEP)
    if not key_ok:
        print("""
PROBLEM IDENTIFIED: Groq API key issue
-----------------------------------------
Current key in .env starts with: """ + (GROQ_API_KEY[:15] + "..." if GROQ_API_KEY else "EMPTY") + """

SOLUTIONS:
  1. Get a free key at: https://console.groq.com
  2. Update .env:  GROQ_API_KEY=gsk_your_new_key_here
  3. Restart the backend server
""")
    else:
        print("""
Groq API is connected. If OCR still fails:
  - Check image size (< 4MB recommended)
  - Check image format (JPEG/PNG/WEBP)
  - Check backend logs for detailed errors
  - Rate limits: free tier = 30 req/min
""")


if __name__ == "__main__":
    asyncio.run(main())
