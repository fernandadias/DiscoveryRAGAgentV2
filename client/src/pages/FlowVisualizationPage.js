import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  VStack,
  Heading,
  Text,
  Button,
  Flex,
  SimpleGrid,
  Card,
  CardBody,
  CardHeader,
  Badge,
  HStack,
  Divider,
  Progress,
  useColorModeValue,
  Icon,
  Alert,
  AlertIcon,
  Spinner
} from '@chakra-ui/react';
import { FiPlay, FiPause, FiRefreshCw, FiInfo, FiDatabase, FiCpu, FiSearch, FiMessageSquare } from 'react-icons/fi';
import { queryService } from '../services/api';

// Componente para um nó do fluxo
const FlowNode = ({ title, description, status, type, icon }) => {
  const getBgColor = () => {
    switch (status) {
      case 'active':
        return 'brand.500';
      case 'completed':
        return 'green.500';
      case 'waiting':
        return 'gray.300';
      default:
        return 'gray.300';
    }
  };

  const getTextColor = () => {
    return status === 'waiting' ? 'text.secondary' : 'white';
  };

  const getTypeColor = () => {
    switch (type) {
      case 'input':
        return 'blue';
      case 'process':
        return 'purple';
      case 'storage':
        return 'orange';
      case 'api':
        return 'teal';
      case 'output':
        return 'green';
      default:
        return 'gray';
    }
  };

  return (
    <Card 
      bg={getBgColor()} 
      color={getTextColor()}
      borderRadius="lg"
      boxShadow="md"
      transition="all 0.3s"
      _hover={{ transform: 'scale(1.02)', boxShadow: 'lg' }}
    >
      <CardHeader pb={2}>
        <Flex justify="space-between" align="center">
          <Heading size="sm">{title}</Heading>
          <Badge colorScheme={getTypeColor()}>{type}</Badge>
        </Flex>
      </CardHeader>
      <CardBody pt={0}>
        <Text fontSize="sm">{description}</Text>
        <Icon as={icon} mt={2} />
      </CardBody>
    </Card>
  );
};

// Componente para uma conexão entre nós
const FlowConnection = ({ status }) => {
  const getColor = () => {
    switch (status) {
      case 'active':
        return 'brand.500';
      case 'completed':
        return 'green.500';
      case 'waiting':
        return 'gray.300';
      default:
        return 'gray.300';
    }
  };

  return (
    <Flex justify="center" align="center" h="100%">
      <Box 
        w="80%" 
        h="4px" 
        bg={getColor()} 
        borderRadius="full"
      />
    </Flex>
  );
};

// Componente para métricas do processamento
const MetricsCard = ({ title, value, unit, icon }) => {
  const cardBg = useColorModeValue('white', 'gray.700');
  
  return (
    <Card bg={cardBg}>
      <CardBody>
        <Flex align="center">
          <Icon as={icon} boxSize={8} color="brand.500" mr={4} />
          <Box>
            <Text fontSize="sm" color="text.secondary">{title}</Text>
            <Flex align="baseline">
              <Heading size="md">{value}</Heading>
              {unit && <Text ml={1} color="text.secondary">{unit}</Text>}
            </Flex>
          </Box>
        </Flex>
      </CardBody>
    </Card>
  );
};

