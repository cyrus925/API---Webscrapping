import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from src.app import get_application

app = get_application()


# Rediriger le root endpoint vers Swagger UI
@app.get("/", include_in_schema=False)
async def redirect_to_docs():
    return RedirectResponse(url="/docs")



if __name__ == "__main__":
    uvicorn.run("main:app", debug=True, reload=True, port=8081)
