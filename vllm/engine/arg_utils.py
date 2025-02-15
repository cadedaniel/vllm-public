import argparse
import dataclasses
import json
from dataclasses import dataclass
from typing import Optional, Tuple

from vllm.config import (CacheConfig, ModelConfig, ParallelConfig,
                         SchedulerConfig, LoadConfig, SpeculativeConfig,
                         LoRAConfig)


@dataclass
class EngineArgs:
    """Arguments for vLLM engine."""
    model: str
    tokenizer: Optional[str] = None
    tokenizer_mode: str = 'auto'
    trust_remote_code: bool = False
    download_dir: Optional[str] = None
    load_format: str = 'auto'
    dtype: str = 'auto'
    seed: int = 0
    max_model_len: Optional[int] = None
    worker_use_ray: bool = False
    pipeline_parallel_size: int = 1
    tensor_parallel_size: int = 1
    block_size: int = 16
    swap_space: int = 4  # GiB
    gpu_memory_utilization: float = 0.90
    max_num_batched_tokens: Optional[int] = None
    max_num_seqs: int = 256
    disable_log_stats: bool = False
    revision: Optional[str] = None
    tokenizer_revision: Optional[str] = None
    quantization: Optional[str] = None
    load_s3_path: str = None
    load_s3_region: str = 'us-west-2'
    enable_cuda_graph: bool = False
    cuda_graph_max_context_len: int = 5000
    cuda_graph_cache_size: int = 10
    disable_shared_memory: bool = False
    num_tokenizer_actors: int = 0
    speculative_model: Optional[str] = None
    speculative_model_uses_tp_1: bool = False
    num_speculative_tokens: Optional[int] = None
    target_model_input_padding_size: Optional[int] = None
    draft_model_input_padding_size: Optional[int] = None
    enable_lora: bool = False
    max_loras: int = 1
    max_lora_rank: int = 16
    lora_extra_vocab_size: int = 256
    lora_dtype = 'auto'
    max_cpu_loras: int = -1
    flash_style: bool = False
    max_chunked_prefill_len: int = -1
    max_num_prompt_seqs: int = 256
    input_padding_size: int = 8
    ray_workers_use_nsight: bool = False

    def __post_init__(self):
        if self.tokenizer is None:
            self.tokenizer = self.model

    @staticmethod
    def add_cli_args(
            parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
        """Shared CLI arguments for vLLM engine."""

        # NOTE: If you update any of the arguments below, please also
        # make sure to update docs/source/models/engine_args.rst

        # Model arguments
        parser.add_argument(
            '--model',
            type=str,
            default='facebook/opt-125m',
            help='name or path of the huggingface model to use')
        parser.add_argument(
            '--tokenizer',
            type=str,
            default=EngineArgs.tokenizer,
            help='name or path of the huggingface tokenizer to use')
        parser.add_argument(
            '--revision',
            type=str,
            default=None,
            help='the specific model version to use. It can be a branch '
            'name, a tag name, or a commit id. If unspecified, will use '
            'the default version.')
        parser.add_argument(
            '--tokenizer-revision',
            type=str,
            default=None,
            help='the specific tokenizer version to use. It can be a branch '
            'name, a tag name, or a commit id. If unspecified, will use '
            'the default version.')
        parser.add_argument('--tokenizer-mode',
                            type=str,
                            default=EngineArgs.tokenizer_mode,
                            choices=['auto', 'slow'],
                            help='tokenizer mode. "auto" will use the fast '
                            'tokenizer if available, and "slow" will '
                            'always use the slow tokenizer.')
        parser.add_argument('--trust-remote-code',
                            action='store_true',
                            help='trust remote code from huggingface')
        parser.add_argument('--download-dir',
                            type=str,
                            default=EngineArgs.download_dir,
                            help='directory to download and load the weights, '
                            'default to the default cache dir of '
                            'huggingface')

        # LoRA related configs
        parser.add_argument('--enable-lora',
                            action='store_true',
                            help='enable lora adapters')
        parser.add_argument('--max-loras',
                            type=int,
                            default=EngineArgs.max_loras,
                            help='max number of LoRAs in a single batch')
        parser.add_argument('--max-lora-rank',
                            type=int,
                            default=EngineArgs.max_lora_rank,
                            help='max LoRA rank')
        parser.add_argument('--lora-extra-vocab-size',
                            type=int,
                            default=EngineArgs.lora_extra_vocab_size,
                            help='LoRA extra vocab size')
        parser.add_argument('--lora-dtype',
                            type=str,
                            default=EngineArgs.lora_dtype,
                            choices=['auto', 'float16', 'bfloat16', 'float32'],
                            help='data type for lora')
        parser.add_argument(
            '--max-cpu-loras',
            type=int,
            default=EngineArgs.max_cpu_loras,
            help=('Maximum number of loras to store in CPU memory. '
                  'Must be >= than max_num_seqs. '
                  'Defaults to max_num_seqs.'))
        # Cuda Graph related configs
        parser.add_argument('--enable-cuda-graph',
                            action='store_true',
                            help='enable cuda graph for decoding')
        parser.add_argument('--cuda-graph-max-context-len',
                            type=int,
                            default=5000,
                            help='max context length for cuda graph decoding.'
                            'request with longer context will fallback to'
                            'non-compiled decoding')
        parser.add_argument('--cuda-graph-cache-size',
                            type=int,
                            default=10,
                            help='num of cached cuda graphs for decoding')
        parser.add_argument(
            '--disable-shared-memory',
            action='store_true',
            help='don\'t use shared memory for engine<->worker comms')
        parser.add_argument(
            '--num-tokenizer-actors',
            type=int,
            default=0,
            help='num of Ray actors for tokenization (0 is no Ray)')
        parser.add_argument(
            '--load-format',
            type=str,
            default=EngineArgs.load_format,
            choices=['auto', 'pt', 'safetensors', 'npcache', 'dummy'],
            help='The format of the model weights to load. '
            '"auto" will try to load the weights in the safetensors format '
            'and fall back to the pytorch bin format if safetensors format '
            'is not available. '
            '"pt" will load the weights in the pytorch bin format. '
            '"safetensors" will load the weights in the safetensors format. '
            '"npcache" will load the weights in pytorch format and store '
            'a numpy cache to speed up the loading. '
            '"dummy" will initialize the weights with random values, '
            'which is mainly for profiling.')
        parser.add_argument(
            '--dtype',
            type=str,
            default=EngineArgs.dtype,
            choices=[
                'auto', 'half', 'float16', 'bfloat16', 'float', 'float32'
            ],
            help='data type for model weights and activations. '
            'The "auto" option will use FP16 precision '
            'for FP32 and FP16 models, and BF16 precision '
            'for BF16 models.')
        parser.add_argument('--max-model-len',
                            type=int,
                            default=None,
                            help='model context length. If unspecified, '
                            'will be automatically derived from the model.')
        # Parallel arguments
        parser.add_argument('--worker-use-ray',
                            action='store_true',
                            help='use Ray for distributed serving, will be '
                            'automatically set when using more than 1 GPU')
        parser.add_argument('--pipeline-parallel-size',
                            '-pp',
                            type=int,
                            default=EngineArgs.pipeline_parallel_size,
                            help='number of pipeline stages')
        parser.add_argument('--tensor-parallel-size',
                            '-tp',
                            type=int,
                            default=EngineArgs.tensor_parallel_size,
                            help='number of tensor parallel replicas')
        # KV cache arguments
        parser.add_argument('--block-size',
                            type=int,
                            default=EngineArgs.block_size,
                            choices=[8, 16, 32, 64, 128, 256, 512, 1024],
                            help='token block size')
        # TODO(woosuk): Support fine-grained seeds (e.g., seed per request).
        parser.add_argument('--seed',
                            type=int,
                            default=EngineArgs.seed,
                            help='random seed')
        parser.add_argument('--swap-space',
                            type=int,
                            default=EngineArgs.swap_space,
                            help='CPU swap space size (GiB) per GPU')
        parser.add_argument('--gpu-memory-utilization',
                            type=float,
                            default=EngineArgs.gpu_memory_utilization,
                            help='the percentage of GPU memory to be used for'
                            'the model executor')
        parser.add_argument('--max-num-batched-tokens',
                            type=int,
                            default=EngineArgs.max_num_batched_tokens,
                            help='maximum number of batched tokens per '
                            'iteration')
        parser.add_argument('--max-num-seqs',
                            type=int,
                            default=EngineArgs.max_num_seqs,
                            help='maximum number of sequences per iteration')
        parser.add_argument('--disable-log-stats',
                            action='store_true',
                            help='disable logging statistics')
        # Quantization settings.
        parser.add_argument('--quantization',
                            '-q',
                            type=str,
                            choices=['awq', 'squeezellm', None],
                            default=None,
                            help='Method used to quantize the weights')
        parser.add_argument('--load-s3-path',
                            type=str,
                            default=None,
                            help='Fast loading s3 path')
        parser.add_argument('--load-s3-region',
                            type=str,
                            default='us-west-2',
                            help='Fast loading s3 region')
        parser.add_argument('--rope-scaling',
                            default=None,
                            type=json.loads,
                            help='RoPE scaling configuration')
        parser.add_argument(
            '--speculative-model',
            type=str,
            default=None,
            help='name of the draft model to be used in speculative decoding.')

        parser.add_argument(
            '--speculative-model-uses-tp-1',
            action='store_true',
            help='whether the speculative model should use the same tensor '
            'parallel degree as the verifier model, or use tp=1')

        parser.add_argument('--num-speculative-tokens',
                            type=int,
                            default=None,
                            help='number of speculative tokens to sample from '
                            'the draft model in speculative decoding')

        parser.add_argument('--target-model-input-padding-size',
                            type=int,
                            default=None,
                            help='padding size for speculative decoding target'
                            ' model prompt/generation tokens.'
                            ' must be a multiple of 8')

        parser.add_argument('--draft-model-input-padding-size',
                            type=int,
                            default=None,
                            help='padding size for speculative decoding draft'
                            ' model prompt/generation tokens.'
                            ' must be a multiple of 8')

        parser.add_argument('--flash-style',
                            action='store_true',
                            help='use flash attention')
        parser.add_argument(
            '--max-chunked-prefill-len',
            type=int,
            default=-1,
            help='max number of prefill tokens allowed in chunked prefill'
            ', -1 means no limit')
        parser.add_argument(
            '--max-num-prompt-seqs',
            type=int,
            default=1024,
            help='max number of prompt sequences allowed in prefill')
        parser.add_argument('--input-padding-size',
                            type=int,
                            default=8,
                            help='padding size for prompt/generation tokens.'
                            ' must be a multiple of 8')
        parser.add_argument('--ray-workers-use-nsight',
                            type=bool,
                            default=False,
                            help='use nsight to profile ray workers')
        return parser

    @classmethod
    def from_cli_args(cls, args: argparse.Namespace) -> 'EngineArgs':
        # Get the list of attributes of this dataclass.
        attrs = [attr.name for attr in dataclasses.fields(cls)]
        # Set the attributes from the parsed arguments.
        engine_args = cls(**{attr: getattr(args, attr) for attr in attrs})
        return engine_args

    def create_engine_configs(
        self,
    ) -> Tuple[ModelConfig, CacheConfig, ParallelConfig, SchedulerConfig,
               LoadConfig, SpeculativeConfig, Optional[LoRAConfig]]:
        # Initialize the configs.
        model_config = ModelConfig(
            self.model, self.tokenizer, self.tokenizer_mode,
            self.trust_remote_code, self.download_dir, self.load_format,
            self.dtype, self.seed, self.revision, self.tokenizer_revision,
            self.max_model_len, self.quantization, self.enable_cuda_graph,
            self.cuda_graph_max_context_len, self.cuda_graph_cache_size,
            self.flash_style, self.max_chunked_prefill_len)

        cache_config = CacheConfig(
            self.block_size, self.gpu_memory_utilization, self.swap_space,
            getattr(model_config.hf_config, 'sliding_window', None),
            self.flash_style)
        parallel_config = ParallelConfig(
            self.pipeline_parallel_size,
            self.tensor_parallel_size,
            self.worker_use_ray,
            self.disable_shared_memory,
            self.num_tokenizer_actors,
            ray_workers_use_nsight=self.ray_workers_use_nsight,
        )

        speculative_config = SpeculativeConfig.maybe_create_spec_config(
            model_config,
            parallel_config,
            self.dtype,
            speculative_model=self.speculative_model,
            num_speculative_tokens=self.num_speculative_tokens,
            speculative_model_uses_tp_1=self.speculative_model_uses_tp_1,
            target_model_input_padding_size=self.
            target_model_input_padding_size,
            draft_model_input_padding_size=self.draft_model_input_padding_size,
        )

        scheduler_config = SchedulerConfig(
            self.max_num_batched_tokens,
            self.max_num_seqs,
            model_config.max_model_len,
            use_deltas=parallel_config.worker_use_ray
            and not speculative_config,
            num_preallocated_slots_per_step=0 if not speculative_config else
            speculative_config.num_preallocated_slots_per_step,
            max_chunked_prefill_len=self.max_chunked_prefill_len,
            max_num_prompt_seqs=self.max_num_prompt_seqs,
            flash_style=self.flash_style,
            input_padding_size=self.input_padding_size,
        )
        if self.load_s3_path is not None:
            if self.load_s3_path.startswith('s3://'):
                _, _, bucket, key = self.load_s3_path.split('/', 3)
            load_config = LoadConfig(bucket, key, self.load_s3_region)
        else:
            load_config = None

        lora_config = LoRAConfig(
            max_lora_rank=self.max_lora_rank,
            max_loras=self.max_loras,
            lora_extra_vocab_size=self.lora_extra_vocab_size,
            lora_dtype=self.lora_dtype,
            max_cpu_loras=self.max_cpu_loras
            if self.max_cpu_loras > 0 else None) if self.enable_lora else None

        return (model_config, cache_config, parallel_config, scheduler_config,
                load_config, speculative_config, lora_config)


@dataclass
class AsyncEngineArgs(EngineArgs):
    """Arguments for asynchronous vLLM engine."""
    engine_use_ray: bool = False
    disable_log_requests: bool = False
    max_log_len: Optional[int] = None

    @staticmethod
    def add_cli_args(
            parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
        parser = EngineArgs.add_cli_args(parser)
        parser.add_argument('--engine-use-ray',
                            action='store_true',
                            help='use Ray to start the LLM engine in a '
                            'separate process as the server process.')
        parser.add_argument('--disable-log-requests',
                            action='store_true',
                            help='disable logging requests')
        parser.add_argument('--max-log-len',
                            type=int,
                            default=None,
                            help='max number of prompt characters or prompt '
                            'ID numbers being printed in log. '
                            'Default: unlimited.')
        return parser
