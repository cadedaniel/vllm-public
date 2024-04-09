import pytest

from tests.conftest import cleanup
from vllm import LLM
from vllm.model_executor.utils import set_random_seed


@pytest.fixture
def baseline_llm_generator(request, common_llm_kwargs,
                           per_test_common_llm_kwargs, baseline_llm_kwargs,
                           seed):
    return create_llm_generator("baseline", request, common_llm_kwargs,
                                per_test_common_llm_kwargs,
                                baseline_llm_kwargs, seed)


@pytest.fixture
def test_llm_generator(request, common_llm_kwargs, per_test_common_llm_kwargs,
                       test_llm_kwargs, seed):
    return create_llm_generator("test", request, common_llm_kwargs,
                                per_test_common_llm_kwargs, test_llm_kwargs,
                                seed)


def create_llm_generator(baseline_or_test, request, common_llm_kwargs,
                         per_test_common_llm_kwargs, distinct_llm_kwargs,
                         seed):
    kwargs = {
        **common_llm_kwargs,
        **per_test_common_llm_kwargs,
        **distinct_llm_kwargs,
    }
    test_name = request.node.name

    def generator_inner():
        print(f'Creating {baseline_or_test=} LLM for {test_name=}. {kwargs=}')
        llm = LLM(**kwargs)

        set_random_seed(seed)

        yield llm
        del llm
        cleanup()

    def generator_outer():
        for llm in generator_inner():
            yield llm
            del llm

    return generator_outer
