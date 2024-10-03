#!/bin/bash
#Código para copiar arquivo específico no S3
SOURCE_BUCKET="storage-gw-sql"
DESTINATION_BUCKET="storage-sql-us-east-1"
FILE_PREFIX="CorporeRM"
CURRENT_DATE=$(date +"%Y%m01")
FILE_NAME="${FILE_PREFIX}_${CURRENT_DATE}_0700.bak"

# Comando para copiar o arquivo
aws s3 cp "s3://$SOURCE_BUCKET/Backup SFA/$FILE_NAME" "s3://$DESTINATION_BUCKET/Backup SFA Mensal/$FILE_NAME"
