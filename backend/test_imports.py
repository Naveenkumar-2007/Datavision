try:
    print("Step 1: Importing aiohttp...")
    import aiohttp
    print(f"Success aiohttp version: {aiohttp.__version__}")
    
    print("Step 2: Importing litellm...")
    import litellm
    print(f"Success litellm version: {litellm.version if hasattr(litellm, 'version') else 'unknown'}")
    
    print("Step 3: Importing supabase...")
    import supabase
    print("Success supabase")
    
    print("Step 4: Checking aiohttp attributes...")
    try:
        print(f"Has ConnectionTimeoutError: {hasattr(aiohttp, 'ConnectionTimeoutError')}")
        from aiohttp import ConnectionTimeoutError
        print("Successfully imported ConnectionTimeoutError")
    except ImportError:
        print("FAILED to import ConnectionTimeoutError from aiohttp")
    except AttributeError:
        print("AttributeError accessing ConnectionTimeoutError")

except Exception as e:
    print(f"CRASH during imports: {e}")
    import traceback
    traceback.print_exc()
