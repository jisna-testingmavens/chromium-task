from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import uuid
import os
from typing import Optional, List

app = FastAPI(title="Chromium Pod Manager", version="1.0.0")

# Load Kubernetes config
try:
    config.load_incluster_config()
except:
    config.load_kube_config()

v1 = client.CoreV1Api()

class PodRequest(BaseModel):
    chromium_version: str
    namespace: str = "default"

class PodResponse(BaseModel):
    pod_name: str
    status: str
    chromium_version: str
    namespace: str
    message: Optional[str] = None

AVAILABLE_VERSIONS = [
    "120.0.6099.109", "119.0.6045.105", "118.0.5993.70",
    "117.0.5938.92", "116.0.5845.96", "115.0.5790.102",
    "114.0.5735.90", "113.0.5672.63", "112.0.5615.49",
    "111.0.5563.64", "110.0.5481.77", "109.0.5414.74",
    "108.0.5359.71", "107.0.5304.62", "106.0.5249.61",
    "105.0.5195.52", "104.0.5112.79", "103.0.5060.53",
    "102.0.5005.61", "101.0.4951.41"
]

def create_pod_manifest(chromium_version: str, namespace: str, pod_name: str):
    return {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {
            "name": pod_name,
            "namespace": namespace,
            "labels": {
                "app": "chromium-runner",
                "chromium-version": chromium_version.replace(".", "-")
            }
        },
        "spec": {
            "containers": [{
                "name": "chromium",
                "image": f"{os.environ.get('ECR_REGISTRY', 'your-account.dkr.ecr.us-east-1.amazonaws.com')}/chromium-base:latest",
                "env": [{"name": "CHROMIUM_VERSION", "value": chromium_version}],
                "command": ["/bin/bash"],
                "args": ["-c", "while true; do sleep 30; done"],
                "volumeMounts": [{
                    "name": "chromium-versions",
                    "mountPath": "/opt/chromium-versions",
                    "readOnly": True
                }],
                "resources": {
                    "requests": {"memory": "512Mi", "cpu": "250m"},
                    "limits": {"memory": "2Gi", "cpu": "1000m"}
                }
            }],
            "volumes": [{
                "name": "chromium-versions",
                "persistentVolumeClaim": {"claimName": "chromium-versions-pvc"}
            }],
            "restartPolicy": "Never"
        }
    }

@app.get("/")
async def root():
    return {
        "service": "Chromium Pod Manager",
        "version": "1.0.0",
        "endpoints": {
            "versions": "/versions",
            "create_pod": "POST /pods",
            "list_pods": "/pods",
            "get_pod": "/pods/{namespace}/{pod_name}",
            "delete_pod": "DELETE /pods/{namespace}/{pod_name}"
        }
    }

@app.get("/versions")
async def list_versions():
    return {"available_versions": AVAILABLE_VERSIONS, "count": len(AVAILABLE_VERSIONS)}

@app.post("/pods", response_model=PodResponse)
async def create_pod(request: PodRequest):
    if request.chromium_version not in AVAILABLE_VERSIONS:
        raise HTTPException(status_code=400, detail=f"Version not available. Available: {AVAILABLE_VERSIONS}")
    
    pod_name = f"chromium-{request.chromium_version.replace('.', '-')}-{uuid.uuid4().hex[:8]}"
    
    try:
        pod_manifest = create_pod_manifest(request.chromium_version, request.namespace, pod_name)
        v1.create_namespaced_pod(namespace=request.namespace, body=pod_manifest)
        
        return PodResponse(
            pod_name=pod_name,
            status="Created",
            chromium_version=request.chromium_version,
            namespace=request.namespace,
            message=f"Pod {pod_name} created successfully"
        )
    except ApiException as e:
        raise HTTPException(status_code=500, detail=f"Failed to create pod: {e.reason}")

@app.get("/pods/{namespace}/{pod_name}")
async def get_pod_status(namespace: str, pod_name: str):
    try:
        pod = v1.read_namespaced_pod(name=pod_name, namespace=namespace)
        return {
            "pod_name": pod.metadata.name,
            "status": pod.status.phase,
            "chromium_version": pod.metadata.labels.get("chromium-version", "unknown"),
            "created_at": str(pod.metadata.creation_timestamp),
            "pod_ip": pod.status.pod_ip
        }
    except ApiException as e:
        raise HTTPException(status_code=404, detail=f"Pod not found: {e.reason}")

@app.delete("/pods/{namespace}/{pod_name}")
async def delete_pod(namespace: str, pod_name: str):
    try:
        v1.delete_namespaced_pod(name=pod_name, namespace=namespace)
        return {"message": f"Pod {pod_name} deleted successfully"}
    except ApiException as e:
        raise HTTPException(status_code=404, detail=f"Failed to delete pod: {e.reason}")

@app.get("/pods")
async def list_pods(namespace: str = "default"):
    try:
        pods = v1.list_namespaced_pod(namespace=namespace, label_selector="app=chromium-runner")
        return {
            "count": len(pods.items),
            "pods": [{
                "name": pod.metadata.name,
                "status": pod.status.phase,
                "chromium_version": pod.metadata.labels.get("chromium-version", "unknown"),
                "created_at": str(pod.metadata.creation_timestamp)
            } for pod in pods.items]
        }
    except ApiException as e:
        raise HTTPException(status_code=500, detail=f"Failed to list pods: {e.reason}")

if __name__ == "__main__":
    import uvicorn
    import os
    uvicorn.run(app, host="0.0.0.0", port=8000)
