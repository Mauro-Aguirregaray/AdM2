#!/bin/sh
sleep 10;
/usr/bin/mc config host add s3 http://s3:9000 ${MINIO_ACCESS_KEY:-minio} ${MINIO_SECRET_ACCESS_KEY:-minio123} --api S3v4;
if /usr/bin/mc ls s3/${MLFLOW_BUCKET_NAME:-mlflow} >/dev/null 2>&1; then
echo "Bucket mlflow ya existe.";
else
/usr/bin/mc mb s3/${MLFLOW_BUCKET_NAME:-mlflow};
/usr/bin/mc policy download s3/${MLFLOW_BUCKET_NAME:-mlflow};
fi;
if /usr/bin/mc ls s3/${DATA_REPO_BUCKET_NAME:-data} >/dev/null 2>&1; then
echo "Bucket data ya existe.";
else
/usr/bin/mc mb s3/${DATA_REPO_BUCKET_NAME:-data};
/usr/bin/mc policy download s3/${DATA_REPO_BUCKET_NAME:-data};
fi;
exit 0;
'