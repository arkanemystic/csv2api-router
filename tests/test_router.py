import unittest
import asyncio
from src.pipeline.router import APIRouter

class TestAPIRouter(unittest.TestCase):
    
    def setUp(self):
        self.router = APIRouter(api_key="test_key")
    
    async def async_test_execute_api_call(self):
        async with self.router as router:
            # Test transaction API call
            tx_call = {
                'method': 'get_transaction',
                'params': {'tx_hash': '0x123'},
                'chain': 'ETHEREUM'
            }
            result = await router.execute_api_call(tx_call)
            self.assertIsInstance(result, dict)
            self.assertTrue(result['success'])
            self.assertEqual(result['method'], 'get_transaction')
    
    def test_execute_api_call(self):
        # Run async test in event loop
        asyncio.run(self.async_test_execute_api_call())
    
    def test_invalid_method(self):
        # Test invalid API method
        async def test_invalid():
            async with self.router as router:
                invalid_call = {
                    'method': 'invalid_method',
                    'params': {},
                    'chain': 'ETHEREUM'
                }
                with self.assertRaises(ValueError):
                    await router.execute_api_call(invalid_call)
        
        asyncio.run(test_invalid())
    
    def test_supported_methods(self):
        # Test all supported methods are properly configured
        expected_methods = {
            'get_transaction',
            'get_receipt',
            'get_balance',
            'get_transfers',
            'get_abi',
            'get_events'
        }
        
        async def test_methods():
            async with self.router as router:
                # Test that all expected methods exist in router's supported_methods
                self.assertEqual(set(router.supported_methods.keys()), expected_methods)
                
                # Test that each method's handler is properly defined
                for method in expected_methods:
                    self.assertTrue(callable(router.supported_methods[method]))
        
        asyncio.run(test_methods())

if __name__ == '__main__':
    unittest.main()