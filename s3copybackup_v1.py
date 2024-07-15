import boto3
from datetime import datetime

s3 = boto3.client('s3')
sns = boto3.client('sns')

# ARN do tópico do SNS criado
sns_topic_arn = 'arn:aws:sns:us-east-1:Substitua pelo ARN do seu tópico SNS'  # Substitua pelo ARN do seu tópico SNS

def lambda_handler(event, context):
    source_bucket = 'sfacopytest1'
    destination_bucket = 'sfacopytest2'
    source_prefix = 'teste/'
    
    # Listar os objetos no bucket de origem
    objects = s3.list_objects_v2(Bucket=source_bucket, Prefix=source_prefix)
    
    if 'Contents' in objects:
        # Encontrar o objeto mais recente
        latest_object = max(objects['Contents'], key=lambda x: x['LastModified'])
        
        copy_source = {
            'Bucket': source_bucket,
            'Key': latest_object['Key']
        }
        
        try:
            # Copiar o objeto para o bucket de destino
            s3.copy_object(
                CopySource=copy_source,
                Bucket=destination_bucket,
                Key=latest_object['Key']
            )
            
            # Enviar notificação de sucesso por email
            message = f"O último backup '{latest_object['Key']}' foi copiado com sucesso para {destination_bucket}."
            subject = "Backup Copiado com Sucesso"
            sns.publish(TopicArn=sns_topic_arn, Message=message, Subject=subject)
            
            return {
                'statusCode': 200,
                'body': message
            }
        
        except Exception as e:
            # Em caso de erro, enviar notificação de falha por email
            error_message = f"Erro ao copiar o backup '{latest_object['Key']}' para {destination_bucket}: {str(e)}"
            error_subject = "Erro ao Copiar Backup"
            sns.publish(TopicArn=sns_topic_arn, Message=error_message, Subject=error_subject)
            
            return {
                'statusCode': 500,
                'body': error_message
            }
    
    else:
        return {
            'statusCode': 200,
            'body': "Nenhum objeto encontrado no bucket de origem."
        }
