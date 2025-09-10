"""
Absorption API for Codessian Adaptive Orchestrator
==================================================

Automatically discovers, tests, and integrates external AI capabilities.
This is the "metabolization" system that allows the orchestrator to absorb
competitive advantages from other AI systems and tools.
"""

import asyncio
import aiohttp
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import importlib
import tempfile
import subprocess
from urllib.parse import urlparse
import yaml

class CapabilityType(Enum):
    LLM_API = "llm_api"
    TOOL_API = "tool_api"
    MODEL_HUB = "model_hub"
    PLUGIN = "plugin"
    MICROSERVICE = "microservice"
    KNOWLEDGE_BASE = "knowledge_base"

class IntegrationStatus(Enum):
    DISCOVERED = "discovered"
    TESTING = "testing"
    TRIAL_PERIOD = "trial_period"
    INTEGRATED = "integrated"
    REJECTED = "rejected"
    DEPRECATED = "deprecated"

@dataclass
class CapabilitySpec:
    """Specification of an external capability"""
    id: str
    name: str
    type: CapabilityType
    endpoint: Optional[str] = None
    api_key_required: bool = False
    task_types: List[str] = None
    
    # Performance characteristics
    expected_latency_ms: Optional[int] = None
    cost_per_request: Optional[float] = None
    rate_limits: Optional[Dict[str, Any]] = None
    
    # Capability metadata
    description: str = ""
    version: str = "unknown"
    provider: str = "unknown"
    documentation_url: str = ""
    
    # Integration details
    integration_method: str = "api"  # api, sdk, embedding, microservice
    auth_method: str = "api_key"  # api_key, oauth, none
    input_format: str = "json"
    output_format: str = "json"
    
    # Discovery metadata
    discovered_at: datetime = None
    last_tested: datetime = None
    status: IntegrationStatus = IntegrationStatus.DISCOVERED
    
    def __post_init__(self):
        if self.task_types is None:
            self.task_types = []
        if self.discovered_at is None:
            self.discovered_at = datetime.utcnow()

@dataclass
class CapabilityTest:
    """Results from testing a capability"""
    capability_id: str
    test_timestamp: datetime
    success: bool
    
    # Performance metrics
    latency_ms: float
    accuracy_score: Optional[float] = None
    cost_actual: Optional[float] = None
    
    # Test details
    test_tasks: List[Dict[str, Any]] = None
    outputs: List[Any] = None
    errors: List[str] = None
    
    # Comparative results
    baseline_comparison: Optional[Dict[str, float]] = None
    
    def __post_init__(self):
        if self.test_tasks is None:
            self.test_tasks = []
        if self.outputs is None:
            self.outputs = []
        if self.errors is None:
            self.errors = []

