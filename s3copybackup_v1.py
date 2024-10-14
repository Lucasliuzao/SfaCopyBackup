import boto3
import logging
from datetime import datetime

# Inicializando clientes S3 e SNS
s3 = boto3.client('s3')
sns = boto3.client('sns')

# ARN do SNS
sns_topic_arn = 'colocar arn do sns'  # Substitua pelo ARN do SNS

# Configurar logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    source_bucket = 'bucket de origem'
    source_prefix = 'pasta/'
    destination_bucket = 'backup de destino'
    destination_prefix = 'pasta/'
    
    # Nome base do arquivo que deve ser copiado
    file_prefix = 'nome do arquivo'
    
    # Mês vigente no formato YYYY/MM
    current_month = datetime.now().strftime('%Y/%m')
    logger.info(f"Mês vigente: {current_month}") #caso o arquivo contenha data

    try:
        # Listar arquivos no bucket de origem com o prefixo específico
        response = s3.list_objects_v2(Bucket=source_bucket, Prefix=source_prefix)
        
        if 'Contents' not in response:
            logger.info("Nenhum arquivo encontrado no bucket de origem para o mês corrente.")
            return {'statusCode': 404, 'body': "Nenhum arquivo encontrado no bucket de origem para o mês corrente."}

        # Filtrar arquivos que começam com "CorporeRM"
        files = [obj['Key'] for obj in response.get('Contents', []) if obj['Key'].startswith(f"{source_prefix}{file_prefix}")]
        
        if not files:
            logger.info("Nenhum arquivo correspondente encontrado no bucket de origem.")
            return {'statusCode': 404, 'body': "Nenhum arquivo correspondente encontrado no bucket de origem."}

        # Selecionar o arquivo mais recente
        latest_file = max(files)  # Usando max para pegar o arquivo mais recente
        logger.info(f"Arquivo mais recente encontrado: {latest_file}")

        # Definir a chave de destino
        destination_key = f"{destination_prefix}{current_month}/{latest_file.split('/')[-1]}"
        logger.info(f"Copiando arquivo para: {destination_key}")

        # Tentar copiar usando CopyObject
        try:
            s3.copy_object(
                CopySource={'Bucket': source_bucket, 'Key': latest_file},
                Bucket=destination_bucket,
                Key=destination_key
            )
            logger.info(f"Arquivo '{latest_file}' copiado com sucesso para '{destination_bucket}/{destination_key}'")
        except s3.exceptions.ClientError as e:
            # Se falhar devido ao tamanho, use multipart upload
            if e.response['Error']['Code'] == 'InvalidRequest':
                logger.warning(f"Erro ao usar CopyObject: {str(e)}. Tentando cópia multipart.")
                copy_multipart_file(latest_file, destination_bucket, destination_key)

        # Enviar notificação de sucesso
        message = f"O arquivo '{latest_file}' foi copiado com sucesso para '{destination_bucket}/{destination_key}'."
        subject = "Backup Copiado com Sucesso"
        sns.publish(TopicArn=sns_topic_arn, Message=message, Subject=subject)

        return {'statusCode': 200, 'body': message}

    except Exception as e:
        logger.error(f"Erro ao listar ou copiar os arquivos: {str(e)}")
        return {'statusCode': 500, 'body': f"Erro ao listar ou copiar os arquivos: {str(e)}"}

def copy_multipart_file(source_key, destination_bucket, destination_key):
    """Realiza a cópia multipart do arquivo."""
    try:
        # Iniciar o upload multipart
        multipart_upload = s3.create_multipart_upload(Bucket=destination_bucket, Key=destination_key)
        upload_id = multipart_upload['UploadId']
        parts = []
        
        part_size = 1024 * 1024 * 1024  # 100 MB (Ajustar conforme necessário)
        offset = 0
        
        # Obter o tamanho do arquivo de origem
        file_size = s3.head_object(Bucket='bucket de origem', Key=source_key)['ContentLength']
        logger.info(f"Tamanho do arquivo: {file_size} bytes. Iniciando cópia multipart.")
        
        while offset < file_size:
            end_range = min(offset + part_size, file_size) - 1
            logger.info(f"Copiando parte {len(parts) + 1}: bytes {offset}-{end_range}")
            
            # Ler parte do arquivo
            part = s3.get_object(Bucket='bucket de origem', Key=source_key, Range=f"bytes={offset}-{end_range}")
            data = part['Body'].read()

            # Enviar parte
            response = s3.upload_part(
                Bucket=destination_bucket,
                Key=destination_key,
                PartNumber=len(parts) + 1,
                UploadId=upload_id,
                Body=data
            )
            parts.append({'ETag': response['ETag'], 'PartNumber': len(parts) + 1})
            offset += part_size

        # Completar o upload multipart
        s3.complete_multipart_upload(Bucket=destination_bucket, Key=destination_key, UploadId=upload_id, MultipartUpload={'Parts': parts})
        logger.info(f"Cópia multipart do arquivo '{source_key}' concluída com sucesso para '{destination_key}'")
    
    except Exception as e:
        # Se houver um erro, cancelar o upload multipart
        s3.abort_multipart_upload(Bucket=destination_bucket, Key=destination_key, UploadId=upload_id)
        logger.error(f"Erro ao realizar a cópia multipart do arquivo '{source_key}': {str(e)}")
        raise

