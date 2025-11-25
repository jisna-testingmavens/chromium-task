from fastapi import FastAPI
from pydantic import BaseModel
from kubernetes import client, config
import os
import time
import base64
import hmac
import hashlib
import json
import requests

app = FastAPI()

# Load in-cluster config OR local kubeconfig
try:
    config.load_incluster_config()
except:
    config.load_kube_config()

NAMESPACE = os.getenv("NAMESPACE", "guac")
GUI_IMAGE = os.getenv("GUI_IMAGE")
GUAC_SECRET_HEX = os.getenv("GUAC_SECRET_HEX")
GUAC_HOST = os.getenv("GUAC_HOST")   # http://guacamole.guac.svc.cluster.local:8080

apps = client.AppsV1Api()
core = client.CoreV1Api()


class CreateRequest(BaseModel):
    name: str


def sign_token(payload: dict, secret_hex: str):
    header = {"alg": "HS256", "typ": "JWT"}
    key = bytes.fromhex(secret_hex)

    b64 = lambda x: base64.urlsafe_b64encode(json.dumps(x).encode()).rstrip(b"=")
    segments = [b64(header), b64(payload)]
    signing_input = b".".join(segments)
    signature = hmac.new(key, signing_input, hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).rstrip(b"=")
    return (signing_input + b"." + sig_b64).decode()


@app.post("/create")
def create_pod(req: CreateRequest):
    name = req.name.lower()

    # 1. Create Service
    svc_name = f"svc-gui-{name}"
    service = client.V1Service(
        metadata=client.V1ObjectMeta(name=svc_name),
        spec=client.V1ServiceSpec(
            selector={"app": name},
            ports=[client.V1ServicePort(port=5900, target_port=5900)],
        ),
    )
    core.create_namespaced_service(namespace=NAMESPACE, body=service)

    # 2. Create StatefulSet
    ss_name = f"gui-{name}"
    container = client.V1Container(
        name="gui",
        image=GUI_IMAGE,
        ports=[client.V1ContainerPort(container_port=5900)],
    )
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"app": name}),
        spec=client.V1PodSpec(containers=[container]),
    )
    spec = client.V1StatefulSetSpec(replicas=1, service_name=svc_name, selector={"matchLabels": {"app": name}}, template=template)
    sts = client.V1StatefulSet(metadata=client.V1ObjectMeta(name=ss_name), spec=spec)

    apps.create_namespaced_stateful_set(namespace=NAMESPACE, body=sts)

    # 3. Wait 2–3 seconds for pod start
    time.sleep(3)

    # 4. Build connection token
    payload = {
        "username": name,
        "expires": int(time.time()) + 3600,
        "connections": {
            f"conn-{name}": {
                "protocol": "vnc",
                "parameters": {
                    "hostname": svc_name,
                    "port": "5900",
                }
            }
        }
    }
    token = sign_token(payload, GUAC_SECRET_HEX)

    full_url = f"{GUAC_HOST}/guacamole/#/?token={token}"

    return {
        "message": "Pod + Service created",
        "guacamole_url": full_url,
        "service": svc_name,
        "statefulset": ss_name
    }

