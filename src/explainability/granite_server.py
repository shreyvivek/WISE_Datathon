"""Granite note server. Runs INSIDE the provided LinuxONE JupyterLab container (llama.cpp built with zDNN).
stdlib-only HTTP so it needs nothing beyond llama_cpp. Usage: python granite_server.py [port]
POST /note  {facts: {...}}  -> {text, gen_ms, n_tokens}      GET /health -> model info + load time"""
import json, sys, time
from http.server import BaseHTTPRequestHandler, HTTPServer
from llama_cpp import Llama

MODEL = "/home/ibm-user/granite-4.0-h-350m-base-be.f16.gguf"
t0 = time.perf_counter()
llm = Llama(model_path=MODEL, n_ctx=2048, n_batch=256, n_threads=3, n_gpu_layers=0, verbose=False)  # zDNN offload measured slower for this model
LOAD_S = time.perf_counter() - t0
sys.path.insert(0, "/home/ibm-user/secondlook")


class H(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        b = json.dumps(obj).encode(); self.send_response(code); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        self._send(200, {"model": MODEL.split("/")[-1], "load_s": round(LOAD_S, 2), "n_ctx": 2048})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        from src.explainability.reviewer_notes import build_prompt
        s = time.perf_counter()
        out = llm.create_completion(prompt=build_prompt(body["facts"]), temperature=0, max_tokens=110, stop=["\n", "FACTS:"])
        self._send(200, {"text": out["choices"][0]["text"].strip(), "gen_ms": round((time.perf_counter() - s) * 1e3, 1),
                         "n_tokens": out["usage"]["completion_tokens"]})

    def log_message(self, *a):  # keep request contents out of logs
        pass


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", int(sys.argv[1]) if len(sys.argv) > 1 else 8001), H).serve_forever()
