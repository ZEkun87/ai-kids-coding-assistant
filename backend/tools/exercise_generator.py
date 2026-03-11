#这是优化后的通义千问API
import os
import logging
from typing import Optional, Union
from dataclasses import dataclass
from functools import lru_cache

# 替换 OpenAI 为通义千问 SDK
import dashscope
from dashscope import Generation
from dashscope.api_entities.dashscope_response import GenerationResponse
from dashscope.exception import (
    ApiKeyNotFoundError,
    ApiKeyExpiredError,
    RateLimitExceededError,
    ServiceUnavailableError,
    BadRequestError
)
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

# ====================== 全局配置（通义千问专属） ======================
# 日志配置（生产级）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("exercise_generator.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

# 配置类（解耦环境变量）
@dataclass(frozen=True)
class AppConfig:
    dashscope_api_key: str = os.getenv("DASHSCOPE_API_KEY", "")
    qwen_model: str = os.getenv("QWEN_MODEL", "qwen-turbo")  # 通义千问模型（轻量版性价比高）
    max_retry_attempts: int = int(os.getenv("MAX_RETRY_ATTEMPTS", 3))
    timeout: int = int(os.getenv("DASHSCOPE_TIMEOUT", 30))
    max_tokens: int = int(os.getenv("MAX_TOKENS", 1500))
    max_topic_length: int = 50  # 主题最大长度限制

# 单例加载配置
@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    config = AppConfig()
    # 校验关键配置
    if not config.dashscope_api_key:
        raise ValueError("未配置 DASHSCOPE_API_KEY 环境变量！")
    # 初始化通义千问 API Key
    dashscope.api_key = config.dashscope_api_key
    return config

# ====================== 重试装饰器（通义千问异常适配） ======================
def retry_on_qwen_error():
    """通义千问 API 重试装饰器：处理限流/服务不可用/网络错误"""
    config = get_config()
    return retry(
        stop=stop_after_attempt(config.max_retry_attempts),
        wait=wait_exponential(multiplier=1, min=2, max=10),  # 2s→4s→8s 重试
        retry=retry_if_exception_type(
            (RateLimitExceededError, ServiceUnavailableError)
        ),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True  # 最终失败时抛出异常
    )

# ====================== 参数校验 ======================
def validate_topic(topic: Union[str, bytes]) -> str:
    """校验练习题主题有效性"""
    config = get_config()
    if not topic:
        raise ValueError("编程练习题主题不能为空")
    if isinstance(topic, bytes):
        topic = topic.decode("utf-8")
    if not isinstance(topic, str):
        raise TypeError(f"主题必须是字符串类型，当前类型: {type(topic)}")
    
    topic = topic.strip()
    if len(topic) > config.max_topic_length:
        raise ValueError(f"主题长度不能超过 {config.max_topic_length} 个字符（当前: {len(topic)}）")
    
    logger.info(f"主题校验通过: {topic}")
    return topic

# ====================== 提示词优化（适配通义千问的中文理解） ======================
def get_exercise_prompt(topic: str) -> str:
    """生成标准化的小学生编程练习题提示词（适配通义千问）"""
    prompt_template = """
    你是专业的小学编程启蒙老师，擅长用简单易懂的方式设计编程练习题。请严格按照以下要求生成一道编程练习题：
    
    练习题主题：{topic}
    
    输出格式（必须严格遵守，分3个部分，使用中文标题）：
    1. 题目：简洁明了的编程练习题描述，符合小学3-6年级学生的认知水平，仅使用Python基础语法
    2. 示例代码：可运行的Python代码框架（留出需要填空的位置，添加清晰注释）
    3. 答案：完整的正确代码 + 50字以内的简单解释（用小学生能听懂的语言）
    
    额外要求：
    - 题目难度适中，仅涉及变量、简单运算、循环、条件判断等基础语法
    - 代码注释使用中文，避免专业术语
    - 解释部分重点说明代码的核心逻辑，而非语法细节
    """
    return prompt_template.format(topic=topic)

# ====================== 核心生成函数（适配通义千问 API） ======================
@retry_on_qwen_error()
def generate_exercise(topic: str, custom_prompt: Optional[str] = None) -> str:
    """
    调用通义千问 API 生成小学生编程练习题（企业级实现）
    
    Args:
        topic: 练习题主题（如"加法运算"、"打印小星星"）
        custom_prompt: 自定义提示词（可选，覆盖默认模板）
    
    Returns:
        str: 标准化的编程练习题（题目+示例代码+答案）
    
    Raises:
        ValueError: 主题参数无效
        ApiKeyNotFoundError/ApiKeyExpiredError: API Key 错误/过期
        RateLimitExceededError: API 调用限流
        ServiceUnavailableError: 通义千问服务不可用
    """
    # 1. 参数校验
    topic = validate_topic(topic)
    config = get_config()

    # 2. 获取提示词
    prompt = custom_prompt or get_exercise_prompt(topic)

    # 3. 调用通义千问 API（适配 DashScope 格式）
    logger.info(f"开始调用通义千问 API 生成练习题，模型: {config.qwen_model}")
    try:
        response: GenerationResponse = Generation.call(
            model=config.qwen_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,  # 降低随机性，保证输出稳定
            max_tokens=config.max_tokens,
            timeout=config.timeout
        )

        # 4. 解析通义千问响应
        if response.status_code != 200:
            error_msg = f"通义千问 API 错误 {response.code}: {response.message}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        if not response.output or not response.output.choices:
            error_msg = "通义千问返回空响应"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        exercise_content = response.output.choices[0].message.content.strip()
        logger.info(f"练习题生成成功，内容长度: {len(exercise_content)}")
        return exercise_content

    # 精准捕获通义千问专属异常
    except ApiKeyNotFoundError:
        logger.error("DASHSCOPE_API_KEY 未配置或无效", exc_info=True)
        raise
    except ApiKeyExpiredError:
        logger.error("DASHSCOPE_API_KEY 已过期", exc_info=True)
        raise
    except BadRequestError as e:
        logger.error(f"请求参数错误: {str(e)}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"生成练习题失败: {str(e)}", exc_info=True)
        raise

# ====================== 示例调用 ======================
def main():
    """生产级调用示例"""
    # 加载环境变量（推荐使用 python-dotenv）
    try:
        from dotenv import load_dotenv
        load_dotenv()  # 自动加载 .env 文件中的配置
    except ImportError:
        logger.warning("未安装 python-dotenv，建议安装：pip install python-dotenv")

    # 测试生成练习题
    test_topic = "打印九九乘法表"
    try:
        exercise = generate_exercise(test_topic)
        print("=== 小学生编程练习题 ===")
        print(exercise)
    except Exception as e:
        logger.error(f"程序执行失败: {str(e)}", exc_info=True)
        exit(1)

if __name__ == "__main__":
    main()