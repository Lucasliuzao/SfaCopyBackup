#!/bin/bash

# Definir variáveis
SOURCE_BUCKET="sfacopytest1"
DESTINATION_BUCKET="sfacopytest3"
FILE_NAME="Glue.png"
SNS_TOPIC_ARN="arn:aws:sns:us-east-1:942569085084:BackupNotification" # Substitua pelo seu ARN do SNS

# Definir as URLs completas
SOURCE_FILE="s3://$SOURCE_BUCKET/$FILE_NAME"
DESTINATION_FILE="s3://$DESTINATION_BUCKET/$FILE_NAME"

# Copiar o arquivo
aws s3 cp "$SOURCE_FILE" "$DESTINATION_FILE"

# Verificar se a cópia foi bem-sucedida
if [ $? -eq 0 ]; then
    echo "Arquivo '$FILE_NAME' copiado com sucesso de '$SOURCE_BUCKET' para '$DESTINATION_BUCKET'."
    # Enviar notificação de sucesso
    aws sns publish --topic-arn "$SNS_TOPIC_ARN" --subject "Backup bem-sucedido" --message "O arquivo '$FILE_NAME' foi copiado com sucesso para o bucket de destino."
else
    echo "Erro ao copiar o arquivo."
    # Enviar notificação de falha
    aws sns publish --topic-arn "$SNS_TOPIC_ARN" --subject "Falha no backup" --message "Erro ao copiar o arquivo '$FILE_NAME'."
    exit 1
fi

# Encerrar a instância
aws ec2 stop-instances --instance-ids "$(curl -s http://169.254.169.254/latest/meta-data/instance-id)"