class CapabilityDiscoverer:
    """Discovers external capabilities from various sources"""
    
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        self.logger = logging.getLogger(__name__)
        
        # Discovery sources
        self.discovery_sources = {
            'model_hubs': [
                'https://huggingface.co/api/models',
                'https://replicate.com/api/v1/models',
            ],
            'api_directories': [
                'https://api.apis.guru/v2/list.json',
            ],
            'ai_tool_registries': [
                # Custom registries for AI tools
            ]
        }
    
    async def discover_from_model_hubs(self) -> List[CapabilitySpec]:
        """Discover models from popular model hubs"""
        capabilities = []
        
        # Hugging Face discovery
        try:
            hf_models = await self._discover_huggingface_models()
            capabilities.extend(hf_models)
        except Exception as e:
            self.logger.warning(f"Failed to discover HuggingFace models: {e}")
        
        # Replicate discovery
        try:
            replicate_models = await self._discover_replicate_models()
            capabilities.extend(replicate_models)
        except Exception as e:
            self.logger.warning(f"Failed to discover Replicate models: {e}")
        
        return capabilities
    
    async def _discover_huggingface_models(self) -> List[CapabilitySpec]:
        """Discover promising models from HuggingFace"""
        capabilities = []
        
        # Search for high-quality models in key categories
        search_queries = [
            'text-generation',
            'question-answering', 
            'text-classification',
            'summarization',
            'code-generation'
        ]
        
        for query in search_queries:
            try:
                url = f"https://huggingface.co/api/models?pipeline_tag={query}&sort=downloads&limit=10"
                
                async with self.session.get(url) as response:
                    if response.status == 200:
                        models = await response.json()
                        
                        for model in models:
                            if model.get('downloads', 0) > 1000:  # Popularity filter
                                capability = CapabilitySpec(
                                    id=f"hf_{model['id'].replace('/', '_')}",
                                    name=model['id'],
                                    type=CapabilityType.MODEL_HUB,
                                    endpoint=f"https://api-inference.huggingface.co/models/{model['id']}",
                                    api_key_required=True,
                                    task_types=[query],
                                    description=model.get('description', ''),
                                    provider='huggingface',
                                    integration_method='api',
                                    auth_method='api_key'
                                )
                                capabilities.append(capability)
                                
            except Exception as e:
                self.logger.warning(f"Failed to search HuggingFace for {query}: {e}")
        
        return capabilities
    
    async def _discover_replicate_models(self) -> List[CapabilitySpec]:
        """Discover models from Replicate"""
        capabilities = []
        
        try:
            url = "https://replicate.com/api/v1/collections/language-models"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    models = data.get('models', [])
                    
                    for model in models[:20]:  # Limit to top 20
                        capability = CapabilitySpec(
                            id=f"replicate_{model['name'].replace('/', '_')}",
                            name=model['name'],
                            type=CapabilityType.MODEL_HUB,
                            endpoint=f"https://api.replicate.com/v1/predictions",
                            api_key_required=True,
                            task_types=['text-generation'],
                            description=model.get('description', ''),
                            provider='replicate',
                            integration_method='api',
                            auth_method='api_key'
                        )
                        capabilities.append(capability)
                        
        except Exception as e:
            self.logger.warning(f"Failed to discover Replicate models: {e}")
        
        return capabilities
    
    async def discover_from_api_endpoints(self, endpoints: List[str]) -> List[CapabilitySpec]:
        """Discover capabilities from API endpoints"""
        capabilities = []
        
        for endpoint in endpoints:
            try:
                capability = await self._probe_api_endpoint(endpoint)
                if capability:
                    capabilities.append(capability)
            except Exception as e:
                self.logger.warning(f"Failed to probe endpoint {endpoint}: {e}")
        
        return capabilities
    
    async def _probe_api_endpoint(self, endpoint: str) -> Optional[CapabilitySpec]:
        """Probe an API endpoint to understand its capabilities"""
        try:
            # Try to get OpenAPI/Swagger spec
            spec_urls = [
                f"{endpoint}/openapi.json",
                f"{endpoint}/swagger.json", 
                f"{endpoint}/docs/openapi.json",
                f"{endpoint}/.well-known/openapi"
            ]
            
            for spec_url in spec_urls:
                try:
                    async with self.session.get(spec_url, timeout=10) as response:
                        if response.status == 200:
                            spec = await response.json()
                            return self._parse_openapi_spec(endpoint, spec)
                except:
                    continue
            
            # Fallback: basic HTTP probe
            return await self._basic_http_probe(endpoint)
            
        except Exception as e:
            self.logger.warning(f"Failed to probe {endpoint}: {e}")
            return None
    
    async def _basic_http_probe(self, endpoint: str) -> Optional[CapabilitySpec]:
        """Basic HTTP probe when OpenAPI spec is not available"""
        try:
            async with self.session.get(endpoint, timeout=5) as response:
                if response.status in [200, 404, 405]:  # Server is responsive
                    parsed_url = urlparse(endpoint)
                    
                    return CapabilitySpec(
                        id=f"api_{hashlib.md5(endpoint.encode()).hexdigest()[:8]}",
                        name=f"API at {parsed_url.netloc}",
                        type=CapabilityType.TOOL_API,
                        endpoint=endpoint,
                        task_types=['unknown'],
                        provider=parsed_url.netloc,
                        integration_method='api'
                    )
        except:
            pass
        
        return None
    
    def _parse_openapi_spec(self, endpoint: str, spec: Dict[str, Any]) -> CapabilitySpec:
        """Parse OpenAPI specification to understand API capabilities"""
        info = spec.get('info', {})
        paths = spec.get('paths', {})
        
        # Infer task types from API paths and operations
        task_types = []
        for path, methods in paths.items():
            for method, operation in methods.items():
                if isinstance(operation, dict):
                    summary = operation.get('summary', '').lower()
                    description = operation.get('description', '').lower()
                    
                    # Infer capabilities from API descriptions
                    if any(keyword in summary + description for keyword in 
                           ['generate', 'create', 'write']):
                        task_types.append('generation')
                    if any(keyword in summary + description for keyword in 
                           ['analyze', 'classify', 'detect']):
                        task_types.append('analysis')
                    if any(keyword in summary + description for keyword in 
                           ['search', 'find', 'query']):
                        task_types.append('retrieval')
        
        return CapabilitySpec(
            id=f"api_{hashlib.md5(endpoint.encode()).hexdigest()[:8]}",
            name=info.get('title', f"API at {urlparse(endpoint).netloc}"),
            type=CapabilityType.TOOL_API,
            endpoint=endpoint,
            task_types=list(set(task_types)) or ['unknown'],
            description=info.get('description', ''),
            version=info.get('version', 'unknown'),
            provider=urlparse(endpoint).netloc,
            documentation_url=spec.get('externalDocs', {}).get('url', ''),
            integration_method='api'
        )

