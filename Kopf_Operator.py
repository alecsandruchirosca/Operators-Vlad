import kopf
from kubernetes import client, config

# Configuring the Kubernetes client
config.load_kube_config()

@kopf.on.create('mycompany.com', 'v1', 'wordpresssites')
def create_fn(spec, **kwargs):
    name = kwargs.get('name')
    namespace = kwargs.get('namespace', 'default')

    # Data for MariaDB
    db_user = spec.get('dbUser')
    db_password = spec.get('dbPassword')
    db_name = spec.get('dbName')

    # Data for WordPress
    wp_image = spec.get('wpImage', 'wordpress:latest')

    # Create Secret for the database
    secret_data = {
        "username": base64.b64encode(db_user.encode()).decode(),
        "password": base64.b64encode(db_password.encode()).decode(),
    }
    secret = client.V1Secret(
        metadata=client.V1ObjectMeta(name=f"{name}-db-secret"),
        date=secret_date,
        type="Opaque",
    )

# Creating StatefulSet for MariaDB Galera
    create_mariadb_statefulset(namespace, name, db_user, db_password, db_name)

# Creating Deployment for WordPress
    create_wordpress_deployment(namespace, name, wp_image)


    client.CoreV1Api().create_namespaced_secret(namespace, secret)

    # Logic for creating the other resources (PVC, Deployment, Service, etc.)

def create_mariadb_statefulset(namespace, name, db_user, db_password, db_name):
    statefulset = V1StatefulSet(
        metadata=V1ObjectMeta(
            name=f"{name}-mariadb",
            namespace=namespace
        ),
        spec=V1StatefulSetSpec(
            serviceName=f"{name}-mariadb",
            replicas=3,
            selector={'matchLabels': {'app': f"{name}-mariadb"}},
            template=V1PodTemplateSpec(
                metadata=V1ObjectMeta(labels={'app': f"{name}-mariadb"}),
                spec={
                    'containers': [
                        V1Container(
                            name="mariadb",
                            image="mariadb:10.5",
                            ports=[V1ContainerPort(container_port=3306)],
                            env=[
                                V1EnvVar(name="MYSQL_ROOT_PASSWORD", value=db_password),
                                V1EnvVar(name="MYSQL_DATABASE", value=db_name),
                                V1EnvVar(name="MYSQL_USER", value=db_user),
                                V1EnvVar(name="MYSQL_PASSWORD", value=db_password)
                            ],
                            volumeMounts=[V1VolumeMount(mount_path="/var/lib/mysql", name="data")]
                        )
                    ]
                }
            ),
            volumeClaimTemplates=[
                V1PersistentVolumeClaim(
                    metadata=V1ObjectMeta(name="data"),
                    spec=V1PersistentVolumeClaimSpec(
                        accessModes=["ReadWriteOnce"],
                        resources=V1ResourceRequirements(
                            requests={"storage": "10Gi"}
                        )
                    )
                )
            ]
        )
    )
def create_wordpress_deployment(namespace, name, wp_image, db_name, db_user_secret_name):
    deployment = V1Deployment(
        metadata=V1ObjectMeta(name=f"{name}-wordpress", namespace=namespace),
        spec=V1DeploymentSpec(
            replicas=2,
            selector=V1LabelSelector(matchLabels={"app": f"{name}-wordpress"}),
            template=V1PodTemplateSpec(
                metadata=V1ObjectMeta(labels={"app": f"{name}-wordpress"}),
                spec={
                    'containers': [
                        V1Container(
                            name="wordpress",
                            image=wp_image,
                            ports=[V1ContainerPort(container_port=80)],
                            env=[
                                V1EnvVar(
                                    name="WORDPRESS_DB_HOST",
                                    value="mariadb-service:3306"
                                ),
                                V1EnvVar(
                                    name="WORDPRESS_DB_NAME",
                                    value=db_name
                                ),
                                V1EnvVar(
                                    name="WORDPRESS_DB_USER",
                                    valueFrom=V1EnvVarSource(
                                        secretKeyRef=V1SecretKeySelector(
                                            name=db_user_secret_name,
                                            key="username"
                                        )
                                    )
                                ),
                                V1EnvVar(
                                    name="WORDPRESS_DB_PASSWORD",
                                    valueFrom=V1EnvVarSource(
                                        secretKeyRef=V1SecretKeySelector(
                                            name=db_user_secret_name,
                                            key="password"
                                        )
                                    )
                                ),
                            ]
                        )
                    ]
                }
            )
        )
    )
    client.AppsV1Api().create_namespaced_deployment(namespace=namespace, body=deployment)


    return {'message': f"WordPress site '{name}' created with MariaDB Galera!"}

This basic example shows how to respond to creation events for custom resources such as wordpresssites under the mycompany.com group. When such a resource is created, the operator will initiate the creation of a Kubernetes secret to store the database credentials and proceed with the rest of the required resources.
