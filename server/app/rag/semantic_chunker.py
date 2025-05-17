"""
Módulo de chunking semântico otimizado para o Discovery RAG Agent V2.

Este módulo implementa técnicas avançadas de chunking semântico com tamanho reduzido
e sobreposição para melhorar a qualidade da recuperação de informações.
"""

import re
import uuid
import tiktoken
from typing import List, Dict, Any, Optional, Tuple


class SemanticChunker:
    """
    Implementa chunking semântico com tamanho controlado e sobreposição.
    
    Características:
    - Respeita fronteiras semânticas (parágrafos, seções)
    - Tamanho de chunk configurável (padrão: 300-500 tokens)
    - Sobreposição configurável (padrão: 15-20%)
    - Preservação de metadados e contexto
    """
    
    def __init__(
        self, 
        max_tokens: int = 400, 
        overlap_tokens: int = 60,
        model: str = "cl100k_base"
    ):
        """
        Inicializa o chunker semântico.
        
        Args:
            max_tokens: Número máximo de tokens por chunk
            overlap_tokens: Número de tokens de sobreposição entre chunks
            model: Modelo de tokenização (compatível com tiktoken)
        """
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self.tokenizer = tiktoken.get_encoding(model)
        
    def chunk_document(
        self, 
        document: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Divide um documento em chunks semânticos.
        
        Args:
            document: Dicionário contendo o documento com campos:
                - id: Identificador único do documento
                - title: Título do documento
                - content: Conteúdo textual do documento
                - metadata: Metadados adicionais (opcional)
                
        Returns:
            Lista de chunks com metadados
        """
        # Extrair informações do documento
        doc_id = document.get("id", str(uuid.uuid4()))
        title = document.get("title", "")
        content = document.get("content", "")
        metadata = document.get("metadata", {})
        
        # Dividir o documento em seções
        sections = self._split_into_sections(title, content)
        
        # Processar cada seção em chunks
        all_chunks = []
        for section_title, section_content in sections:
            section_chunks = self._chunk_section(section_title, section_content)
            all_chunks.extend(section_chunks)
            
        # Enriquecer chunks com metadados
        enriched_chunks = self._enrich_chunks(all_chunks, doc_id, title, metadata)
        
        return enriched_chunks
    
    def _split_into_sections(
        self, 
        title: str, 
        content: str
    ) -> List[Tuple[str, str]]:
        """
        Divide o conteúdo em seções baseadas em cabeçalhos.
        
        Args:
            title: Título do documento
            content: Conteúdo textual do documento
            
        Returns:
            Lista de tuplas (título_seção, conteúdo_seção)
        """
        # Padrões para identificar cabeçalhos
        section_patterns = [
            r"^#{1,6}\s+(.+)$",              # Cabeçalhos Markdown (# Título)
            r"^(.+)\n[=\-]{2,}$",            # Cabeçalhos alternativos Markdown (Título\n===)
            r"<h[1-6][^>]*>(.+?)</h[1-6]>",  # Cabeçalhos HTML
        ]
        
        # Combinar padrões em uma expressão regular
        combined_pattern = "|".join(f"({pattern})" for pattern in section_patterns)
        
        # Dividir o conteúdo em linhas
        lines = content.split("\n")
        
        # Inicializar seções
        sections = []
        current_section_title = title
        current_section_content = []
        
        # Processar cada linha
        for line in lines:
            # Verificar se a linha é um cabeçalho
            is_header = False
            header_title = None
            
            for pattern in section_patterns:
                match = re.match(pattern, line)
                if match:
                    is_header = True
                    header_title = match.group(1)
                    break
            
            if is_header and header_title:
                # Finalizar seção atual
                if current_section_content:
                    section_content = "\n".join(current_section_content)
                    sections.append((current_section_title, section_content))
                
                # Iniciar nova seção
                current_section_title = header_title
                current_section_content = []
            else:
                # Adicionar linha à seção atual
                current_section_content.append(line)
        
        # Adicionar última seção
        if current_section_content:
            section_content = "\n".join(current_section_content)
            sections.append((current_section_title, section_content))
        
        # Se não houver seções, usar o documento inteiro como uma seção
        if not sections:
            sections = [(title, content)]
            
        return sections
    
    def _chunk_section(
        self, 
        section_title: str, 
        section_content: str
    ) -> List[Dict[str, str]]:
        """
        Divide uma seção em chunks respeitando o limite de tokens.
        
        Args:
            section_title: Título da seção
            section_content: Conteúdo da seção
            
        Returns:
            Lista de chunks da seção
        """
        # Tokenizar o conteúdo
        tokens = self.tokenizer.encode(section_content)
        
        # Se a seção for pequena o suficiente, mantê-la inteira
        if len(tokens) <= self.max_tokens:
            return [{"title": section_title, "content": section_content}]
        
        # Dividir em parágrafos
        paragraphs = self._split_into_paragraphs(section_content)
        
        # Agrupar parágrafos em chunks respeitando o limite de tokens
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for para in paragraphs:
            para_tokens = self.tokenizer.encode(para)
            
            # Se adicionar este parágrafo exceder o limite
            if current_tokens + len(para_tokens) > self.max_tokens and current_chunk:
                # Finalizar o chunk atual
                chunk_content = "\n\n".join(current_chunk)
                chunks.append({"title": section_title, "content": chunk_content})
                
                # Iniciar novo chunk com sobreposição
                overlap_start = max(0, len(current_chunk) - 1)
                current_chunk = current_chunk[overlap_start:]
                current_tokens = sum(len(self.tokenizer.encode(p)) for p in current_chunk)
            
            # Adicionar parágrafo ao chunk atual
            current_chunk.append(para)
            current_tokens += len(para_tokens)
        
        # Adicionar o último chunk se não estiver vazio
        if current_chunk:
            chunk_content = "\n\n".join(current_chunk)
            chunks.append({"title": section_title, "content": chunk_content})
            
        return chunks
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """
        Divide o texto em parágrafos.
        
        Args:
            text: Texto a ser dividido
            
        Returns:
            Lista de parágrafos
        """
        # Dividir por quebras de linha duplas ou outros separadores de parágrafo
        paragraphs = re.split(r"\n\s*\n", text)
        
        # Filtrar parágrafos vazios
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _enrich_chunks(
        self, 
        chunks: List[Dict[str, str]], 
        doc_id: str,
        doc_title: str,
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Adiciona metadados e IDs aos chunks.
        
        Args:
            chunks: Lista de chunks básicos
            doc_id: ID do documento original
            doc_title: Título do documento original
            metadata: Metadados adicionais do documento
            
        Returns:
            Lista de chunks enriquecidos com metadados
        """
        enriched_chunks = []
        
        for i, chunk in enumerate(chunks):
            # Gerar ID único para o chunk
            chunk_id = f"{doc_id}_chunk_{i}"
            
            # Criar metadados do chunk
            chunk_metadata = {
                "chunk_id": chunk_id,
                "document_id": doc_id,
                "document_title": doc_title,
                "section_title": chunk["title"],
                "position": i / len(chunks),  # Posição relativa no documento
                "total_chunks": len(chunks)
            }
            
            # Adicionar metadados do documento
            if metadata:
                for key, value in metadata.items():
                    if key not in chunk_metadata:
                        chunk_metadata[key] = value
            
            # Criar chunk enriquecido
            enriched_chunk = {
                "id": chunk_id,
                "text": chunk["content"],
                "metadata": chunk_metadata
            }
            
            enriched_chunks.append(enriched_chunk)
            
        return enriched_chunks


class MarkdownChunker(SemanticChunker):
    """
    Versão especializada do chunker semântico otimizada para documentos Markdown.
    """
    
    def _split_into_sections(
        self, 
        title: str, 
        content: str
    ) -> List[Tuple[str, str]]:
        """
        Divide o conteúdo Markdown em seções baseadas em cabeçalhos.
        
        Args:
            title: Título do documento
            content: Conteúdo Markdown do documento
            
        Returns:
            Lista de tuplas (título_seção, conteúdo_seção)
        """
        # Padrão para cabeçalhos Markdown
        header_pattern = r"^(#{1,6})\s+(.+)$"
        
        # Dividir o conteúdo em linhas
        lines = content.split("\n")
        
        # Inicializar seções
        sections = []
        current_level = 0
        current_title = title
        current_content = []
        
        # Processar cada linha
        for line in lines:
            # Verificar se a linha é um cabeçalho
            match = re.match(header_pattern, line)
            
            if match:
                # Nível do cabeçalho (# = 1, ## = 2, etc.)
                level = len(match.group(1))
                header_title = match.group(2)
                
                # Finalizar seção atual se não estiver vazia
                if current_content and (level <= current_level or current_level == 0):
                    section_content = "\n".join(current_content)
                    sections.append((current_title, section_content))
                    current_content = []
                
                # Atualizar título e nível da seção atual
                current_title = header_title
                current_level = level
            else:
                # Adicionar linha à seção atual
                current_content.append(line)
        
        # Adicionar última seção
        if current_content:
            section_content = "\n".join(current_content)
            sections.append((current_title, section_content))
        
        # Se não houver seções, usar o documento inteiro como uma seção
        if not sections:
            sections = [(title, content)]
            
        return sections


class PDFChunker(SemanticChunker):
    """
    Versão especializada do chunker semântico otimizada para conteúdo extraído de PDFs.
    """
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """
        Divide o texto extraído de PDF em parágrafos, lidando com quebras de linha.
        
        Args:
            text: Texto extraído de PDF
            
        Returns:
            Lista de parágrafos
        """
        # Normalizar quebras de linha
        normalized = re.sub(r"\r\n", "\n", text)
        
        # Identificar quebras de parágrafo (linha em branco ou indentação)
        paragraphs = []
        current_para = []
        
        lines = normalized.split("\n")
        for i, line in enumerate(lines):
            # Verificar se é uma quebra de parágrafo
            is_break = (
                not line.strip() or  # Linha vazia
                (i > 0 and line.startswith("    ") and not lines[i-1].endswith(".")) or  # Indentação
                (i > 0 and re.match(r"^\d+\.\s", line))  # Item numerado
            )
            
            if is_break and current_para:
                # Finalizar parágrafo atual
                paragraphs.append(" ".join(current_para))
                current_para = []
                
                # Adicionar linha atual se não for vazia
                if line.strip():
                    current_para.append(line.strip())
            else:
                # Adicionar ao parágrafo atual
                if line.strip():
                    # Verificar se deve juntar com a linha anterior
                    if current_para and not current_para[-1].endswith("."):
                        current_para[-1] = current_para[-1] + " " + line.strip()
                    else:
                        current_para.append(line.strip())
        
        # Adicionar último parágrafo
        if current_para:
            paragraphs.append(" ".join(current_para))
        
        return paragraphs