const FlowVisualizationPage = () => {
  const [isSimulating, setIsSimulating] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [simulationId, setSimulationId] = useState(null);
  const [flowStatus, setFlowStatus] = useState({
    status: 'idle',
    current_step: 0,
    nodes: {
      query: 'waiting',
      classification: 'waiting',
      retrieval: 'waiting',
      reranking: 'waiting',
      context: 'waiting',
      prompt: 'waiting',
      generation: 'waiting',
      response: 'waiting'
    },
    connections: {
      query_classification: 'waiting',
      classification_retrieval: 'waiting',
      retrieval_reranking: 'waiting',
      reranking_context: 'waiting',
      context_prompt: 'waiting',
      prompt_generation: 'waiting',
      generation_response: 'waiting'
    },
    metrics: {
      processingTime: 0,
      documentsRetrieved: 0,
      chunksProcessed: 0,
      tokensUsed: 0
    },
    current_node_details: null
  });

  const pollingInterval = useRef(null);
  const cardBg = useColorModeValue('white', 'gray.700');

  // Iniciar simulação
  const startSimulation = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Chamar API para iniciar simulação
      const result = await queryService.startFlowSimulation(
        "Quais os perfis de usuários já conhecemos hoje com base nos hábitos de uso deles?", 
        "informative"
      );
      
      setSimulationId(result.simulationId);
      setIsSimulating(true);
      
      // Iniciar polling para atualizar status
      startPolling(result.simulationId);
    } catch (err) {
      setError('Erro ao iniciar simulação. Por favor, tente novamente.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  // Parar simulação
  const stopSimulation = () => {
    if (pollingInterval.current) {
      clearInterval(pollingInterval.current);
      pollingInterval.current = null;
    }
    setIsSimulating(false);
  };

  // Iniciar polling para atualizar status
  const startPolling = (id) => {
    // Limpar intervalo existente se houver
    if (pollingInterval.current) {
      clearInterval(pollingInterval.current);
    }
    
    // Polling a cada 1 segundo
    pollingInterval.current = setInterval(async () => {
      try {
        const status = await queryService.getFlowStatus(id);
        setFlowStatus(status);
        
        // Se a simulação estiver completa, parar polling
        if (status.status === 'completed') {
          stopSimulation();
        }
      } catch (err) {
        console.error('Erro ao obter status da simulação:', err);
        // Não parar polling em caso de erro temporário
      }
    }, 1000);
  };

  // Resetar simulação
  const resetSimulation = () => {
    stopSimulation();
    setSimulationId(null);
    setFlowStatus({
      status: 'idle',
      current_step: 0,
      nodes: {
        query: 'waiting',
        classification: 'waiting',
        retrieval: 'waiting',
        reranking: 'waiting',
        context: 'waiting',
        prompt: 'waiting',
        generation: 'waiting',
        response: 'waiting'
      },
      connections: {
        query_classification: 'waiting',
        classification_retrieval: 'waiting',
        retrieval_reranking: 'waiting',
        reranking_context: 'waiting',
        context_prompt: 'waiting',
        prompt_generation: 'waiting',
        generation_response: 'waiting'
      },
      metrics: {
        processingTime: 0,
        documentsRetrieved: 0,
        chunksProcessed: 0,
        tokensUsed: 0
      },
      current_node_details: null
    });
  };

  // Limpar intervalo ao desmontar
  useEffect(() => {
    return () => {
      if (pollingInterval.current) {
        clearInterval(pollingInterval.current);
      }
    };
  }, []);

  // Mapear ícones para nós
  const nodeIcons = {
    query: FiMessageSquare,
    classification: FiInfo,
    retrieval: FiDatabase,
    reranking: FiSearch,
    context: FiCpu,
    prompt: FiMessageSquare,
    generation: FiCpu,
    response: FiMessageSquare
  };

  return (
    <VStack spacing={6} align="stretch">
      <Heading as="h1" size="xl">Visualização do Fluxo de Processamento</Heading>
      <Text>
        Esta visualização mostra o fluxo completo de processamento do agente RAG, desde a ingestão de documentos até a geração de respostas, em um formato semelhante ao n8n.
      </Text>
      
      <Flex justify="space-between" align="center">
        <Heading size="md">Fluxo de Processamento</Heading>
        <HStack>
          <Button
            leftIcon={isSimulating ? <FiPause /> : <FiPlay />}
            colorScheme="brand"
            onClick={isSimulating ? stopSimulation : startSimulation}
            isLoading={isLoading}
            loadingText="Iniciando..."
            isDisabled={isLoading}
          >
            {isSimulating ? 'Pausar Simulação' : 'Simular Processamento'}
          </Button>
          <Button
            leftIcon={<FiRefreshCw />}
            variant="outline"
            onClick={resetSimulation}
            isDisabled={isLoading}
          >
            Reiniciar
          </Button>
        </HStack>
      </Flex>
      
      {error && (
        <Alert status="error" borderRadius="md">
          <AlertIcon />
          <Text>{error}</Text>
        </Alert>
      )}
      
      {isLoading && (
        <Flex justify="center" py={10}>
          <VStack>
            <Spinner size="xl" color="brand.500" thickness="4px" />
            <Text mt={4} color="text.secondary">Iniciando simulação...</Text>
          </VStack>
        </Flex>
      )}
      
      {!isLoading && (
        <>
          {/* Métricas */}
          <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4}>
            <MetricsCard 
              title="Tempo de Processamento" 
              value={flowStatus.metrics.processingTime.toFixed(1)} 
              unit="s"
              icon={FiCpu}
            />
            <MetricsCard 
              title="Documentos Recuperados" 
              value={flowStatus.metrics.documentsRetrieved} 
              icon={FiDatabase}
            />
            <MetricsCard 
              title="Chunks Processados" 
              value={flowStatus.metrics.chunksProcessed} 
              icon={FiSearch}
            />
            <MetricsCard 
              title="Tokens Utilizados" 
              value={flowStatus.metrics.tokensUsed} 
              icon={FiMessageSquare}
            />
          </SimpleGrid>
          
          {/* Barra de progresso */}
          <Box>
            <Text mb={1}>Progresso: {Math.round((flowStatus.current_step / 16) * 100)}%</Text>
            <Progress 
              value={(flowStatus.current_step / 16) * 100} 
              colorScheme="brand" 
              borderRadius="full" 
              size="sm"
            />
          </Box>
          
          {/* Visualização do fluxo */}
          <Card bg={cardBg} variant="outline">
            <CardBody>
              <SimpleGrid columns={{ base: 1, md: 4 }} spacing={4} mb={4}>
                <FlowNode 
                  title="Consulta" 
                  description="Análise da consulta do usuário" 
                  status={flowStatus.nodes.query}
                  type="input"
                  icon={nodeIcons.query}
                />
                <FlowConnection status={flowStatus.connections.query_classification} />
                <FlowNode 
                  title="Classificação" 
                  description="Identificação do objetivo" 
                  status={flowStatus.nodes.classification}
                  type="process"
                  icon={nodeIcons.classification}
                />
                <FlowConnection status={flowStatus.connections.classification_retrieval} />
              </SimpleGrid>
              
              <SimpleGrid columns={{ base: 1, md: 4 }} spacing={4} mb={4}>
                <FlowNode 
                  title="Recuperação" 
                  description="Busca de chunks relevantes" 
                  status={flowStatus.nodes.retrieval}
                  type="storage"
                  icon={nodeIcons.retrieval}
                />
                <FlowConnection status={flowStatus.connections.retrieval_reranking} />
                <FlowNode 
                  title="Reranking" 
                  description="Reordenação por relevância" 
                  status={flowStatus.nodes.reranking}
                  type="process"
                  icon={nodeIcons.reranking}
                />
                <FlowConnection status={flowStatus.connections.reranking_context} />
              </SimpleGrid>
              
              <SimpleGrid columns={{ base: 1, md: 4 }} spacing={4} mb={4}>
                <FlowNode 
                  title="Contexto" 
                  description="Seleção dinâmica de contexto" 
                  status={flowStatus.nodes.context}
                  type="process"
                  icon={nodeIcons.context}
                />
                <FlowConnection status={flowStatus.connections.context_prompt} />
                <FlowNode 
                  title="Prompt" 
                  description="Construção de prompt especializado" 
                  status={flowStatus.nodes.prompt}
                  type="process"
                  icon={nodeIcons.prompt}
                />
                <FlowConnection status={flowStatus.connections.prompt_generation} />
              </SimpleGrid>
              
              <SimpleGrid columns={{ base: 1, md: 4 }} spacing={4}>
                <FlowNode 
                  title="Geração" 
                  description="Geração da resposta" 
                  status={flowStatus.nodes.generation}
                  type="api"
                  icon={nodeIcons.generation}
                />
                <FlowConnection status={flowStatus.connections.generation_response} />
                <FlowNode 
                  title="Resposta" 
                  description="Formatação e entrega" 
                  status={flowStatus.nodes.response}
                  type="output"
                  icon={nodeIcons.response}
                />
                <Box></Box> {/* Espaço vazio para manter o grid alinhado */}
              </SimpleGrid>
            </CardBody>
          </Card>
          
          {/* Detalhes do nó atual */}
          {flowStatus.current_node_details && (
            <Card bg={cardBg} variant="outline">
              <CardHeader>
                <Heading size="md">Detalhes do Processamento</Heading>
              </CardHeader>
              <Divider />
              <CardBody>
                <VStack align="start" spacing={3}>
                  <Flex align="center">
                    <Badge colorScheme="brand" mr={2}>Etapa Atual</Badge>
                    <Heading size="sm">{flowStatus.current_node_details.title}</Heading>
                  </Flex>
                  <Text>{flowStatus.current_node_details.description}</Text>
                  <Badge>{flowStatus.current_node_details.type}</Badge>
                </VStack>
              </CardBody>
            </Card>
          )}
        </>
      )}
    </VStack>
  );
};

export default FlowVisualizationPage;
