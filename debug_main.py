"""
Debug main file
"""

import sys
import traceback

try:
    print("=== App Starting ===")
    
    print("1. Importing modules...")
    from core.chat_application import ChatApplication
    print("OK: ChatApplication imported")
    
    print("2. Creating app instance...")
    app = ChatApplication()
    print("OK: App instance created")
    
    print("3. Running application...")
    app.run()
    print("OK: App run completed")
    
except ImportError as e:
    print(f"IMPORT ERROR: {e}")
    print("Detailed traceback:")
    traceback.print_exc()
    input("Press Enter to exit...")
    
except AttributeError as e:
    print(f"ATTRIBUTE ERROR: {e}")
    print("Detailed traceback:")
    traceback.print_exc()
    input("Press Enter to exit...")
    
except Exception as e:
    print(f"GENERAL ERROR: {e}")
    print("Detailed traceback:")
    traceback.print_exc()
    input("Press Enter to exit...")
    
finally:
    print("=== App Finished ===")