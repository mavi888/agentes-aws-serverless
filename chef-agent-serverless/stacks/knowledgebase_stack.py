# knowledge_base_stack.py
import aws_cdk as cdk
from aws_cdk import Stack, CfnOutput, RemovalPolicy
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_deployment as s3deploy
from aws_cdk import aws_iam as iam
from aws_cdk import aws_bedrock as bedrock
from aws_cdk import aws_s3vectors as s3vectors
from constructs import Construct


class KnowledgeBaseStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. Bucket S3 para los documentos fuente
        docs_bucket = s3.Bucket(self, "ChefAgent1KBDocsBucket",
            bucket_name=f"chef-agent1-recetas-kb-docs-{self.account}",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # 2. Subir los documentos al bucket durante el deploy
        s3deploy.BucketDeployment(self, "ChefAgent1DeployDocs",
            sources=[s3deploy.Source.asset("./recetas")],
            destination_bucket=docs_bucket,
        )

        # 3. Vector Bucket (S3 Vectors) — almacena los embeddings
        vector_bucket_name = f"chef-agent1-vectors-{self.account}"
        vector_index_name = "chef-agent1-index"

        vector_bucket = s3vectors.CfnVectorBucket(self, "ChefAgent1VectorBucket",
            vector_bucket_name=vector_bucket_name,
        )

        # 4. Índice de vectores dentro del Vector Bucket
        #    Titan Embed Text v2 genera vectores de 1024 dimensiones
        vector_index = s3vectors.CfnIndex(self, "ChefAgent1VectorIndex",
            vector_bucket_name=vector_bucket_name,
            index_name=vector_index_name,
            data_type="float32",
            dimension=1024,           # dimensiones de Titan Embed Text v2
            distance_metric="cosine", # cosine es el estándar para búsqueda semántica
        )
        vector_index.add_dependency(vector_bucket)

        # 5. Rol IAM para la Knowledge Base
        kb_role = iam.Role(self, "ChefAgent1KBRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
            description="Rol para la Knowledge Base del agente asistente de cocina",
        )

        # Permiso para invocar el modelo de embeddings
        kb_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["bedrock:InvokeModel"],
            resources=[
                f"arn:aws:bedrock:{self.region}::foundation-model/amazon.titan-embed-text-v2:0"
            ],
        ))

        # Permiso para leer los documentos del bucket S3
        kb_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "s3:GetObject",
                "s3:ListBucket",
            ],
            resources=[
                docs_bucket.bucket_arn,
                f"{docs_bucket.bucket_arn}/*",
            ],
        ))

        # Permiso para leer/escribir en el Vector Bucket
        kb_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "s3vectors:GetIndex",
                "s3vectors:ListIndexes",
                "s3vectors:PutVectors",
                "s3vectors:GetVectors",
                "s3vectors:DeleteVectors",
                "s3vectors:QueryVectors",
                "s3vectors:ListVectors",
            ],
            resources=[
                f"arn:aws:s3vectors:{self.region}:{self.account}:bucket/{vector_bucket_name}",
                f"arn:aws:s3vectors:{self.region}:{self.account}:bucket/{vector_bucket_name}/index/*",
            ],
        ))

        # 6. Knowledge Base L1 con S3 Vectors
        # Necesitamos el rol IAM completamente creado antes de crear la KB
        # para evitar race condition en la propagación de permisos IAM
        self.kb = bedrock.CfnKnowledgeBase(self, "ChefAgent1SoporteKB",
            name="chef-agent1-kb",
            description="Knowledge Base agente asistente de cocina",
            role_arn=kb_role.role_arn,
            knowledge_base_configuration=bedrock.CfnKnowledgeBase.KnowledgeBaseConfigurationProperty(
                type="VECTOR",
                vector_knowledge_base_configuration=bedrock.CfnKnowledgeBase.VectorKnowledgeBaseConfigurationProperty(
                    embedding_model_arn=f"arn:aws:bedrock:{self.region}::foundation-model/amazon.titan-embed-text-v2:0",
                ),
            ),
            storage_configuration=bedrock.CfnKnowledgeBase.StorageConfigurationProperty(
                type="S3_VECTORS",
                s3_vectors_configuration=bedrock.CfnKnowledgeBase.S3VectorsConfigurationProperty(
                    vector_bucket_arn=f"arn:aws:s3vectors:{self.region}:{self.account}:bucket/{vector_bucket_name}",
                    index_arn=vector_index.attr_index_arn,
                ),
            ),
        )
        self.kb.add_dependency(vector_index)
        self.kb.add_dependency(kb_role.node.find_child("DefaultPolicy").node.default_child)

        # 7. Data source: S3 con chunking de tamaño fijo
        bedrock.CfnDataSource(self, "ChefAgent1DataSource",
            knowledge_base_id=self.kb.attr_knowledge_base_id,
            name="chef-agent-recetas-abuela",
            data_source_configuration=bedrock.CfnDataSource.DataSourceConfigurationProperty(
                type="S3",
                s3_configuration=bedrock.CfnDataSource.S3DataSourceConfigurationProperty(
                    bucket_arn=docs_bucket.bucket_arn,
                ),
            ),
            vector_ingestion_configuration=bedrock.CfnDataSource.VectorIngestionConfigurationProperty(
                chunking_configuration=bedrock.CfnDataSource.ChunkingConfigurationProperty(
                    chunking_strategy="FIXED_SIZE",
                    fixed_size_chunking_configuration=bedrock.CfnDataSource.FixedSizeChunkingConfigurationProperty(
                        max_tokens=300,
                        overlap_percentage=10,
                    ),
                ),
            ),
        )

        # Outputs
        CfnOutput(self, "ChefAgent1KnowledgeBaseId",
            value=self.kb.attr_knowledge_base_id,
            export_name="ChefAgent1KBId",
            description="ID de la Knowledge Base",
        )
        CfnOutput(self, "ChefAgent1KnowledgeBaseArn",
            value=self.kb.attr_knowledge_base_arn,
            export_name="ChefAgent1KBArn",
        )
        CfnOutput(self, "ChefAgent1DocsBucketName",
            value=docs_bucket.bucket_name,
        )

    @property
    def knowledge_base_id(self) -> str:
        return self.kb.attr_knowledge_base_id

    @property
    def knowledge_base_arn(self) -> str:
        return self.kb.attr_knowledge_base_arn
