#!/bin/bash
# Código para copiar arquivo específico no S3
SOURCE_BUCKET="storage-gw-sql"
DESTINATION_BUCKET="sfacopytest1"
FILE_PREFIX="CorporeRM"
CURRENT_DATE=$(date +"%Y%m01")
FILE_NAME="${FILE_PREFIX}_${CURRENT_DATE}_0700.bak"
SNS_TOPIC_ARN="arn:aws:sns:us-east-1:942569085084:BucketCopyCorporeRM" # Trocar pelo ARN do seu SNS
INSTANCE_ID="i-12937128371" # Substituir pelo ID da instância

# Função para parar a instância EC2
stop_instance() {
    aws ec2 stop-instances --instance-ids "$INSTANCE_ID"
    if [ $? -eq 0 ]; then
        echo "Instância '$INSTANCE_ID' parada com sucesso."
    else
        echo "Erro ao parar a instância '$INSTANCE_ID'."
    fi
}

# Comando para copiar o arquivo
aws s3 cp "s3://$SOURCE_BUCKET/Backup SFA/$FILE_NAME" "s3://$DESTINATION_BUCKET/Backup SFA Mensal/$FILE_NAME"

# Verificar se a cópia foi bem-sucedida
if [ $? -eq 0 ]; then
    echo "Arquivo '$FILE_NAME' copiado com sucesso de '$SOURCE_BUCKET' para '$DESTINATION_BUCKET'."
    
    # Tentar enviar notificação de sucesso via SNS
    aws sns publish --topic-arn "$SNS_TOPIC_ARN" --message "Arquivo '$FILE_NAME' copiado com sucesso." --subject "Backup realizado com sucesso."
    
    if [ $? -ne 0 ]; then
        echo "Erro ao enviar notificação de sucesso via SNS."
    fi
    
    # Parar a instância EC2 após sucesso
    stop_instance

else
    echo "Erro ao copiar o arquivo."
    
    # Tentar enviar notificação de falha via SNS
    aws sns publish --topic-arn "$SNS_TOPIC_ARN" --message "Erro ao copiar o arquivo '$FILE_NAME'." --subject "Falha ao realizar o backup."
    
    if [ $? -ne 0 ]; then
        echo "Erro ao enviar notificação de falha via SNS."
    fi
    
    # Aguardar 10 minutos antes de parar a instância
    echo "Aguardando 10 minutos para análise antes de parar a instância..."
    sleep 600 # 600 segundos = 10 minutos
    
    # Parar a instância EC2 após falha
    stop_instance
    exit 1
fi
