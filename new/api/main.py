from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import os
import uuid
from typing import Optional
import time

app = FastAPI(title="Chromium Pod Manager with Display", version="2.0.0")

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
    service_name: str
    status: str
    chromium_version: str
    namespace: str
    vnc_url: Optional[str] = None
    message: Optional[str] = None

# Only include versions we know exist (update this list based on what's actually downloaded)
AVAILABLE_VERSIONS = [
    "120.0.6099.109",
    "119.0.6045.105", 
    "117.0.5938.92",
    "112.0.5615.49",
    "111.0.5563.64",
    "108.0.5359.71",
    "105.0.5195.52",
    "102.0.5005.61"
]

def create_pod_manifest(chromium_version: str, namespace: str, pod_name: str):
    ecr_registry = os.environ.get('ECR_REGISTRY', 'your-account.dkr.ecr.us-east-1.amazonaws.com')
    
    return {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {
            "name": pod_name,
            "namespace": namespace,
            "labels": {
                "app": "chromium-runner",
                "pod-name": pod_name,  # Add specific pod name label
                "chromium-version": chromium_version.replace(".", "-")
            },
            "annotations": {
                "chromium-version": chromium_version
            }
        },
        "spec": {
            "initContainers": [{
                "name": "copy-chromium",
                "image": "busybox:latest",
                "command": ["/bin/sh"],
                "args": [
                    "-c",
                    f"echo 'Starting copy process...' && "
                    f"echo 'Checking for version {chromium_version}' && "
                    f"ls -la /mnt/source/ && "
                    f"if [ ! -d /mnt/source/{chromium_version} ]; then "
                    f"  echo 'ERROR: Version {chromium_version} not found!' && "
                    f"  echo 'Available versions:' && ls -1 /mnt/source/ && "
                    f"  exit 1; "
                    f"fi && "
                    f"echo 'Found version {chromium_version}, copying...' && "
                    f"cp -rv /mnt/source/{chromium_version}/* /mnt/dest/ && "
                    f"echo 'Setting permissions...' && "
                    f"chmod -R 755 /mnt/dest/ && "
                    f"if [ -f /mnt/dest/chrome ]; then "
                    f"  chmod +x /mnt/dest/chrome && "
                    f"  echo '✓ Chrome binary ready at /mnt/dest/chrome'; "
                    f"else "
                    f"  echo '⚠ Chrome binary not found, checking subdirectories...' && "
                    f"  find /mnt/dest -name chrome -type f && "
                    f"  exit 1; "
                    f"fi && "
                    f"echo '✓ Copy complete'"
                ],
                "volumeMounts": [
                    {
                        "name": "all-chromium-versions",
                        "mountPath": "/mnt/source",
                        "readOnly": True
                    },
                    {
                        "name": "chromium-runtime",
                        "mountPath": "/mnt/dest"
                    }
                ]
            }],
            "containers": [{
                "name": "chromium-vnc",
                "image": f"{ecr_registry}/chromium-vnc:latest",
                "imagePullPolicy": "Always",
                "ports": [
                    {"containerPort": 5900, "name": "vnc", "protocol": "TCP"},
                    {"containerPort": 6080, "name": "novnc", "protocol": "TCP"}
                ],
                "env": [
                    {"name": "CHROMIUM_VERSION", "value": chromium_version},
                    {"name": "DISPLAY", "value": ":99"}
                ],
                "volumeMounts": [{
                    "name": "chromium-runtime",
                    "mountPath": "/opt/chromium"
                }],
                "resources": {
                    "requests": {"memory": "1Gi", "cpu": "500m"},
                    "limits": {"memory": "4Gi", "cpu": "2000m"}
                }
            }],
            "volumes": [
                {
                    "name": "all-chromium-versions",
                    "persistentVolumeClaim": {"claimName": "chromium-versions-pvc"}
                },
                {
                    "name": "chromium-runtime",
                    "emptyDir": {"sizeLimit": "1Gi"}
                }
            ],
            "restartPolicy": "Never"
        }
    }

