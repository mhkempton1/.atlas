import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.google_service import google_service

def run():
    try:
        res1 = google_service.send_email("michael@daviselectric.biz", "Test Email", "This is a test")
        print("SEND RES:", res1)
    except Exception as e:
        print("SEND ERR:", repr(e))

    try:
        res2 = google_service.create_draft("michael@daviselectric.biz", "Test Draft", "This is a test draft")
        print("DRAFT RES:", res2)
    except Exception as e:
        print("DRAFT ERR:", repr(e))

if __name__ == '__main__':
    run()
