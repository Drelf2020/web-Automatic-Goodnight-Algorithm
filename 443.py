from fastapi import FastAPI
from pywebio.input import *
from pywebio.output import *
from pywebio.platform.fastapi import webio_routes
from pywebio.session import eval_js, run_async, run_js
import uvicorn
from app import index, code, admin
app = FastAPI()
app.mount('/night', FastAPI(routes=webio_routes([index, code, admin])))

uvicorn.run(app, host="0.0.0.0", port=443, debug=True, ssl_keyfile='../api.nana7mi.link/api.nana7mi.link.key', ssl_certfile='../api.nana7mi.link/api.nana7mi.link_bundle.crt')