@app.get("/")
async def root():
    return {
        "service": "Chromium Pod Manager with Display",
        "version": "2.0.0",
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
    return {
        "available_versions": AVAILABLE_VERSIONS,
        "count": len(AVAILABLE_VERSIONS),
        "note": "These versions have been verified to exist in storage"
    }

@app.post("/pods", response_model=PodResponse)
async def create_pod(request: PodRequest):
    if request.chromium_version not in AVAILABLE_VERSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Version {request.chromium_version} not available. Available versions: {AVAILABLE_VERSIONS}"
        )
    
    pod_name = f"chromium-{request.chromium_version.replace('.', '-')}-{uuid.uuid4().hex[:8]}"
    service_name = f"{pod_name}-vnc"
    
    try:
        # Create pod
        pod_manifest = create_pod_manifest(request.chromium_version, request.namespace, pod_name)
        v1.create_namespaced_pod(namespace=request.namespace, body=pod_manifest)
        
        # Wait for pod to get its labels
        time.sleep(2)
        
        # Create service with specific pod selector
        service_manifest = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": service_name,
                "namespace": request.namespace,
                "labels": {
                    "app": "chromium-vnc-service"
                }
            },
            "spec": {
                "type": "LoadBalancer",
                "selector": {
                    "pod-name": pod_name  # Use specific pod name
                },
                "ports": [{
                    "name": "novnc",
                    "port": 80,
                    "targetPort": 6080,
                    "protocol": "TCP"
                }]
            }
        }
        
        v1.create_namespaced_service(namespace=request.namespace, body=service_manifest)
        
        return PodResponse(
            pod_name=pod_name,
            service_name=service_name,
            status="Creating",
            chromium_version=request.chromium_version,
            namespace=request.namespace,
            message=f"Pod and service created. Check status with GET /pods/{request.namespace}/{pod_name}"
        )
        
    except ApiException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create resources: {e.reason}. Error: {str(e)}"
        )

@app.get("/pods/{namespace}/{pod_name}")
async def get_pod_status(namespace: str, pod_name: str):
    try:
        pod = v1.read_namespaced_pod(name=pod_name, namespace=namespace)
        
        # Get init container logs if failed
        init_logs = None
        if pod.status.init_container_statuses:
            for init_status in pod.status.init_container_statuses:
                if init_status.state.terminated and init_status.state.terminated.exit_code != 0:
                    try:
                        init_logs = v1.read_namespaced_pod_log(
                            name=pod_name,
                            namespace=namespace,
                            container="copy-chromium"
                        )
                    except:
                        pass
        
        # Get service
        service_name = f"{pod_name}-vnc"
        vnc_url = None
        try:
            service = v1.read_namespaced_service(name=service_name, namespace=namespace)
            if service.status.load_balancer.ingress:
                lb_hostname = service.status.load_balancer.ingress[0].hostname
                vnc_url = f"http://{lb_hostname}/vnc.html"
            else:
                vnc_url = "LoadBalancer provisioning... (wait 2-3 minutes)"
        except:
            vnc_url = "Service not found or still creating"
        
        return {
            "pod_name": pod.metadata.name,
            "status": pod.status.phase,
            "chromium_version": pod.metadata.annotations.get("chromium-version", "unknown"),
            "created_at": str(pod.metadata.creation_timestamp),
            "pod_ip": pod.status.pod_ip,
            "vnc_url": vnc_url,
            "vnc_password": "chromium",
            "init_container_logs": init_logs if init_logs else "No errors"
        }
    except ApiException as e:
        raise HTTPException(status_code=404, detail=f"Pod not found: {e.reason}")

@app.delete("/pods/{namespace}/{pod_name}")
async def delete_pod(namespace: str, pod_name: str):
    try:
        # Delete service first
        service_name = f"{pod_name}-vnc"
        try:
            v1.delete_namespaced_service(name=service_name, namespace=namespace)
        except:
            pass
        
        # Delete pod
        v1.delete_namespaced_pod(name=pod_name, namespace=namespace)
        
        return {"message": f"Pod {pod_name} and service {service_name} deleted"}
    except ApiException as e:
        raise HTTPException(status_code=404, detail=f"Failed to delete: {e.reason}")

@app.get("/pods")
async def list_pods(namespace: str = "default"):
    try:
        pods = v1.list_namespaced_pod(namespace=namespace, label_selector="app=chromium-runner")
        
        pod_list = []
        for pod in pods.items:
            service_name = f"{pod.metadata.name}-vnc"
            vnc_url = None
            try:
                service = v1.read_namespaced_service(name=service_name, namespace=namespace)
                if service.status.load_balancer.ingress:
                    lb = service.status.load_balancer.ingress[0].hostname
                    vnc_url = f"http://{lb}/vnc.html"
                else:
                    vnc_url = "Provisioning..."
            except:
                vnc_url = "No service"
            
            pod_list.append({
                "name": pod.metadata.name,
                "status": pod.status.phase,
                "chromium_version": pod.metadata.annotations.get("chromium-version", "unknown"),
                "created_at": str(pod.metadata.creation_timestamp),
                "vnc_url": vnc_url
            })
        
        return {"count": len(pod_list), "pods": pod_list}
    except ApiException as e:
        raise HTTPException(status_code=500, detail=f"Failed to list pods: {e.reason}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