class CapabilityTester:
    """Tests external capabilities to evaluate their performance"""
    
    def __init__(self, session: aiohttp.ClientSession, test_suite_provider):
        self.session = session
        self.test_suite_provider = test_suite_provider
        self.logger = logging.getLogger(__name__)
    
    async def test_capability(self, capability: CapabilitySpec, 
                            baseline_agent=None) -> CapabilityTest:
        """Run comprehensive tests on a capability"""
        test_start = datetime.utcnow()
        
        try:
            # Get appropriate test tasks for this capability type
            test_tasks = await self.test_suite_provider.get_test_tasks(
                capability.task_types
            )
            
            # Execute tests
            results = []
            errors = []
            total_latency = 0
            
            for task in test_tasks:
                try:
                    start_time = datetime.utcnow()
                    result = await self._execute_test_task(capability, task)
                    latency = (datetime.utcnow() - start_time).total_seconds() * 1000
                    
                    results.append(result)
                    total_latency += latency
                    
                except Exception as e:
                    errors.append(f"Task failed: {str(e)}")
            
            # Calculate performance metrics
            avg_latency = total_latency / len(test_tasks) if test_tasks else 0
            accuracy_score = await self._calculate_accuracy(test_tasks, results)
            
            # Compare with baseline if provided
            baseline_comparison = None
            if baseline_agent:
                baseline_comparison = await self._compare_with_baseline(
                    test_tasks, results, baseline_agent
                )
            
            return CapabilityTest(
                capability_id=capability.id,
                test_timestamp=test_start,
                success=len(errors) == 0,
                latency_ms=avg_latency,
                accuracy_score=accuracy_score,
                test_tasks=test_tasks,
                outputs=results,
                errors=errors,
                baseline_comparison=baseline_comparison
            )
            
        except Exception as e:
            return CapabilityTest(
                capability_id=capability.id,
                test_timestamp=test_start,
                success=False,
                latency_ms=0,
                errors=[str(e)]
            )
    
    async def _execute_test_task(self, capability: CapabilitySpec, 
                               task: Dict[str, Any]) -> Any:
        """Execute a single test task against the capability"""
        if capability.type == CapabilityType.LLM_API:
            return await self._test_llm_api(capability, task)
        elif capability.type == CapabilityType.MODEL_HUB:
            return await self._test_model_hub(capability, task)
        elif capability.type == CapabilityType.TOOL_API:
            return await self._test_tool_api(capability, task)
        else:
            raise ValueError(f"Unsupported capability type: {capability.type}")
    
    async def _test_llm_api(self, capability: CapabilitySpec, 
                          task: Dict[str, Any]) -> Any:
        """Test an LLM API capability"""
        prompt = task.get('prompt', '')
        
        # Format request based on common API patterns
        if 'openai' in capability.provider.lower():
            payload = {
                'model': capability.name.split('/')[-1],
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': task.get('max_tokens', 100)
            }
            headers = {'Authorization': f'Bearer {self._get_api_key(capability)}'}
        
        elif 'huggingface' in capability.provider.lower():
            payload = {'inputs': prompt}
            headers = {'Authorization': f'Bearer {self._get_api_key(capability)}'}
        
        elif 'anthropic' in capability.provider.lower():
            payload = {
                'model': capability.name,
                'max_tokens': task.get('max_tokens', 100),
                'messages': [{'role': 'user', 'content': prompt}]
            }
            headers = {'x-api-key': self._get_api_key(capability)}
        
        else:
            # Generic format
            payload = {'input': prompt, 'max_length': task.get('max_tokens', 100)}
            headers = {'Authorization': f'Bearer {self._get_api_key(capability)}'}
        
        headers['Content-Type'] = 'application/json'
        
        async with self.session.post(
            capability.endpoint,
            json=payload,
            headers=headers,
            timeout=30
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"API returned status {response.status}: {await response.text()}")
    
    async def _test_model_hub(self, capability: CapabilitySpec, 
                            task: Dict[str, Any]) -> Any:
        """Test a model hub capability"""
        if 'huggingface' in capability.provider.lower():
            return await self._test_llm_api(capability, task)  # Same as LLM API
        
        elif 'replicate' in capability.provider.lower():
            payload = {
                'version': capability.name.split(':')[-1] if ':' in capability.name else 'latest',
                'input': {'prompt': task.get('prompt', '')}
            }
            
            headers = {
                'Authorization': f'Token {self._get_api_key(capability)}',
                'Content-Type': 'application/json'
            }
            
            async with self.session.post(
                capability.endpoint,
                json=payload,
                headers=headers,
                timeout=30
            ) as response:
                if response.status in [200, 201]:
                    return await response.json()
                else:
                    raise Exception(f"API returned status {response.status}")
        
        else:
            raise ValueError(f"Unsupported model hub: {capability.provider}")
    
    async def _test_tool_api(self, capability: CapabilitySpec, 
                           task: Dict[str, Any]) -> Any:
        """Test a tool API capability"""
        # Generic API testing - adapt based on task type
        payload = task.get('input_data', {})
        
        headers = {}
        if capability.api_key_required:
            headers['Authorization'] = f'Bearer {self._get_api_key(capability)}'
        
        headers['Content-Type'] = 'application/json'
        
        async with self.session.post(
            capability.endpoint,
            json=payload,
            headers=headers,
            timeout=30
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"API returned status {response.status}")
    
    def _get_api_key(self, capability: CapabilitySpec) -> str:
        """Get API key for the capability (implement secure key management)"""
        # This should integrate with your secure key management system
        # For now, return a placeholder
        return "your_api_key_here"
    
    async def _calculate_accuracy(self, test_tasks: List[Dict], 
                                results: List[Any]) -> float:
        """Calculate accuracy score based on test results"""
        if not test_tasks or not results:
            return 0.0
        
        correct = 0
        total = 0
        
        for task, result in zip(test_tasks, results):
            if 'expected_output' in task:
                # For tasks with expected outputs, check similarity
                expected = task['expected_output']
                actual = self._extract_text_from_result(result)
                
                # Simple similarity check (implement more sophisticated comparison)
                similarity = self._calculate_text_similarity(expected, actual)
                if similarity > 0.8:
                    correct += 1
                total += 1
        
        return correct / total if total > 0 else 0.0
    
    def _extract_text_from_result(self, result: Any) -> str:
        """Extract text from API result (handle different response formats)"""
        if isinstance(result, str):
            return result
        elif isinstance(result, dict):
            # Common response patterns
            if 'choices' in result and result['choices']:
                return result['choices'][0].get('message', {}).get('content', '')
            elif 'generated_text' in result:
                return result['generated_text']
            elif 'output' in result:
                return str(result['output'])
            elif 'text' in result:
                return result['text']
        
        return str(result)
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Simple text similarity calculation"""
        # Implement more sophisticated similarity (e.g., semantic similarity)
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    async def _compare_with_baseline(self, test_tasks: List[Dict], 
                                   results: List[Any], 
                                   baseline_agent) -> Dict[str, float]:
        """Compare capability performance with baseline agent"""
        baseline_results = []
        
        for task in test_tasks:
            try:
                baseline_result = await baseline_agent.execute(task)
                baseline_results.append(baseline_result)
            except Exception as e:
                self.logger.warning(f"Baseline failed on task: {e}")
                baseline_results.append(None)
        
        # Calculate comparative metrics
        new_accuracy = await self._calculate_accuracy(test_tasks, results)
        baseline_accuracy = await self._calculate_accuracy(test_tasks, baseline_results)
        
        return {
            'accuracy_improvement': new_accuracy - baseline_accuracy,
            'new_capability_accuracy': new_accuracy,
            'baseline_accuracy': baseline_accuracy
        }

class TestSuiteProvider:
    """Provides test tasks for different capability types"""
    
    def __init__(self):
        self.test_suites = {
            'generation': self._get_generation_tests(),
            'analysis': self._get_analysis_tests(),
            'retrieval': self._get_retrieval_tests(),
            'reasoning': self._get_reasoning_tests(),
            'code': self._get_code_tests(),
            'math': self._get_math_tests(),
            'unknown': self._get_generic_tests()
        }
    
    async def get_test_tasks(self, task_types: List[str]) -> List[Dict[str, Any]]:
        """Get appropriate test tasks for given capability types"""
        all_tests = []
        
        for task_type in task_types:
            tests = self.test_suites.get(task_type, self.test_suites['unknown'])
            all_tests.extend(tests[:3])  # Limit to 3 tests per type
        
        return all_tests[:10]  # Maximum 10 tests total
    
    def _get_generation_tests(self) -> List[Dict[str, Any]]:
        return [
            {
                'prompt': 'Write a creative story about a robot learning to paint.',
                'max_tokens': 200,
                'expected_quality_indicators': ['creativity', 'coherence', 'narrative_flow']
            },
            {
                'prompt': 'Explain quantum computing in simple terms.',
                'max_tokens': 150,
                'expected_quality_indicators': ['clarity', 'accuracy', 'simplicity']
            },
            {
                'prompt': 'Generate a professional email declining a meeting invitation.',
                'max_tokens': 100,
                'expected_quality_indicators': ['professionalism', 'politeness', 'clarity']
            }
        ]
    
    def _get_analysis_tests(self) -> List[Dict[str, Any]]:
        return [
            {
                'prompt': 'Analyze the sentiment of this text: "I absolutely love this new product! It exceeded all my expectations."',
                'expected_output': 'positive',
                'task_type': 'sentiment_analysis'
            },
            {
                'prompt': 'What is the main topic of this paragraph: "Climate change continues to impact global weather patterns, leading to more frequent extreme weather events."',
                'expected_output': 'climate change',
                'task_type': 'topic_classification'
            }
        ]
    
    def _get_reasoning_tests(self) -> List[Dict[str, Any]]:
        return [
            {
                'prompt': 'If all birds can fly and penguins are birds, can penguins fly? Explain your reasoning.',
                'expected_reasoning_type': 'logical',
                'task_type': 'logical_reasoning'
            },
            {
                'prompt': 'A train leaves Station A at 2 PM traveling at 60 mph. Another train leaves Station B at 3 PM traveling at 80 mph toward Station A. If the stations are 200 miles apart, when will the trains meet?',
                'task_type': 'word_problem'
            }
        ]
    
    def _get_code_tests(self) -> List[Dict[str, Any]]:
        return [
            {
                'prompt': 'Write a Python function to calculate the factorial of a number.',
                'expected_elements': ['def', 'factorial', 'return'],
                'task_type': 'code_generation'
            },
            {
                'prompt': 'Debug this Python code: def add_numbers(a, b): return a + b + c',
                'expected_fix': 'remove +c or define c',
                'task_type': 'code_debugging'
            }
        ]
    
    def _get_math_tests(self) -> List[Dict[str, Any]]:
        return [
            {
                'prompt': 'Solve: 2x + 5 = 13',
                'expected_output': 'x = 4',
                'task_type': 'algebra'
            },
            {
                'prompt': 'What is the derivative of x^2 + 3x + 1?',
                'expected_output': '2x + 3',
                'task_type': 'calculus'
            }
        ]
    
    def _get_retrieval_tests(self) -> List[Dict[str, Any]]:
        return [
            {
                'prompt': 'Find information about the capital of France.',
                'expected_output': 'Paris',
                'task_type': 'factual_retrieval'
            }
        ]
    
    def _get_generic_tests(self) -> List[Dict[str, Any]]:
        return [
            {
                'prompt': 'Hello, how are you?',
                'expected_quality_indicators': ['responsiveness', 'coherence'],
                'task_type': 'general_interaction'
            }
        ]

class AbsorptionAPI:
    """
    Main Absorption API that orchestrates discovery, testing, and integration
    of external capabilities into the Codessian orchestrator.
    """
    
    def __init__(self, orchestrator, metrics_client, policy_engine):
        self.orchestrator = orchestrator
        self.metrics_client = metrics_client
        self.policy_engine = policy_engine
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.session = aiohttp.ClientSession()
        self.discoverer = CapabilityDiscoverer(self.session)
        self.test_suite_provider = TestSuiteProvider()
        self.tester = CapabilityTester(self.session, self.test_suite_provider)
        
        # State management
        self.discovered_capabilities: Dict[str, CapabilitySpec] = {}
        self.test_results: Dict[str, List[CapabilityTest]] = {}
        self.integrated_capabilities: Dict[str, CapabilitySpec] = {}
        
        # Configuration
        self.config = {
            'discovery_interval_hours': 24,
            'testing_interval_hours': 6,
            'integration_threshold': 0.8,  # Minimum performance improvement
            'trial_period_days': 7,
            'max_parallel_tests': 3
        }
    
    async def start_absorption_loop(self):
        """Start the main absorption loop"""
        self.logger.info("Starting Absorption API loop")
        
        # Schedule periodic tasks
        asyncio.create_task(self._discovery_loop())
        asyncio.create_task(self._testing_loop())
        asyncio.create_task(self._integration_loop())
        asyncio.create_task(self._maintenance_loop())
    
    async def _discovery_loop(self):
        """Continuously discover new capabilities"""
        while True:
            try:
                self.logger.info("Starting capability discovery")
                
                # Discover from model hubs
                hub_capabilities = await self.discoverer.discover_from_model_hubs()
                
                # Discover from known API endpoints (you can extend this)
                api_endpoints = []  # Add your target API endpoints here
                api_capabilities = await self.discoverer.discover_from_api_endpoints(api_endpoints)
                
                # Store discovered capabilities
                all_capabilities = hub_capabilities + api_capabilities
                for capability in all_capabilities:
                    if capability.id not in self.discovered_capabilities:
                        self.discovered_capabilities[capability.id] = capability
                        self.logger.info(f"Discovered new capability: {capability.name}")
                
                self.logger.info(f"Discovery complete. Total capabilities: {len(self.discovered_capabilities)}")
                
            except Exception as e:
                self.logger.error(f"Error in discovery loop: {e}")
            
            # Wait before next discovery
            await asyncio.sleep(self.config['discovery_interval_hours'] * 3600)
    
    async def _testing_loop(self):
        """Continuously test discovered capabilities"""
        while True:
            try:
                # Find capabilities that need testing
                capabilities_to_test = [
                    cap for cap in self.discovered_capabilities.values()
                    if (cap.status == IntegrationStatus.DISCOVERED or
                        (cap.last_tested and 
                         datetime.utcnow() - cap.last_tested > 
                         timedelta(hours=self.config['testing_interval_hours'])))
                ]
                
                if capabilities_to_test:
                    self.logger.info(f"Testing {len(capabilities_to_test)} capabilities")
                    
                    # Test capabilities in parallel (with limit)
                    semaphore = asyncio.Semaphore(self.config['max_parallel_tests'])
                    
                    async def test_with_semaphore(capability):
                        async with semaphore:
                            return await self._test_capability_safely(capability)
                    
                    test_tasks = [test_with_semaphore(cap) for cap in capabilities_to_test[:10]]
                    await asyncio.gather(*test_tasks, return_exceptions=True)
                
            except Exception as e:
                self.logger.error(f"Error in testing loop: {e}")
            
            await asyncio.sleep(self.config['testing_interval_hours'] * 3600)
    
    async def _test_capability_safely(self, capability: CapabilitySpec):
        """Test a capability with error handling"""
        try:
            self.logger.info(f"Testing capability: {capability.name}")
            
            # Get baseline agent for comparison
            baseline_agent = await self.orchestrator.get_agent_for_task_types(
                capability.task_types
            )
            
            # Run tests
            test_result = await self.tester.test_capability(capability, baseline_agent)
            
            # Store test results
            if capability.id not in self.test_results:
                self.test_results[capability.id] = []
            self.test_results[capability.id].append(test_result)
            
            # Update capability status based on test results
            capability.last_tested = datetime.utcnow()
            
            if test_result.success:
                if (test_result.baseline_comparison and 
                    test_result.baseline_comparison.get('accuracy_improvement', 0) > 
                    self.config['integration_threshold']):
                    capability.status = IntegrationStatus.TRIAL_PERIOD
                    self.logger.info(f"Capability {capability.name} moved to trial period")
                else:
                    capability.status = IntegrationStatus.TESTING
            else:
                capability.status = IntegrationStatus.REJECTED
                self.logger.warning(f"Capability {capability.name} rejected due to test failures")
            
        except Exception as e:
            self.logger.error(f"Error testing capability {capability.name}: {e}")
            capability.status = IntegrationStatus.REJECTED
    
    async def _integration_loop(self):
        """Handle integration of successful capabilities"""
        while True:
            try:
                # Find capabilities ready for integration
                trial_capabilities = [
                    cap for cap in self.discovered_capabilities.values()
                    if cap.status == IntegrationStatus.TRIAL_PERIOD
                ]
                
                for capability in trial_capabilities:
                    await self._evaluate_for_integration(capability)
                
            except Exception as e:
                self.logger.error(f"Error in integration loop: {e}")
            
            await asyncio.sleep(3600)  # Check every hour
    
    async def _evaluate_for_integration(self, capability: CapabilitySpec):
        """Evaluate if a capability should be integrated"""
        try:
            # Check if trial period is complete
            trial_start = capability.last_tested
            if not trial_start:
                return
            
            trial_duration = datetime.utcnow() - trial_start
            if trial_duration < timedelta(days=self.config['trial_period_days']):
                return  # Still in trial
            
            # Analyze performance during trial
            recent_tests = [
                test for test in self.test_results.get(capability.id, [])
                if test.test_timestamp > trial_start
            ]
            
            if not recent_tests:
                capability.status = IntegrationStatus.REJECTED
                return
            
            # Calculate average performance improvement
            avg_improvement = sum(
                test.baseline_comparison.get('accuracy_improvement', 0)
                for test in recent_tests
                if test.baseline_comparison
            ) / len(recent_tests)
            
            # Integration decision
            if avg_improvement >= self.config['integration_threshold']:
                await self._integrate_capability(capability)
            else:
                capability.status = IntegrationStatus.REJECTED
                self.logger.info(f"Capability {capability.name} rejected after trial")
                
        except Exception as e:
            self.logger.error(f"Error evaluating capability {capability.name}: {e}")
    
    async def _integrate_capability(self, capability: CapabilitySpec):
        """Integrate a capability into the orchestrator"""
        try:
            self.logger.info(f"Integrating capability: {capability.name}")
            
            # Create integration configuration
            integration_config = {
                'capability_id': capability.id,
                'name': capability.name,
                'type': capability.type.value,
                'endpoint': capability.endpoint,
                'task_types': capability.task_types,
                'auth_method': capability.auth_method,
                'integration_method': capability.integration_method,
                'performance_metrics': self._get_capability_performance_summary(capability.id)
            }
            
            # Integrate with orchestrator
            success = await self.orchestrator.integrate_external_capability(integration_config)
            
            if success:
                capability.status = IntegrationStatus.INTEGRATED
                self.integrated_capabilities[capability.id] = capability
                
                # Create policy to monitor integrated capability
                await self._create_monitoring_policy(capability)
                
                self.logger.info(f"Successfully integrated capability: {capability.name}")
            else:
                capability.status = IntegrationStatus.REJECTED
                self.logger.error(f"Failed to integrate capability: {capability.name}")
                
        except Exception as e:
            self.logger.error(f"Error integrating capability {capability.name}: {e}")
            capability.status = IntegrationStatus.REJECTED
    
    def _get_capability_performance_summary(self, capability_id: str) -> Dict[str, Any]:
        """Get performance summary for a capability"""
        tests = self.test_results.get(capability_id, [])
        if not tests:
            return {}
        
        successful_tests = [t for t in tests if t.success]
        
        return {
            'total_tests': len(tests),
            'successful_tests': len(successful_tests),
            'success_rate': len(successful_tests) / len(tests),
            'avg_latency_ms': sum(t.latency_ms for t in successful_tests) / len(successful_tests) if successful_tests else 0,
            'avg_accuracy': sum(t.accuracy_score or 0 for t in successful_tests) / len(successful_tests) if successful_tests else 0,
            'last_test_timestamp': max(t.test_timestamp for t in tests).isoformat()
        }
    
    async def _create_monitoring_policy(self, capability: CapabilitySpec):
        """Create a policy to monitor integrated capability performance"""
        monitoring_policy = {
            'name': f'monitor_{capability.id}',
            'trigger': 'performance_degradation',
            'conditions': [
                {
                    'metric': f'capabilities.{capability.id}.success_rate',
                    'operator': '<',
                    'threshold': 0.8,
                    'time_window': '2h'
                }
            ],
            'action': 'evaluate_capability_removal',
            'parameters': {
                'capability_id': capability.id
            },
            'priority': 6
        }
        
        # Add to policy engine (this would need to be implemented in your policy engine)
        await self.policy_engine.add_dynamic_policy(monitoring_policy)
    
    async def _maintenance_loop(self):
        """Periodic maintenance and cleanup"""
        while True:
            try:
                # Clean up old test results
                cutoff_date = datetime.utcnow() - timedelta(days=30)
                
                for capability_id in list(self.test_results.keys()):
                    self.test_results[capability_id] = [
                        test for test in self.test_results[capability_id]
                        if test.test_timestamp > cutoff_date
                    ]
                
                # Remove deprecated capabilities
                deprecated_capabilities = [
                    cap_id for cap_id, cap in self.discovered_capabilities.items()
                    if cap.status == IntegrationStatus.DEPRECATED
                ]
                
                for cap_id in deprecated_capabilities:
                    del self.discovered_capabilities[cap_id]
                    if cap_id in self.test_results:
                        del self.test_results[cap_id]
                
                self.logger.info(f"Maintenance complete. Cleaned up {len(deprecated_capabilities)} deprecated capabilities")
                
            except Exception as e:
                self.logger.error(f"Error in maintenance loop: {e}")
            
            await asyncio.sleep(24 * 3600)  # Daily maintenance
    
    async def manually_add_capability(self, capability_spec: Dict[str, Any]) -> str:
        """Manually add a capability for testing and potential integration"""
        capability = CapabilitySpec(
            id=capability_spec['id'],
            name=capability_spec['name'],
            type=CapabilityType(capability_spec['type']),
            endpoint=capability_spec.get('endpoint'),
            api_key_required=capability_spec.get('api_key_required', False),
            task_types=capability_spec.get('task_types', []),
            description=capability_spec.get('description', ''),
            provider=capability_spec.get('provider', 'manual'),
            integration_method=capability_spec.get('integration_method', 'api')
        )
        
        self.discovered_capabilities[capability.id] = capability
        self.logger.info(f"Manually added capability: {capability.name}")
        
        # Immediately queue for testing
        asyncio.create_task(self._test_capability_safely(capability))
        
        return capability.id
    
    async def get_absorption_status(self) -> Dict[str, Any]:
        """Get current status of the absorption system"""
        status_counts = {}
        for status in IntegrationStatus:
            status_counts[status.value] = sum(
                1 for cap in self.discovered_capabilities.values()
                if cap.status == status
            )
        
        return {
            'total_discovered': len(self.discovered_capabilities),
            'status_breakdown': status_counts,
            'integrated_count': len(self.integrated_capabilities),
            'recent_discoveries': [
                {
                    'id': cap.id,
                    'name': cap.name,
                    'provider': cap.provider,
                    'discovered_at': cap.discovered_at.isoformat(),
                    'status': cap.status.value
                }
                for cap in sorted(
                    self.discovered_capabilities.values(),
                    key=lambda x: x.discovered_at,
                    reverse=True
                )[:10]
            ],
            'top_performing_capabilities': await self._get_top_performing_capabilities(),
            'integration_pipeline': [
                {
                    'id': cap.id,
                    'name': cap.name,
                    'status': cap.status.value,
                    'performance_summary': self._get_capability_performance_summary(cap.id)
                }
                for cap in self.discovered_capabilities.values()
                if cap.status in [IntegrationStatus.TESTING, IntegrationStatus.TRIAL_PERIOD]
            ]
        }

    async def _get_top_performing_capabilities(self) -> List[Dict[str, Any]]:
        """Get top performing capabilities across all categories"""
        performance_scores = []

        for cap_id, capability in self.discovered_capabilities.items():
            if cap_id in self.test_results:
                tests = self.test_results[cap_id]
                successful_tests = [t for t in tests if t.success]

                if successful_tests:
                    avg_improvement = 0
                    if any(t.baseline_comparison for t in successful_tests):
                        improvements = [
                            t.baseline_comparison.get('accuracy_improvement', 0)
                            for t in successful_tests
                            if t.baseline_comparison
                        ]
                        avg_improvement = sum(improvements) / len(improvements) if improvements else 0

                    performance_scores.append({
                        'capability': capability,
                        'performance_score': avg_improvement,
                        'success_rate': len(successful_tests) / len(tests)
                    })

        # Sort by performance score
        top_performers = sorted(
            performance_scores,
            key=lambda x: x['performance_score'],
            reverse=True
        )[:5]

        return [
            {
                'id': p['capability'].id,
                'name': p['capability'].name,
                'provider': p['capability'].provider,
                'performance_score': p['performance_score'],
                'success_rate': p['success_rate'],
                'status': p['capability'].status.value
            }
            for p in top_performers
        ]

    async def force_integrate_capability(self, capability_id: str) -> bool:
        """Force integration of a capability (override normal flow)"""
        if capability_id not in self.discovered_capabilities:
            return False

        capability = self.discovered_capabilities[capability_id]

        try:
            await self._integrate_capability(capability)
            return capability.status == IntegrationStatus.INTEGRATED
        except Exception as e:
            self.logger.error(f"Failed to force integrate {capability_id}: {e}")
            return False

    async def remove_capability(self, capability_id: str) -> bool:
        """Remove an integrated capability"""
        if capability_id not in self.integrated_capabilities:
            return False

        try:
            # Remove from orchestrator
            success = await self.orchestrator.remove_external_capability(capability_id)

            if success:
                # Update status
                if capability_id in self.discovered_capabilities:
                    self.discovered_capabilities[capability_id].status = IntegrationStatus.DEPRECATED

                # Remove from integrated set
                del self.integrated_capabilities[capability_id]

                self.logger.info(f"Removed capability: {capability_id}")
                return True

        except Exception as e:
            self.logger.error(f"Error removing capability {capability_id}: {e}")

        return False

    async def close(self):
        """Clean shutdown of the absorption API"""
        await self.session.close()


# Example usage and integration
class MockOrchestrator:
    """Mock orchestrator for testing the Absorption API"""

    def __init__(self):
        self.agents = {}
        self.external_capabilities = {}

    async def get_agent_for_task_types(self, task_types: List[str]):
        """Get current agent handling these task types"""
        # Mock baseline agent
        class MockAgent:
            async def execute(self, task):
                # Simulate baseline performance
                return {"output": "baseline response", "confidence": 0.7}

        return MockAgent()

    async def integrate_external_capability(self, config: Dict[str, Any]) -> bool:
        """Integrate an external capability"""
        capability_id = config['capability_id']
        self.external_capabilities[capability_id] = config

        print(f"Integrated capability: {config['name']}")
        print(f"Task types: {config['task_types']}")
        print(f"Performance: {config.get('performance_metrics', {})}")

        return True

    async def remove_external_capability(self, capability_id: str) -> bool:
        """Remove an external capability"""
        if capability_id in self.external_capabilities:
            del self.external_capabilities[capability_id]
            return True
        return False


# Example configuration and startup
async def example_absorption_system():
    """Example of how to set up and run the Absorption API"""

    # Mock dependencies
    class MockMetricsClient:
        async def get_current_metrics(self):
            return {
                'accuracy': 0.85,
                'cost_per_request': 0.02,
                'avg_latency': 1200
            }

    class MockPolicyEngine:
        async def add_dynamic_policy(self, policy):
            print(f"Added monitoring policy: {policy['name']}")
            return True

    # Initialize system
    orchestrator = MockOrchestrator()
    metrics_client = MockMetricsClient()
    policy_engine = MockPolicyEngine()

    absorption_api = AbsorptionAPI(orchestrator, metrics_client, policy_engine)

    # Example: Manually add a capability for testing
    capability_config = {
        'id': 'test_openai_gpt4',
        'name': 'OpenAI GPT-4',
        'type': 'llm_api',
        'endpoint': 'https://api.openai.com/v1/chat/completions',
        'api_key_required': True,
        'task_types': ['generation', 'reasoning', 'analysis'],
        'description': 'OpenAI GPT-4 language model',
        'provider': 'openai',
        'integration_method': 'api'
    }

    capability_id = await absorption_api.manually_add_capability(capability_config)
    print(f"Added capability for testing: {capability_id}")

    # Get system status
    status = await absorption_api.get_absorption_status()
    print("Absorption System Status:")
    print(json.dumps(status, indent=2, default=str))

    # Start the absorption loop (in real usage, this runs continuously)
    # await absorption_api.start_absorption_loop()

    # Clean up
    await absorption_api.close()


if __name__ == "__main__":
    # Run the example
    asyncio.run(example_absorption_system())