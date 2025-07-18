import uvicorn

def main():
    print("Hello from automatic-ppm-criterion-highlight-system!")


if __name__ == "__main__":
    main()
    uvicorn.run("app.app:app", host="0.0.0.0", port=8009, reload=True)
    
