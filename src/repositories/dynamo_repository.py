# --------------------------------------------------
# repositories/dynamo_repository.py
# --------------------------------------------------
# Repositório responsável por salvar e recuperar dados no DynamoDB
#
# Em termo de aprendizado:
# - Aqui conectamos a aplicação com um banco NoSQL na AWS
# - Mostra conhecimento prático de DynamoDB (muito usado em projetos serveless)
# - Segregamos "infra" da "lógica de negócio" (boa prática de arquitetura)
#
# Na prática:
# - Cada requisição processada em /generate será salva no DynamoDB
# - Depois podemos consultar histórico por usuário ou por request_id
# --------------------------------------------------

import boto3
import logging
from typing import Dict, Any, Optional
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from src.config import settings

try:
    from moto import mock_aws as mock_dynamodb
except ImportError:
    mock_dynamodb = None

log = logging.getLogger("awsProject.dynamo")

class DynamoRepository:
    """
    Repositório de persistência em DynamoDB
    - Cada item é identificado por 'pk' (partition key)
    - Usamos `user_id` como chave primária + `request_id` com sort key
    - Isso permite listar facilmente o histórico de prompts por usuário
    - Se ENV=dev → usa `moto` para simulação local
    - Se ENV=prod → usa DynamoDB real
    """

    def __init__(self):
        """
        Inicializa o  cliente apontando para DynamoDB
        - Pode ser AWS real ou DynamoDB Local (via settings.DYNAMO_ENDPOINT)
        """
        if settings.ENV == "dev":
            if not mock_dynamodb:
                raise RuntimeError("Moto não está instalado — necessário para rodar em modo dev/test")
            log.info("Iniciando DynamoDB simulado em moto")
            self.mock = mock_dynamodb()
            self.mock.start()
            self.dynamo = boto3.resource("dynamodb", region_name="us-east-1")
            self._ensure_table()
        else:
            log.info("Conectando ao DynamoDB real")
            self.dynamo = boto3.resource(
                "dynamodb",
                endpoint_url=settings.DYNAMO_ENDPOINT,
                region_name="us-east-1", # default (mock), pode vir do settings também
                aws_access_key_id="fake", # credenciais fake para rodar local
                aws_secret_access_key="fake"
            )
        
        self.table = self.dynamo.Table(settings.DYNAMO_TABLE)
    
    def _ensure_table(self):
        """
        Cria tabela automaticamente se não existir (apenas em dev)
        """
        existing_tables = self.dynamo.meta.client.list_tables()["TableNames"]
        if settings.DYNAMO_TABLE not in existing_tables:
            self.dynamo.create_table(
                TableName=settings.DYNAMO_TABLE,
                KeySchema=[
                    {"AttributeName": "user_id", "KeyType": "HASH"},
                    {"AttributeName": "request_id", "KeyType": "RANGE"},
                ],
                AttributeDefinitions=[
                    {"AttributeName": "user_id", "AttributeType": "S"},
                    {"AttributeName": "request_id", "AttributeType": "S"},
                ],
                BillingMode="PAY_PER_REQUEST",
            )
            log.info("Tabela %s criada (simulada)", settings.DYNAMO_TABLE)

    def save_item(self, user_id: str, request_id: str, prompt: str, response: Dict[str, Any]) -> None:
        """
        Salva no DynamoDB um histórico de geração
        - user_id → quem fez a chamada
        - request_id → identificador único (permite buscar depois)
        - prompt → entrada original do usuário
        - response → saída gerada (JSON serializável)
        """

        item = {
            "user_id": user_id,
            "request_id": request_id,
            "prompt": prompt,
            "response": response
        }
        try:
            self.table.put_item(Item=item)
            log.info("Saved request_id=%s user_id=%s into DynamoDB", request_id, user_id)
        except ClientError as e:
            log.error("DynamoDB put_item error: %s", e)
            raise

    def get_item(self, user_id: str, request_id: str) -> Optional[Dict[str, Any]]:
        """
        Recupera um item específico (usuário + request_id)
        - Útil para reprocessar ou debugar chamadas antigas
        """
        try:
            resp = self.table.get_item(
                Key={
                    "user_id": user_id,
                    "request_id": request_id
                }
            )
            return resp.get("Item")
        except ClientError as e:
            log.error("DynamoDB get_item error: %s", e)
            return None
        
    def list_items(self, user_id: str) -> list[Dict[str, Any]]:
        """
        Lista todo histórico de prompts de um usuário
        - Exemplo: usuário quer ver últimos 10 prompts enviados
        - Útil em dashboards e debugging
        """
        try:
            resp = self.table.query(
                KeyConditionExpression=Key("user_id").eq(user_id)
            )
            return resp.get("Items", [])
        except ClientError as e:
            log.error("DynamoDB query error: %s", e)
            return []