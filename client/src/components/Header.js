import React from 'react';
import { Box, Flex, Heading, Spacer, Button, IconButton, useColorModeValue } from '@chakra-ui/react';
import { FiMenu, FiUser, FiHelpCircle } from 'react-icons/fi';

const Header = ({ onToggleSidebar }) => {
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  return (
    <Box 
      as="header" 
      bg={bgColor} 
      borderBottom="1px" 
      borderColor={borderColor} 
      py={3} 
      px={6}
      boxShadow="sm"
    >
      <Flex align="center">
        <IconButton
          icon={<FiMenu />}
          variant="ghost"
          onClick={onToggleSidebar}
          aria-label="Toggle Sidebar"
          display={{ base: 'flex', md: 'none' }}
          mr={3}
        />
        
        <Heading size="md" color="brand.500">Discovery RAG Agent</Heading>
        
        <Spacer />
        
        <Flex gap={2}>
          <IconButton
            icon={<FiHelpCircle />}
            variant="ghost"
            aria-label="Help"
          />
          <IconButton
            icon={<FiUser />}
            variant="ghost"
            aria-label="User Profile"
          />
        </Flex>
      </Flex>
    </Box>
  );
};

export default Header;
