from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uuid
import traceback

from services.LDhap import calculate_hap


api_app = FastAPI()
app = FastAPI()
app.mount('/api', api_app)
app.mount('/', StaticFiles(directory="../client/LDlink", html=True), name="LDlink")

origins = [
    "*"
]

api_app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@api_app.get("/ping")
async def ping():
    return {"message": True}

# @app.get("/api/ldhap")
@api_app.get('/LDlinkRest/ldhap')
@api_app.get('/LDlinkRest2/ldhap')
@api_app.get('/LDlinkRestWeb/ldhap')
async def ldhap(
    snps: str = "rs3%0Ars4", 
    pop: str = "YRI", 
    genome_build: str = "grch37", 
    token: Optional[str] = None
):
    try:
        request_id = str(uuid.uuid1())
        print({
            "message": "reached ldhap",
            "snps": snps,
            "pop": pop,
            "request_id": request_id,
            "genome_build": genome_build,
            "token": token
        })
        out_json = calculate_hap(snps, pop, request_id, True, genome_build)
        return out_json
    except Exception as e:
        exc_obj = e
        raise HTTPException(status_code=400, detail="Internal server error: %s" % ''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))