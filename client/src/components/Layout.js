import React from 'react';
import { Box, Flex, VStack, Heading, Text, Image, useColorModeValue } from '@chakra-ui/react';
import Sidebar from './Sidebar';
import Header from './Header';

const Layout = ({ children }) => {
  const bgColor = useColorModeValue('background.secondary', 'gray.800');
  const contentBgColor = useColorModeValue('background.primary', 'gray.700');

  return (
    <Flex h="100vh" direction="column">
      <Header />
      <Flex flex="1" overflow="hidden">
        <Sidebar />
        <Box
          as="main"
          flex="1"
          bg={bgColor}
          p={4}
          overflowY="auto"
        >
          <Box
            bg={contentBgColor}
            borderRadius="lg"
            boxShadow="sm"
            p={6}
            h="full"
          >
            {children}
          </Box>
        </Box>
      </Flex>
    </Flex>
  );
};

export default Layout;
