import boto3
from datetime import datetime

s3 = boto3.client('s3')
sns = boto3.client('sns')

# ARN do tópico do SNS criado
sns_topic_arn = 'arn:aws:sns:us-east-1:942569085084:BucketCopyCorporeRM'  # Substitua pelo ARN do seu tópico SNS

def lambda_handler(event, context):
    source_bucket = 'sfacopytest1'
    destination_bucket = 'sfacopytest2'
    source_prefixes = ['teste1/', 'teste2/', 'teste3/']  # Prefixos das pastas dentro do bucket de origem
    
    latest_object = None

    try:
        for prefix in source_prefixes:
            # Listar os objetos no bucket de origem com o prefixo especificado
            objects = s3.list_objects_v2(Bucket=source_bucket, Prefix=prefix)
            
            if 'Contents' in objects:
                # Encontrar o objeto mais recente na pasta especificada
                most_recent_in_prefix = max(objects['Contents'], key=lambda x: x['LastModified'])
                
                if latest_object is None or most_recent_in_prefix['LastModified'] > latest_object['LastModified']:
                    latest_object = most_recent_in_prefix
        
        if latest_object:
            try:
                # Verificar se o objeto já foi copiado para o bucket de destino
                s3.head_object(Bucket=destination_bucket, Key=latest_object['Key'])
                # Se o objeto já existe, notificar que o backup já foi feito
                message = f"O backup '{latest_object['Key']}' já existe no bucket {destination_bucket}. Nenhuma ação necessária."
                subject = "Backup Já Existente"
                sns.publish(TopicArn=sns_topic_arn, Message=message, Subject=subject)
                return {
                    'statusCode': 200,
                    'body': message
                }
            except s3.exceptions.ClientError as e:
                if e.response['Error']['Code'] == '404':
                    # Objeto não encontrado, continuar com a cópia
                    pass
                else:
                    # Outro erro ocorreu
                    raise

            # Copiar o objeto para o bucket de destino mantendo o mesmo caminho
            s3.copy_object(
                CopySource={
                    'Bucket': source_bucket,
                    'Key': latest_object['Key']
                },
                Bucket=destination_bucket,
                Key=latest_object['Key']  # Mantém o mesmo nome e caminho no bucket de destino
            )
            
            # Enviar notificação de sucesso por email
            message = f"O último backup '{latest_object['Key']}' foi copiado com sucesso para {destination_bucket}."
            subject = "Backup Copiado com Sucesso"
            sns.publish(TopicArn=sns_topic_arn, Message=message, Subject=subject)
            
            return {
                'statusCode': 200,
                'body': message
            }
        else:
            # Caso nenhum objeto tenha sido encontrado em todas as pastas
            return {
                'statusCode': 200,
                'body': "Nenhum objeto encontrado nas pastas especificadas do bucket de origem."
            }

    except Exception as e:
        # Em caso de erro, enviar notificação de falha por email
        error_message = f"Erro ao copiar o backup para {destination_bucket}: {str(e)}"
        error_subject = "Erro ao Copiar Backup"
        sns.publish(TopicArn=sns_topic_arn, Message=error_message, Subject=error_subject)
        
        return {
            'statusCode': 500,
            'body': error_message
        }
