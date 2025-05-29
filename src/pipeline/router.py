import asyncio
import logging
from typing import Dict, List, Union, Any, Optional
import aiohttp
from ..utils.logger import log_info, log_error, log_debug

class APIRouter:
    """Routes and executes blockchain API calls."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def execute_api_call(self, api_call: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single API call and return the result."""
        try:
            method = api_call.get('method')
            params = api_call.get('params', {})
            chain = api_call.get('chain', 'ETHEREUM')
            
            # Map method to actual API endpoint and handler
            handlers = {
                'get_transaction': self._handle_transaction,
                'get_receipt': self._handle_receipt,
                'get_balance': self._handle_balance,
                'get_transfers': self._handle_transfers,
                'get_abi': self._handle_abi,
                'get_events': self._handle_events
            }
            
            if method not in handlers:
                raise ValueError(f"Unsupported API method: {method}")
            
            handler = handlers[method]
            result = await handler(params, chain)
            
            log_info(f"Successfully executed {method} API call")
            log_debug(f"API call result: {result}")
            
            return {
                'success': True,
                'method': method,
                'chain': chain,
                'result': result
            }
            
        except Exception as e:
            error_msg = f"Error executing API call {api_call.get('method')}: {str(e)}"
            log_error(error_msg)
            return {
                'success': False,
                'method': api_call.get('method'),
                'error': error_msg
            }
    
    async def execute_batch(self, api_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute multiple API calls in batch mode."""
        async with self:
            tasks = [self.execute_api_call(call) for call in api_calls]
            return await asyncio.gather(*tasks)
    
    async def execute_interactive(self, api_call: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single API call in interactive mode with detailed logging."""
        async with self:
            log_info(f"Executing API call: {api_call.get('method')}")
            result = await self.execute_api_call(api_call)
            return result
    
    # API Handler Methods
    async def _handle_transaction(self, params: Dict[str, Any], chain: str) -> Dict[str, Any]:
        """Handle get_transaction API calls."""
        tx_hash = params.get('tx_hash')
        if not tx_hash:
            raise ValueError("Transaction hash is required")
            
        endpoint = self._get_chain_endpoint(chain)
        async with self.session.get(
            f"{endpoint}/api",
            params={'module': 'proxy', 'action': 'eth_getTransactionByHash', 'txhash': tx_hash, 'apikey': self.api_key}
        ) as response:
            return await response.json()
    
    async def _handle_receipt(self, params: Dict[str, Any], chain: str) -> Dict[str, Any]:
        """Handle get_receipt API calls."""
        tx_hash = params.get('tx_hash')
        if not tx_hash:
            raise ValueError("Transaction hash is required")
            
        endpoint = self._get_chain_endpoint(chain)
        async with self.session.get(
            f"{endpoint}/api",
            params={'module': 'proxy', 'action': 'eth_getTransactionReceipt', 'txhash': tx_hash, 'apikey': self.api_key}
        ) as response:
            return await response.json()
    
    async def _handle_balance(self, params: Dict[str, Any], chain: str) -> Dict[str, Any]:
        """Handle get_balance API calls."""
        address = params.get('address')
        token_address = params.get('token_address')
        if not address or not token_address:
            raise ValueError("Both address and token_address are required")
            
        endpoint = self._get_chain_endpoint(chain)
        async with self.session.get(
            f"{endpoint}/api",
            params={
                'module': 'account', 
                'action': 'tokenbalance',
                'contractaddress': token_address,
                'address': address,
                'apikey': self.api_key
            }
        ) as response:
            return await response.json()
    
    async def _handle_transfers(self, params: Dict[str, Any], chain: str) -> Dict[str, Any]:
        """Handle get_transfers API calls."""
        address = params.get('address')
        if not address:
            raise ValueError("Address is required")
            
        endpoint = self._get_chain_endpoint(chain)
        async with self.session.get(
            f"{endpoint}/api",
            params={
                'module': 'account',
                'action': 'tokentx',
                'address': address,
                'apikey': self.api_key
            }
        ) as response:
            return await response.json()
    
    async def _handle_abi(self, params: Dict[str, Any], chain: str) -> Dict[str, Any]:
        """Handle get_abi API calls."""
        contract_address = params.get('contract_address')
        if not contract_address:
            raise ValueError("Contract address is required")
            
        endpoint = self._get_chain_endpoint(chain)
        async with self.session.get(
            f"{endpoint}/api",
            params={
                'module': 'contract',
                'action': 'getabi',
                'address': contract_address,
                'apikey': self.api_key
            }
        ) as response:
            return await response.json()
    
    async def _handle_events(self, params: Dict[str, Any], chain: str) -> Dict[str, Any]:
        """Handle get_events API calls."""
        contract_address = params.get('contract_address')
        event_name = params.get('event_name')
        if not contract_address or not event_name:
            raise ValueError("Contract address and event name are required")
            
        endpoint = self._get_chain_endpoint(chain)
        async with self.session.get(
            f"{endpoint}/api",
            params={
                'module': 'logs',
                'action': 'getLogs',
                'address': contract_address,
                'topic0': self._get_event_topic(event_name),
                'apikey': self.api_key
            }
        ) as response:
            return await response.json()
    
    def _get_chain_endpoint(self, chain: str) -> str:
        """Get the API endpoint for a given chain."""
        endpoints = {
            'ETHEREUM': 'https://api.etherscan.io',
            'POLYGON': 'https://api.polygonscan.com',
            'BSC': 'https://api.bscscan.com'
        }
        return endpoints.get(chain.upper(), endpoints['ETHEREUM'])
    
    def _get_event_topic(self, event_name: str) -> str:
        """Get the topic hash for a given event name."""
        # In a real implementation, this would use web3.py to calculate the event topic
        # For now, we'll just return a placeholder
        return "0x0000000000000000000000000000000000000000000000000000000000000000"

async def route_api_calls(api_calls: Union[Dict[str, Any], List[Dict[str, Any]]], 
                         api_key: Optional[str] = None,
                         batch_mode: bool = True) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Route and execute API calls either in batch or interactive mode.
    
    Args:
        api_calls: Single API call dict or list of API calls
        api_key: Optional API key for blockchain explorers
        batch_mode: Whether to execute calls in batch mode
        
    Returns:
        API call results
    """
    router = APIRouter(api_key=api_key)
    
    if isinstance(api_calls, dict):
        api_calls = [api_calls]
        batch_mode = False
    
    if batch_mode:
        results = await router.execute_batch(api_calls)
    else:
        results = await router.execute_interactive(api_calls[0])
    
    return results

if __name__ == "__main__":
    async def test():
        # Test API calls
        test_calls = [
            {
                "method": "get_transaction",
                "params": {"tx_hash": "0x123..."},
                "chain": "ETHEREUM"
            },
            {
                "method": "get_balance",
                "params": {
                    "address": "0x456...",
                    "token_address": "0x789..."
                },
                "chain": "POLYGON"
            }
        ]
        
        results = await route_api_calls(test_calls, api_key="YOUR_API_KEY")
        print(results)
    
    asyncio.run(test())