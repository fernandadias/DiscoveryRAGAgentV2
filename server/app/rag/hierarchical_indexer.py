"""
Módulo de indexação hierárquica para o Discovery RAG Agent V2.

Este módulo implementa técnicas avançadas de indexação em dois níveis (documento e chunk)
para melhorar a qualidade da recuperação e permitir consultas mais contextualizadas.
"""

import uuid
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import weaviate
from weaviate.util import generate_uuid5
from openai import AsyncOpenAI


class HierarchicalIndexer:
    """
    Implementa indexação hierárquica em dois níveis (documento e chunk).
    
    Características:
    - Indexação de documentos completos com embeddings de nível superior
    - Indexação de chunks com embeddings detalhados
    - Vinculação bidirecional entre documentos e chunks
    - Metadados enriquecidos para filtragem e classificação
    """
    
    def __init__(
        self,
        weaviate_client,
        openai_client: Optional[AsyncOpenAI] = None,
        embedding_model: str = "text-embedding-3-small",
        document_class: str = "Document",
        chunk_class: str = "Chunk"
    ):
        """
        Inicializa o indexador hierárquico.
        
        Args:
            weaviate_client: Cliente Weaviate inicializado
            openai_client: Cliente OpenAI para geração de embeddings
            embedding_model: Modelo de embedding a ser utilizado
            document_class: Nome da classe Weaviate para documentos
            chunk_class: Nome da classe Weaviate para chunks
        """
        self.vector_db = weaviate_client
        self.openai_client = openai_client or AsyncOpenAI()
        self.embedding_model = embedding_model
        self.document_class = document_class
        self.chunk_class = chunk_class
        
    async def setup_schema(self):
        """
        Configura o schema do Weaviate para documentos e chunks.
        """
        # Verificar se as classes já existem
        schema = self.vector_db.schema.get()
        existing_classes = [c["class"] for c in schema["classes"]] if "classes" in schema else []
        
        # Configurar classe de documentos se não existir
        if self.document_class not in existing_classes:
            document_class_obj = {
                "class": self.document_class,
                "description": "Document class for hierarchical indexing",
                "vectorizer": "none",  # Usaremos embeddings personalizados
                "properties": [
                    {
                        "name": "title",
                        "dataType": ["text"],
                        "description": "Document title"
                    },
                    {
                        "name": "summary",
                        "dataType": ["text"],
                        "description": "Document summary or abstract"
                    },
                    {
                        "name": "source",
                        "dataType": ["text"],
                        "description": "Source of the document"
                    },
                    {
                        "name": "type",
                        "dataType": ["text"],
                        "description": "Type of document (product_guidelines, design_guidelines, etc.)"
                    },
                    {
                        "name": "category",
                        "dataType": ["text"],
                        "description": "Category of the document"
                    },
                    {
                        "name": "author",
                        "dataType": ["text"],
                        "description": "Author of the document"
                    },
                    {
                        "name": "created_at",
                        "dataType": ["date"],
                        "description": "Creation date of the document"
                    },
                    {
                        "name": "tags",
                        "dataType": ["text[]"],
                        "description": "Tags associated with the document"
                    }
                ]
            }
            self.vector_db.schema.create_class(document_class_obj)
        
        # Configurar classe de chunks se não existir
        if self.chunk_class not in existing_classes:
            chunk_class_obj = {
                "class": self.chunk_class,
                "description": "Chunk class for hierarchical indexing",
                "vectorizer": "none",  # Usaremos embeddings personalizados
                "properties": [
                    {
                        "name": "text",
                        "dataType": ["text"],
                        "description": "Chunk text content"
                    },
                    {
                        "name": "title",
                        "dataType": ["text"],
                        "description": "Section title for the chunk"
                    },
                    {
                        "name": "document_id",
                        "dataType": ["text"],
                        "description": "ID of the parent document"
                    },
                    {
                        "name": "document_title",
                        "dataType": ["text"],
                        "description": "Title of the parent document"
                    },
                    {
                        "name": "position",
                        "dataType": ["number"],
                        "description": "Relative position in the document (0-1)"
                    },
                    {
                        "name": "type",
                        "dataType": ["text"],
                        "description": "Type of document (product_guidelines, design_guidelines, etc.)"
                    },
                    {
                        "name": "category",
                        "dataType": ["text"],
                        "description": "Category of the document"
                    },
                    {
                        "name": "tags",
                        "dataType": ["text[]"],
                        "description": "Tags associated with the document"
                    }
                ]
            }
            self.vector_db.schema.create_class(chunk_class_obj)
    
    async def index_document(
        self, 
        document: Dict[str, Any], 
        chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Indexa um documento e seus chunks no Weaviate.
        
        Args:
            document: Dicionário contendo o documento
            chunks: Lista de chunks do documento
            
        Returns:
            Dicionário com IDs do documento e chunks indexados
        """
        # 1. Criar resumo do documento para embedding de documento
        doc_summary = self._create_document_summary(document)
        
        # 2. Gerar embedding para o documento completo
        doc_embedding = await self._generate_embedding(doc_summary)
        
        # 3. Indexar documento no nível superior
        doc_id = await self._index_document_entry(document, doc_embedding)
        
        # 4. Gerar embeddings para todos os chunks
        chunk_texts = [chunk["text"] for chunk in chunks]
        chunk_embeddings = await self._generate_embeddings_batch(chunk_texts)
        
        # 5. Indexar cada chunk e vinculá-lo ao documento pai
        chunk_ids = []
        for i, chunk in enumerate(chunks):
            chunk_with_embedding = chunk.copy()
            chunk_with_embedding["embedding"] = chunk_embeddings[i]
            chunk_with_embedding["document_id"] = doc_id
            
            # Adicionar metadados do documento ao chunk
            if "metadata" not in chunk_with_embedding:
                chunk_with_embedding["metadata"] = {}
                
            chunk_with_embedding["metadata"]["document_id"] = doc_id
            chunk_with_embedding["metadata"]["document_title"] = document.get("title", "")
            
            # Herdar tipo e categoria do documento
            if "type" not in chunk_with_embedding["metadata"] and "type" in document:
                chunk_with_embedding["metadata"]["type"] = document["type"]
                
            if "category" not in chunk_with_embedding["metadata"] and "category" in document:
                chunk_with_embedding["metadata"]["category"] = document["category"]
            
            chunk_id = await self._index_chunk_entry(chunk_with_embedding)
            chunk_ids.append(chunk_id)
        
        # 6. Atualizar documento com referências aos chunks
        await self._update_document_with_chunks(doc_id, chunk_ids)
        
        return {
            "document_id": doc_id,
            "chunk_ids": chunk_ids,
            "chunks_count": len(chunks)
        }
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """
        Gera embedding para um texto usando a API OpenAI.
        
        Args:
            text: Texto para gerar embedding
            
        Returns:
            Lista de floats representando o embedding
        """
        response = await self.openai_client.embeddings.create(
            model=self.embedding_model,
            input=text
        )
        return response.data[0].embedding
    
    async def _generate_embeddings_batch(
        self, 
        texts: List[str], 
        batch_size: int = 100
    ) -> List[List[float]]:
        """
        Gera embeddings para múltiplos textos em lotes.
        
        Args:
            texts: Lista de textos para gerar embeddings
            batch_size: Tamanho do lote para requisições à API
            
        Returns:
            Lista de embeddings
        """
        all_embeddings = []
        
        # Processar em lotes para evitar limites de API
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            response = await self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=batch
            )
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
            
        return all_embeddings
    
    def _create_document_summary(self, document: Dict[str, Any]) -> str:
        """
        Cria um resumo representativo do documento inteiro.
        
        Args:
            document: Documento a ser resumido
            
        Returns:
            Texto de resumo para embedding de documento
        """
        title = document.get("title", "")
        content = document.get("content", "")
        
        # Versão simples: título + primeiros 1000 caracteres
        summary = f"{title}\n\n"
        
        # Adicionar metadados relevantes ao resumo
        if "type" in document:
            summary += f"Type: {document['type']}\n"
            
        if "category" in document:
            summary += f"Category: {document['category']}\n"
            
        if "tags" in document and document["tags"]:
            tags = ", ".join(document["tags"]) if isinstance(document["tags"], list) else document["tags"]
            summary += f"Tags: {tags}\n"
            
        # Adicionar conteúdo
        summary += f"\n{content[:1000]}"
        if len(content) > 1000:
            summary += "..."
            
        return summary
    
    async def _index_document_entry(
        self, 
        document: Dict[str, Any], 
        embedding: List[float]
    ) -> str:
        """
        Indexa um documento no Weaviate.
        
        Args:
            document: Documento a ser indexado
            embedding: Embedding do documento
            
        Returns:
            ID do documento indexado
        """
        # Gerar UUID consistente se o documento tiver ID
        if "id" in document:
            doc_uuid = generate_uuid5(document["id"])
        else:
            doc_uuid = str(uuid.uuid4())
        
        # Preparar propriedades do documento
        properties = {
            "title": document.get("title", ""),
            "summary": self._create_document_summary(document),
            "source": document.get("source", ""),
            "type": document.get("type", ""),
            "category": document.get("category", ""),
            "author": document.get("author", ""),
            "created_at": document.get("created_at", ""),
            "tags": document.get("tags", [])
        }
        
        # Remover propriedades vazias
        properties = {k: v for k, v in properties.items() if v}
        
        # Indexar no Weaviate
        self.vector_db.data_object.create(
            properties,
            self.document_class,
            doc_uuid,
            vector=embedding
        )
        
        return doc_uuid
    
    async def _index_chunk_entry(self, chunk: Dict[str, Any]) -> str:
        """
        Indexa um chunk no Weaviate.
        
        Args:
            chunk: Chunk a ser indexado
            
        Returns:
            ID do chunk indexado
        """
        # Gerar UUID consistente se o chunk tiver ID
        if "id" in chunk:
            chunk_uuid = generate_uuid5(chunk["id"])
        else:
            chunk_uuid = str(uuid.uuid4())
        
        # Extrair metadados
        metadata = chunk.get("metadata", {})
        
        # Preparar propriedades do chunk
        properties = {
            "text": chunk["text"],
            "title": metadata.get("section_title", ""),
            "document_id": metadata.get("document_id", ""),
            "document_title": metadata.get("document_title", ""),
            "position": metadata.get("position", 0),
            "type": metadata.get("type", ""),
            "category": metadata.get("category", ""),
            "tags": metadata.get("tags", [])
        }
        
        # Remover propriedades vazias
        properties = {k: v for k, v in properties.items() if v}
        
        # Indexar no Weaviate
        self.vector_db.data_object.create(
            properties,
            self.chunk_class,
            chunk_uuid,
            vector=chunk["embedding"]
        )
        
        return chunk_uuid
    
    async def _update_document_with_chunks(
        self, 
        doc_id: str, 
        chunk_ids: List[str]
    ) -> None:
        """
        Atualiza um documento com referências aos seus chunks.
        
        Args:
            doc_id: ID do documento
            chunk_ids: Lista de IDs dos chunks
        """
        # No Weaviate, podemos usar referências cruzadas
        # Mas isso requer configuração adicional no schema
        # Por enquanto, mantemos apenas a referência do chunk para o documento
        pass
    
    async def delete_document(self, document_id: str) -> Dict[str, Any]:
        """
        Remove um documento e todos os seus chunks do índice.
        
        Args:
            document_id: ID do documento a ser removido
            
        Returns:
            Resultado da operação
        """
        # 1. Buscar todos os chunks associados ao documento
        result = self.vector_db.query.get(
            self.chunk_class, 
            ["id"]
        ).with_where({
            "path": ["document_id"],
            "operator": "Equal",
            "valueString": document_id
        }).do()
        
        # 2. Remover cada chunk
        chunks_deleted = 0
        if "data" in result and "Get" in result["data"] and self.chunk_class in result["data"]["Get"]:
            chunks = result["data"]["Get"][self.chunk_class]
            for chunk in chunks:
                self.vector_db.data_object.delete(
                    self.chunk_class,
                    chunk["id"]
                )
                chunks_deleted += 1
        
        # 3. Remover o documento
        self.vector_db.data_object.delete(
            self.document_class,
            document_id
        )
        
        return {
            "document_id": document_id,
            "chunks_deleted": chunks_deleted,
            "success": True
        }


class EnhancedRetriever:
    """
    Implementa recuperação avançada em duas fases com reranking.
    
    Características:
    - Recuperação inicial baseada em similaridade vetorial
    - Reranking para melhorar a relevância dos resultados
    - Filtragem por tipo, categoria e outros metadados
    - Suporte a consultas híbridas (documento + chunks)
    """
    
    def __init__(
        self,
        weaviate_client,
        openai_client: Optional[AsyncOpenAI] = None,
        embedding_model: str = "text-embedding-3-small",
        document_class: str = "Document",
        chunk_class: str = "Chunk"
    ):
        """
        Inicializa o recuperador avançado.
        
        Args:
            weaviate_client: Cliente Weaviate inicializado
            openai_client: Cliente OpenAI para geração de embeddings e reranking
            embedding_model: Modelo de embedding a ser utilizado
            document_class: Nome da classe Weaviate para documentos
            chunk_class: Nome da classe Weaviate para chunks
        """
        self.vector_db = weaviate_client
        self.openai_client = openai_client or AsyncOpenAI()
        self.embedding_model = embedding_model
        self.document_class = document_class
        self.chunk_class = chunk_class
    
    async def retrieve(
        self, 
        query: str, 
        filters: Optional[Dict[str, Any]] = None, 
        top_k: int = 20, 
        rerank_top_k: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Recupera chunks relevantes para uma consulta.
        
        Args:
            query: Consulta do usuário
            filters: Filtros adicionais (tipo, categoria, etc.)
            top_k: Número de resultados iniciais a recuperar
            rerank_top_k: Número de resultados após reranking
            
        Returns:
            Lista de chunks relevantes com metadados
        """
        # 1. Gerar embedding para a consulta
        query_embedding = await self._generate_embedding(query)
        
        # 2. Fase 1: Recuperação inicial
        initial_results = await self._initial_retrieval(query, query_embedding, filters, top_k)
        
        # 3. Fase 2: Reranking
        reranked_results = await self._rerank_results(query, initial_results)
        
        # 4. Selecionar os top_k resultados após reranking
        final_results = reranked_results[:rerank_top_k]
        
        return final_results
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """
        Gera embedding para um texto usando a API OpenAI.
        
        Args:
            text: Texto para gerar embedding
            
        Returns:
            Lista de floats representando o embedding
        """
        response = await self.openai_client.embeddings.create(
            model=self.embedding_model,
            input=text
        )
        return response.data[0].embedding
    
    async def _initial_retrieval(
        self, 
        query: str, 
        query_embedding: List[float], 
        filters: Optional[Dict[str, Any]], 
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Realiza a recuperação inicial baseada em similaridade vetorial.
        
        Args:
            query: Consulta do usuário
            query_embedding: Embedding da consulta
            filters: Filtros adicionais
            top_k: Número de resultados a recuperar
            
        Returns:
            Lista de resultados iniciais
        """
        # Construir filtros para o Weaviate
        where_filter = None
        if filters:
            where_filter = {}
            
            if "type" in filters:
                where_filter = {
                    "path": ["type"],
                    "operator": "Equal",
                    "valueString": filters["type"]
                }
            
            if "category" in filters:
                category_filter = {
                    "path": ["category"],
                    "operator": "Equal",
                    "valueString": filters["category"]
                }
                
                # Combinar filtros se necessário
                if "type" in filters:
                    where_filter = {
                        "operator": "And",
                        "operands": [where_filter, category_filter]
                    }
                else:
                    where_filter = category_filter
        
        # Buscar chunks similares
        response = self.vector_db.query.get(
            self.chunk_class, 
            ["text", "title", "document_id", "document_title", "position", "type", "category"]
        ).with_near_vector({
            "vector": query_embedding
        }).with_where(where_filter).with_limit(top_k).with_additional(["score"]).do()
        
        # Extrair resultados
        results = []
        if "data" in response and "Get" in response["data"] and self.chunk_class in response["data"]["Get"]:
            chunks = response["data"]["Get"][self.chunk_class]
            
            for chunk in chunks:
                # Buscar informações do documento pai
                parent_doc = await self._get_parent_document(chunk["document_id"])
                
                results.append({
                    "text": chunk["text"],
                    "title": chunk.get("title", ""),
                    "document_title": chunk.get("document_title", parent_doc.get("title", "")),
                    "document_source": parent_doc.get("source", ""),
                    "type": chunk.get("type", parent_doc.get("type", "")),
                    "category": chunk.get("category", parent_doc.get("category", "")),
                    "position": chunk.get("position", 0),
                    "similarity_score": chunk.get("_additional", {}).get("score", 0)
                })
        
        return results
    
    async def _get_parent_document(self, doc_id: str) -> Dict[str, Any]:
        """
        Busca informações do documento pai.
        
        Args:
            doc_id: ID do documento
            
        Returns:
            Informações do documento
        """
        response = self.vector_db.query.get(
            self.document_class, 
            ["title", "summary", "source", "type", "category", "author"]
        ).with_id(doc_id).do()
        
        if "data" in response and "Get" in response["data"] and self.document_class in response["data"]["Get"]:
            return response["data"]["Get"][self.document_class][0]
        
        return {}
    
    async def _rerank_results(
        self, 
        query: str, 
        initial_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Reordena os resultados usando LLM para melhorar a relevância.
        
        Args:
            query: Consulta do usuário
            initial_results: Resultados da recuperação inicial
            
        Returns:
            Resultados reordenados por relevância
        """
        # Se não houver resultados, retornar lista vazia
        if not initial_results:
            return []
        
        # Preparar prompt para o LLM
        prompt = f"""
        Avalie a relevância de cada trecho para a consulta: "{query}"
        
        Atribua uma pontuação de 0 a 10 para cada trecho, onde:
        - 10: Extremamente relevante, responde diretamente à consulta
        - 7-9: Muito relevante, contém informações importantes relacionadas
        - 4-6: Moderadamente relevante, tem alguma relação com a consulta
        - 1-3: Pouco relevante, tem relação tangencial
        - 0: Irrelevante, não tem relação com a consulta
        
        Responda apenas com a lista de pontuações, uma por linha, sem explicações.
        """
        
        # Adicionar cada trecho ao prompt
        for i, result in enumerate(initial_results):
            prompt += f"\n\nTrecho {i+1}:\n{result['text'][:300]}..."
        
        # Obter pontuações do LLM
        response = await self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        
        # Extrair pontuações
        scores_text = response.choices[0].message.content.strip()
        scores = []
        
        for line in scores_text.split('\n'):
            try:
                score = float(line.strip())
                scores.append(score)
            except ValueError:
                # Ignorar linhas que não são números
                pass
        
        # Garantir que temos pontuações para todos os resultados
        if len(scores) < len(initial_results):
            # Preencher com zeros se faltarem pontuações
            scores.extend([0] * (len(initial_results) - len(scores)))
        
        # Combinar pontuações com resultados
        for i, result in enumerate(initial_results):
            if i < len(scores):
                result["rerank_score"] = scores[i]
                # Combinar com a pontuação de similaridade vetorial
                result["combined_score"] = 0.3 * result["similarity_score"] + 0.7 * (scores[i] / 10)
            else:
                result["rerank_score"] = 0
                result["combined_score"] = 0.3 * result["similarity_score"]
        
        # Ordenar por pontuação combinada
        reranked_results = sorted(initial_results, key=lambda x: x["combined_score"], reverse=True)
        
        return reranked_results
