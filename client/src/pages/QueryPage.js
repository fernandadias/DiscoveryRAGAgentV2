import React, { useState, useEffect } from 'react';
import {
  Box,
  VStack,
  HStack,
  Heading,
  Text,
  Textarea,
  Button,
  Select,
  Divider,
  useToast,
  Spinner,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Flex,
  Badge,
  Card,
  CardBody,
  CardHeader,
  useColorModeValue
} from '@chakra-ui/react';
import { FiSend, FiRefreshCw } from 'react-icons/fi';
import ReactMarkdown from 'react-markdown';
import { queryService } from '../services/api';

const QueryPage = () => {
  const [query, setQuery] = useState('');
  const [objective, setObjective] = useState('informative');
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);
  
  const toast = useToast();
  const cardBg = useColorModeValue('white', 'gray.700');
  const responseBg = useColorModeValue('gray.50', 'gray.800');
  
  const handleSubmit = async () => {
    if (!query.trim()) {
      toast({
        title: 'Consulta vazia',
        description: 'Por favor, insira uma consulta para continuar.',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      });
      return;
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      // Chamada real à API
      const result = await queryService.sendQuery(query, objective);
      setResponse(result);
      
      // Iniciar simulação de fluxo em background
      try {
        await queryService.startFlowSimulation(query, objective);
      } catch (flowError) {
        console.error('Erro ao iniciar simulação de fluxo:', flowError);
        // Não bloquear o fluxo principal se a simulação falhar
      }
    } catch (err) {
      setError('Ocorreu um erro ao processar sua consulta. Por favor, tente novamente.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleReset = () => {
    setQuery('');
    setResponse(null);
    setError(null);
  };
  
  return (
    <VStack spacing={6} align="stretch">
      <Heading as="h1" size="xl">Consulta ao Agente</Heading>
      
      <Card bg={cardBg} variant="outline">
        <CardHeader>
          <Heading size="md">Nova Consulta</Heading>
        </CardHeader>
        <CardBody>
          <VStack spacing={4} align="stretch">
            <Box>
              <Text mb={2} fontWeight="medium">Objetivo da Consulta</Text>
              <Select 
                value={objective} 
                onChange={(e) => setObjective(e.target.value)}
              >
                <option value="informative">Informativo (O que sabemos?)</option>
                <option value="hypothesis">Avaliação de Hipótese</option>
                <option value="benchmark">Benchmark e Boas Práticas</option>
                <option value="objectives">Alinhamento com Objetivos</option>
              </Select>
            </Box>
            
            <Box>
              <Text mb={2} fontWeight="medium">Sua Consulta</Text>
              <Textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Digite sua consulta ou hipótese aqui..."
                size="lg"
                rows={5}
                resize="vertical"
              />
            </Box>
            
            <HStack justify="flex-end" spacing={4}>
              <Button 
                leftIcon={<FiRefreshCw />} 
                variant="outline" 
                onClick={handleReset}
                isDisabled={isLoading || (!query && !response)}
              >
                Limpar
              </Button>
              <Button 
                leftIcon={<FiSend />} 
                colorScheme="brand" 
                onClick={handleSubmit}
                isLoading={isLoading}
                loadingText="Processando..."
                isDisabled={!query.trim()}
              >
                Enviar
              </Button>
            </HStack>
          </VStack>
        </CardBody>
      </Card>
      
      {isLoading && (
        <Flex justify="center" py={10}>
          <VStack>
            <Spinner size="xl" color="brand.500" thickness="4px" />
            <Text mt={4} color="text.secondary">Processando sua consulta...</Text>
          </VStack>
        </Flex>
      )}
      
      {error && (
        <Alert status="error" borderRadius="md">
          <AlertIcon />
          <AlertTitle mr={2}>Erro!</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      
      {response && !isLoading && (
        <Card bg={cardBg} variant="outline">
          <CardHeader>
            <Flex justify="space-between" align="center">
              <Heading size="md">Resposta</Heading>
              <HStack spacing={2}>
                <Badge colorScheme="green">
                  {response.metadata.processingTime}
                </Badge>
                <Badge colorScheme="blue">
                  {response.metadata.tokensUsed} tokens
                </Badge>
                <Badge colorScheme="purple">
                  {response.metadata.objective}
                </Badge>
              </HStack>
            </Flex>
          </CardHeader>
          <Divider />
          <CardBody>
            <Box 
              bg={responseBg} 
              p={6} 
              borderRadius="md"
              className="markdown-content"
            >
              <ReactMarkdown>
                {response.response}
              </ReactMarkdown>
            </Box>
          </CardBody>
        </Card>
      )}
    </VStack>
  );
};

export default QueryPage;
