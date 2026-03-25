from fastapi.middleware.cors import CORSMiddleware


class Cors:
    middleware_class = CORSMiddleware
    allow_origins = [
        "http://localhost:8000",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ]
    allow_credentials = True
    allow_methods = ["*"]
    allow_headers = ["*"]
