#!/bin/bash
#Código para copiar arquivo específico no S3
SOURCE_BUCKET="storage-gw-sql"
DESTINATION_BUCKET="sfacopytest1"
FILE_PREFIX="CorporeRM"
CURRENT_DATE=$(date +"%Y%m01")
FILE_NAME="${FILE_PREFIX}_${CURRENT_DATE}_0700.bak"
SNS_TOPIC_ARN="arn:aws:sns:us-east-1:942569085084:BucketCopyCorporeRM" #trocar pelo arn do seu sns

# Comando para copiar o arquivo
aws s3 cp "s3://$SOURCE_BUCKET/Backup SFA/$FILE_NAME" "s3://$DESTINATION_BUCKET/Backup SFA Mensal/$FILE_NAME"
if [$? -eq 0]; then
    echo "Arquivo '$FILE_NAME' copiado com sucesso de '$SOURCE_BUCKET' para '$DESTINATION_BUCKET'."
    aws sns publish --topic-arn "$SNS_TOPIC_ARN" --subject "Backup realizado com sucesso."

#Parte do código para parar a instância EC2
INSTANCE_ID="i-12937128371" #Substituir pelo ID da instância
aws ec2 stop_instances --instance-ids "INSTANCE_ID"

if [$? -eq 0]; then
    echo "Instância '#INSTANCE_ID' parada com sucesso."
else
    echo "Erro ao parar a instância '$INSTANCE_ID'."
  fi
else
  echo "Erro ao copiar o arquivo."
  aws sns publish --topic-arn "$SNS_TOPIC_ARN" --subject "Falha ao realizar o backup."
  exit 1
fi
