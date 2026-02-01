import uvicorn

if __name__ == "__main__":
    uvicorn.run("core.app:app", host="127.0.0.1", port=4201, reload=True)
