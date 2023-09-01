import kopf
import kubernetes.client
from kubernetes.client.rest import ApiException
import yaml

@kopf.on.create('assessment.com', 'v1', 'projects')
def create_fn(spec, **kwargs):
    name = kwargs["body"]["metadata"]["name"]
    
    print("Name is %s\n" % name)
    # Create the deployment spec
    doc = yaml.safe_load(f"""
        apiVersion: apps/v1
        kind: Deployment
        metadata:
          name: {name}-deployment
          labels:
            app: {name}
        spec:
          replicas: {spec.get('replicas', 1)}
          selector:
            matchLabels:
              app: {name}
          template:
            metadata:
              labels:
                app: {name}
            spec:
              containers:
              - name: webapp
                image: webapp_4:latest
                ports:
                - containerPort: 5001
                imagePullPolicy: IfNotPresent

              - name: mongo
                image: mongo:latest
                imagePullPolicy: IfNotPresent 

                volumeMounts:
                - name: storage
                  mountPath: /data/db
              
              volumes:
              - name: storage
                persistentVolumeClaim:
                   claimName: mongo-pvc

    """)

    # Make it our child: assign the namespace, name, labels, owner references, etc.
    kopf.adopt(doc)

    # Actually create an object by requesting the Kubernetes API.
    api = kubernetes.client.AppsV1Api()
    try:
      depl = api.create_namespaced_deployment(namespace=doc['metadata']['namespace'], body=doc)
      # Update the parent's status.
      return {'children': [depl.metadata.uid]}
    except ApiException as e:
      print("Exception when calling AppsV1Api->create_namespaced_deployment: %s\n" % e)


@kopf.on.update('assessment.com', 'v1', 'projects')
def update_fn(spec, name, **kwargs):
    size = spec.get('size', None)
    if not size:
        raise kopf.PermanentError(f"Size must be set. Got {size!r}.")
    doc = yaml.safe_load(f"""

        apiVersion: v1
        kind: PersistentVolumeClaim
        metadata:
           name: mongo-pvc 
           #annotations:
           #     volume.beta.kubernetes.io/storage-class: standard
        spec:
          accessModes:
             - ReadWriteOnce
          resources:
            requests:
              storage: "{size}"           
    """)
    
    kopf.adopt(doc)

    # Actually patch an object by requesting the Kubernetes API.
    api = kubernetes.client.CoreV1Api()

    try:
      depl = api.patch_namespaced_persistent_volume_claim(name='mongo-pvc', namespace='default', body=doc)
      # Update the parent's status.
      return {'children': [depl.metadata.uid]}
    except ApiException as e:
      print("Exception when calling CoreV1Api->patch_namespaced_persistent_volume_claim: %s\n" % e)
